"""Reprex: concurrent range reads from data.source.coop are slower over HTTP/2 than HTTP/1.1.

    pip install obstore
    python source_coop_reprex.py [--rounds 5] [--requests 320] [--concurrency 64]

No credentials, no Icechunk. Uses obstore (Python bindings to Rust object_store) to fetch the same
1.66 MB byte ranges from public objects four ways, interleaved:

  S3 API   (S3Store, endpoint https://data.source.coop, path-style, unsigned)  x  HTTP/1.1 | HTTP/2
  plain GET (HTTPStore on https://data.source.coop/<account>/)                 x  HTTP/1.1 | HTTP/2

object_store uses HTTP/1.1 by default; `http2_only` switches the same client to HTTP/2. Prints the
Cloudflare edge (colo), the protocol it negotiated and the TCP connect time (a rough round-trip
time), from https://data.source.coop/cdn-cgi/trace. The client's IP address is not printed.
"""
import argparse
import asyncio
import datetime as dt
import statistics
import time
import urllib.request

import obstore
from obstore.store import HTTPStore, S3Store

ENDPOINT = "https://data.source.coop"
ACCOUNT = "ocean-icechunks"
KEYS = [f"pacioos/roms_hiig_reanalysis/netcdf/v2.0/2009/hiig_his_zlevel_200901{d:02d}.nc"
        for d in range(1, 9)]  # public, ~267 MB each
RANGE = 1_656_720


def edge():
    """colo and http version from Cloudflare's trace endpoint, plus a TCP connect time."""
    import socket
    with urllib.request.urlopen(f"{ENDPOINT}/cdn-cgi/trace", timeout=30) as r:
        kv = dict(line.split("=", 1) for line in r.read().decode().splitlines() if "=" in line)
    t = time.perf_counter()
    socket.create_connection(("data.source.coop", 443), timeout=10).close()
    return {"colo": kv.get("colo"), "loc": kv.get("loc"), "connect_ms": round((time.perf_counter() - t) * 1e3, 1)}


def make(kind, http2):
    opts = {"http2_only": True} if http2 else {}
    if kind == "s3":
        return S3Store(ACCOUNT, endpoint=ENDPOINT, region="us-east-1", skip_signature=True,
                       virtual_hosted_style_request=False, client_options=opts)
    return HTTPStore.from_url(f"{ENDPOINT}/{ACCOUNT}", client_options=opts)  # no trailing slash


async def read_all(store, reqs, conc):
    sem = asyncio.Semaphore(conc)

    async def one(k, a, b):
        async with sem:
            return len(await obstore.get_range_async(store, k, start=a, end=b))
    t = time.perf_counter()
    n = sum(await asyncio.gather(*(one(*q) for q in reqs)))
    return time.perf_counter() - t, n


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--rounds", type=int, default=5)
    p.add_argument("--requests", type=int, default=320)
    p.add_argument("--concurrency", type=int, default=64)
    a = p.parse_args()
    per = -(-a.requests // len(KEYS))
    reqs = [(k, i * RANGE, (i + 1) * RANGE) for k in KEYS for i in range(per)][: a.requests]
    total = len(reqs) * RANGE
    cases = {"S3 API    HTTP/1.1": ("s3", False), "S3 API    HTTP/2": ("s3", True),
             "plain GET HTTP/1.1": ("http", False), "plain GET HTTP/2": ("http", True)}
    print(f"{dt.datetime.now(dt.timezone.utc):%Y-%m-%d %H:%MZ}  obstore {obstore.__version__}  "
          f"edge {edge()}\n{len(reqs)} x {RANGE / 1e6:.2f} MB = {total / 1e6:.0f} MB per read, "
          f"{a.concurrency} in flight")
    times = {k: [] for k in cases}
    for r in range(a.rounds):
        for name, (kind, h2) in cases.items():  # interleave so a slow minute hits all cases
            wall, n = asyncio.run(read_all(make(kind, h2), reqs, a.concurrency))
            assert n == total, (name, n)
            times[name].append(wall)
            print(f"  round {r + 1} {name}  {wall:6.2f} s", flush=True)
    print(f"\n{'':20s} {'median s':>9s} {'best s':>8s} {'MB/s':>7s}")
    for name, v in times.items():
        print(f"{name:20s} {statistics.median(v):9.2f} {min(v):8.2f} {total / statistics.median(v) / 1e6:7.0f}")
    print(f"edge after run: {edge()}")


if __name__ == "__main__":
    main()
