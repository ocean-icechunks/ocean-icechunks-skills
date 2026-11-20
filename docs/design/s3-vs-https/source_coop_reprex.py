"""Reprex: throughput of concurrent range reads from data.source.coop, by client and protocol.

No Icechunk, no credentials. Fetches the same set of byte ranges from public Source Cooperative
objects with several ordinary clients, interleaved, for a few rounds, and prints wall time and
throughput for each. The ranges match what a Zarr/Icechunk reader issues for one variable of a
virtual dataset: 1.66 MB ranges, 64 in flight at once.

    pip install httpx[http2] obstore boto3
    python source_coop_reprex.py [--requests 160] [--concurrency 64] [--rounds 3] [--json out.json]

Clients:
  httpx-h1     httpx, HTTP/1.1, plain GET + Range on https://data.source.coop/<account>/<key>
  httpx-h2     httpx, HTTP/2, same URLs
  obstore-http obstore HTTPStore (Rust object_store / reqwest), same URLs
  obstore-s3   obstore S3Store, endpoint https://data.source.coop, path-style, unsigned (S3 GetObject)
  boto3-s3     boto3 S3 GetObject with Range, endpoint https://data.source.coop, unsigned
"""
import argparse
import asyncio
import datetime as dt
import json
import platform
import statistics
import time
from concurrent.futures import ThreadPoolExecutor

ENDPOINT = "https://data.source.coop"
BUCKET = "ocean-icechunks"  # Source Cooperative account; the S3 "bucket" at the proxy
KEYS = [f"pacioos/roms_hiig_reanalysis/netcdf/v2.0/2009/hiig_his_zlevel_200901{d:02d}.nc"
        for d in range(1, 9)]  # public, ~267 MB each
RANGE = 1_656_720               # bytes per request


def plan(n):
    """n (key, start, end) tuples spread over the files, end exclusive."""
    per = -(-n // len(KEYS))
    out = [(k, i * RANGE, (i + 1) * RANGE) for k in KEYS for i in range(per)]
    return out[:n]


async def run_httpx(reqs, conc, http2):
    import httpx
    limits = httpx.Limits(max_connections=conc, max_keepalive_connections=conc)
    timing, versions = [], set()
    async with httpx.AsyncClient(http2=http2, http1=not http2, limits=limits, timeout=120) as c:
        sem = asyncio.Semaphore(conc)

        async def one(k, a, b):
            async with sem:
                r = await c.get(f"{ENDPOINT}/{BUCKET}/{k}", headers={"Range": f"bytes={a}-{b - 1}"})
                r.raise_for_status()
                versions.add(r.http_version)
                timing.append(r.headers.get("server-timing", ""))
                return len(r.content)
        t = time.perf_counter()
        n = sum(await asyncio.gather(*(one(*q) for q in reqs)))
        return time.perf_counter() - t, n, {"protocol": sorted(versions), "server_timing": timing}


async def run_obstore(reqs, conc, kind):
    import obstore
    if kind == "http":
        from obstore.store import HTTPStore
        store, prefix = HTTPStore.from_url(f"{ENDPOINT}/{BUCKET}"), ""  # no trailing slash: it would double
    else:
        from obstore.store import S3Store
        store = S3Store(BUCKET, endpoint=ENDPOINT, region="us-east-1", skip_signature=True,
                        virtual_hosted_style_request=False)
        prefix = ""
    sem = asyncio.Semaphore(conc)

    async def one(k, a, b):
        async with sem:
            return len(await obstore.get_range_async(store, prefix + k, start=a, end=b))
    t = time.perf_counter()
    n = sum(await asyncio.gather(*(one(*q) for q in reqs)))
    return time.perf_counter() - t, n, {}


def run_boto3(reqs, conc):
    import boto3
    from botocore import UNSIGNED
    from botocore.config import Config
    s3 = boto3.client("s3", endpoint_url=ENDPOINT, region_name="us-east-1",
                      config=Config(signature_version=UNSIGNED, max_pool_connections=conc,
                                    s3={"addressing_style": "path"}))

    def one(q):
        k, a, b = q
        return len(s3.get_object(Bucket=BUCKET, Key=k, Range=f"bytes={a}-{b - 1}")["Body"].read())
    t = time.perf_counter()
    with ThreadPoolExecutor(conc) as ex:
        n = sum(ex.map(one, reqs))
    return time.perf_counter() - t, n, {}


CLIENTS = {
    "httpx-h1": lambda r, c: asyncio.run(run_httpx(r, c, http2=False)),
    "httpx-h2": lambda r, c: asyncio.run(run_httpx(r, c, http2=True)),
    "obstore-http": lambda r, c: asyncio.run(run_obstore(r, c, "http")),
    "obstore-s3": lambda r, c: asyncio.run(run_obstore(r, c, "s3")),
    "boto3-s3": run_boto3,
}


def colo():
    """Cloudflare data-centre code from cf-ray (e.g. PDX), to say which edge served the test."""
    import httpx
    r = httpx.head(f"{ENDPOINT}/{BUCKET}/{KEYS[0]}", timeout=30)
    return r.headers.get("cf-ray", "").rsplit("-", 1)[-1]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--requests", type=int, default=160)
    p.add_argument("--concurrency", type=int, default=64)
    p.add_argument("--rounds", type=int, default=3)
    p.add_argument("--clients", default=",".join(CLIENTS))
    p.add_argument("--json")
    a = p.parse_args()
    reqs = plan(a.requests)
    names = a.clients.split(",")
    res = {"utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
           "cloudflare_colo": colo(), "python": platform.python_version(),
           "requests": len(reqs), "bytes_per_request": RANGE, "concurrency": a.concurrency,
           "runs": {n: [] for n in names}, "extra": {}}
    print(f"{res['utc']}  edge {res['cloudflare_colo']}  {len(reqs)} x {RANGE/1e6:.2f} MB, "
          f"concurrency {a.concurrency}, {a.rounds} rounds")
    for r in range(a.rounds):
        for n in names:  # interleave clients so a slow minute hits all of them
            wall, nbytes, extra = CLIENTS[n](reqs, a.concurrency)
            assert nbytes == len(reqs) * RANGE, (n, nbytes)
            res["runs"][n].append(round(wall, 3))
            if extra and r == 0:
                st = [float(s.split("total;dur=")[1].split(",")[0]) for s in extra["server_timing"]
                      if "total;dur=" in s]
                res["extra"][n] = {"protocol": extra["protocol"],
                                   "server_timing_total_ms_median": statistics.median(st) if st else None}
            print(f"  round {r + 1} {n:13s} {wall:6.2f} s  {nbytes / wall / 1e6:7.1f} MB/s", flush=True)
    print("\nclient          median s   best s   median MB/s")
    for n, w in res["runs"].items():
        print(f"{n:15s} {statistics.median(w):8.2f} {min(w):8.2f} "
              f"{len(reqs) * RANGE / statistics.median(w) / 1e6:12.1f}")
    for n, e in res["extra"].items():
        print(f"{n}: protocol {e['protocol']}, proxy server-timing total median "
              f"{e['server_timing_total_ms_median']} ms")
    if a.json:
        with open(a.json, "w") as f:
            json.dump(res, f, indent=1)


if __name__ == "__main__":
    main()
