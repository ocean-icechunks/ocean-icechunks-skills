<!-- NOT FILED. Decision (Eli, 2026-11-20): this is an Icechunk issue (earth-mover/icechunk#2571);
     nothing goes to Source Cooperative. Kept as a record of the evidence. -->

# Reading through the S3 API is 2–5× slower than plain HTTPS on data.source.coop, because it offers HTTP/2

**Ask:** could `data.source.coop` stop offering HTTP/2, so that clients connect over HTTP/1.1, as they do
with AWS S3? That alone would remove the slowdown below for every affected client, with no change on the
client side. Browsers and other clients fall back to HTTP/1.1 without trouble. Other options are at the end.

**Why:** we read NetCDF files on Source Cooperative through Icechunk virtual stores. The same bytes read
2–5× slower when the store references them as `s3://ocean-icechunks/...` (S3 API, endpoint `data.source.coop`)
than as `https://data.source.coop/ocean-icechunks/...`. The cause is HTTP/2: `data.source.coop` offers it,
Icechunk's S3 client (the Rust AWS SDK) accepts it, and the Rust HTTP/2 client is slow for many parallel range
reads. Icechunk's HTTPS client stays on HTTP/1.1. On the other S3-compatible endpoints we tested (AWS S3,
CloudFerro), which offer only HTTP/1.1, `s3://` and `https://` read at the same speed.

The slow part appears to be on the client side (curl over HTTP/2 is fast here), and we are reporting it to
Icechunk as well. But Source Cooperative is the only S3 endpoint we have found where clients hit it.

## What we see

Concurrent range reads from `https://data.source.coop` are about half as fast over HTTP/2 as over HTTP/1.1
when the client is Rust `object_store` (obstore) or the Rust AWS SDK (hyper/h2 under both). The proxy
serves both protocols, and the S3 API itself adds no cost: over HTTP/1.1, S3 GetObject and plain GET read at
the same speed.

## Reprex

No credentials, `pip install obstore`:

```
python source_coop_reprex.py --rounds 5
```

It reads the same 320 × 1.66 MB ranges of public `ocean-icechunks/pacioos/...` objects four ways, with
64 in flight, and prints the Cloudflare colo and connect time from `/cdn-cgi/trace` (not the client IP).

<details><summary><code>source_coop_reprex.py</code> (click to expand)</summary>

```python
"""Reprex: concurrent range reads from data.source.coop are slower over HTTP/2 than HTTP/1.1.

    pip install obstore
    python source_coop_reprex.py [--rounds 5] [--requests 320] [--concurrency 64]

No credentials, no Icechunk. Uses obstore (Python bindings to Rust object_store) to fetch the same
1.66 MB byte ranges from public objects four ways, interleaved:

  S3 API   (S3Store, endpoint https://data.source.coop, path-style, unsigned)  x  HTTP/1.1 | HTTP/2
  plain GET (HTTPStore on https://data.source.coop/<account>/)                 x  HTTP/1.1 | HTTP/2

object_store uses HTTP/1.1 by default; `http2_only` switches the same client to HTTP/2. Prints the
Cloudflare edge (colo, from https://data.source.coop/cdn-cgi/trace) and a TCP connect time
(a rough round-trip time). The client's IP address is not printed.
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
    """Cloudflare colo and country from the trace endpoint, plus a TCP connect time."""
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
```

</details>

Result, 2026-11-20, from AWS us-west-2 (Cloudflare colo PDX, TCP connect ≈ 30 ms), obstore 0.12.1, 530 MB per read:

| client | median s | best s | MB/s |
|---|---|---|---|
| S3 API (S3Store, unsigned, path-style), HTTP/1.1 | 1.12 | 0.92 | 474 |
| S3 API, HTTP/2 | 1.95 | 1.55 | 272 |
| plain GET (HTTPStore), HTTP/1.1 | 0.94 | 0.87 | 562 |
| plain GET, HTTP/2 | 1.87 | 1.64 | 283 |

With curl 8.23 (nghttp2), the same 320 ranges took 1.23–1.29 s over HTTP/2 (one multiplexed connection) and
1.16–1.24 s over HTTP/1.1 (64 connections). So HTTP/2 through the proxy can be fast. The gap is specific to
the Rust hyper/h2 client, which has a known HTTP/2 throughput problem
([apache/arrow-rs-object-store#104](https://github.com/apache/arrow-rs-object-store/issues/104)).

From Google Colab the gap for the Icechunk case was larger (3–5×), so it may grow with distance to the edge.

## Other options, if turning off HTTP/2 is not practical

1. Offer an HTTP/1.1-only hostname for S3-API access. Clients that point their S3 endpoint at it would
   read at full speed. This needs a configuration change on the client side.
2. Say in the docs that S3 clients built on the Rust AWS SDK (Icechunk's `s3_store`, for example) may read
   2–5× faster over HTTP/1.1, and that `https://data.source.coop/...` URLs avoid the problem for Icechunk today.

We would also like to know whether offering HTTP/2 to S3-API clients is intentional, and whether any
per-connection or per-stream limit in the Worker or the Cloudflare front end could cap HTTP/2 throughput (for
example concurrent streams per connection, or how response bodies are streamed back through the Worker). curl's
HTTP/2 client is fast here, so we expect not, but we would rather ask than assume.

Related: ocean-icechunks/ocean-icechunks-skills#27 (investigation), ocean-icechunks/pacioos#40.
