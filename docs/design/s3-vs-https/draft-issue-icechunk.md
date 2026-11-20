<!-- DRAFT for earth-mover/icechunk. Not posted. Review before filing. -->

# `s3_store` reads are ~2× slower than `http_store` on endpoints that offer HTTP/2

**Ask:** please make `s3_store` virtual chunk reads use HTTP/1.1, as `http_store` already does, or give
users a way to force it.

**Why it matters:** `s3_store` uses the AWS SDK's default HTTP client, which negotiates HTTP/2 whenever the
server offers it. `http_store` uses `object_store`, which stays on HTTP/1.1. So on any endpoint that offers
HTTP/2, expect `s3_store` to read the same bytes more slowly than `http_store`. On endpoints that offer only
HTTP/1.1 (AWS S3, Tigris, Wasabi, CloudFerro) both clients use HTTP/1.1 and read equally fast.

Endpoints we found offering HTTP/2: Source Cooperative (`data.source.coop`), OSN (`uri.osn.mghpcc.org`) and
GCS (`storage.googleapis.com`). We measured two of them. The same 64 virtual chunks (530 MB) read, median of 3:

| container | Source Cooperative | GCS (`gs://noaa-oar-gobai`) |
|---|---|---|
| `http_store()` (HTTP/1.1) | 1.1 s | 1.6 s |
| `http_store(opts={"http1_only": "false"})` (HTTP/2) | 2.4 s | 3.0 s |
| `s3_store(endpoint_url=..., anonymous=True, force_path_style=True)` (HTTP/2) | 2.3 s | 3.3 s |
| `gcs_store()` (object_store, HTTP/1.1) | — | 1.7 s |

Measured from AWS us-west-2; from Google Colab, `s3_store` on Source Cooperative was 3–5× slower than
`http_store`. During the reads, the HTTP/2 clients held about 6 connections and the HTTP/1.1 client about 69.
Turning HTTP/2 on for `http_store` reproduces the slowdown, so the cause is HTTP/2, not the S3 API.

**This is a known problem:** `object_store` defaults to HTTP/1.1 for exactly this reason
(`object_store` 0.14 `src/client/mod.rs`: "HTTP/2 is known to be significantly slower than HTTP/1, so we
default to HTTP/1 for now"). See [apache/arrow-rs-object-store#104](https://github.com/apache/arrow-rs-object-store/issues/104):
one HTTP/2 client stuck at ~250 MB/s whatever the concurrency, against ~1,280 MB/s over HTTP/1.1. It points to
hyper's HTTP/2 client. Other clients are fine over HTTP/2 on the same endpoint: curl and GDAL read as fast as
over HTTP/1.1.

**Where in the code (v2.3.1):** `icechunk-s3/src/lib.rs` `mk_client` uses the SDK's default HTTP client;
`aws-smithy-http-client` 1.5 offers ALPN `["h2", "http/1.1"]` (`src/client/tls/rustls_provider.rs:322`).

## Reprex

`pip install icechunk zarr numpy`, no credentials. An in-memory repo with one uint8 array whose 64 chunks
are virtual references to 8.3 MB byte ranges of public files on Source Cooperative, read through the
three containers above.

<details><summary><code>icechunk_reprex.py</code> (click to expand)</summary>

```python
"""Reprex: Icechunk virtual-chunk reads from data.source.coop, s3_store vs http_store.

    pip install icechunk zarr numpy
    python icechunk_reprex.py [--rounds 5]

No credentials, no xarray/VirtualiZarr. Builds an in-memory Icechunk repo holding one uint8 array
whose 64 chunks are virtual references to consecutive 8.3 MB byte ranges of public files on
Source Cooperative (no codecs, so a chunk read is exactly a range read). The same references are
read three ways:

  http_store()                            default object_store client: HTTP/1.1 only
  http_store(opts={"http1_only": "false"})  same client, HTTP/2 allowed via ALPN
  s3_store(endpoint_url=data.source.coop)   AWS SDK client: offers h2 first, so HTTP/2 here

Each 8.3 MB chunk is fetched by Icechunk as several concurrent range requests.
"""
import argparse
import os
import statistics
import time

import icechunk
import numpy as np
import zarr

ENDPOINT = "https://data.source.coop"
ACCOUNT = "ocean-icechunks"
KEYS = [f"pacioos/roms_hiig_reanalysis/netcdf/v2.0/2009/hiig_his_zlevel_200901{d:02d}.nc"
        for d in range(1, 9)]  # public, ~267 MB each
CHUNK = 8_283_600              # bytes per chunk (one ROMS time step in the original test)
PER_FILE = 8
PREFIX = {"https": f"{ENDPOINT}/{ACCOUNT}/", "s3": f"s3://{ACCOUNT}/"}


def stores():
    return {
        "https  http_store() default (HTTP/1.1)": ("https", icechunk.http_store()),
        "https  http_store(http1_only=false)": ("https", icechunk.http_store(opts={"http1_only": "false"})),
        "s3     s3_store(endpoint data.source.coop)": ("s3", icechunk.s3_store(
            region="us-east-1", endpoint_url=ENDPOINT, anonymous=True, force_path_style=True)),
    }


def build(scheme, store_cfg):
    cfg = icechunk.RepositoryConfig.default()
    cfg.set_virtual_chunk_container(icechunk.VirtualChunkContainer(PREFIX[scheme], store_cfg))
    cred = (icechunk.credentials.HttpAccess if scheme == "https"
            else icechunk.credentials.s3_anonymous_credentials())
    repo = icechunk.Repository.create(
        icechunk.in_memory_storage(), cfg,
        authorize_virtual_chunk_access=icechunk.containers_credentials({PREFIX[scheme]: cred}))
    s = repo.writable_session("main")
    n = len(KEYS) * PER_FILE
    zarr.create_array(s.store, name="bytes", shape=(n * CHUNK,), chunks=(CHUNK,), dtype="uint8",
                      compressors=None, filters=None, fill_value=0)
    i = 0
    for k in KEYS:
        for j in range(PER_FILE):
            s.store.set_virtual_ref(f"bytes/c/{i}", PREFIX[scheme] + k, offset=j * CHUNK, length=CHUNK)
            i += 1
    s.commit("reprex")
    return repo


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--rounds", type=int, default=5)
    p.add_argument("--concurrency", type=int, default=64, help="zarr async.concurrency")
    a = p.parse_args()
    zarr.config.set({"async.concurrency": a.concurrency})
    cases = {name: build(*spec) for name, spec in stores().items()}
    total = len(KEYS) * PER_FILE * CHUNK
    print(f"icechunk {icechunk.__version__}, zarr {zarr.__version__}; {len(KEYS) * PER_FILE} chunks x "
          f"{CHUNK / 1e6:.1f} MB = {total / 1e6:.0f} MB per read; zarr concurrency {a.concurrency}")
    times, sums, failures = {k: [] for k in cases}, {}, {k: 0 for k in cases}
    for r in range(a.rounds):
        for name, repo in cases.items():  # interleave so a slow minute hits all cases
            arr = zarr.open_array(repo.readonly_session("main").store, path="bytes", mode="r")
            t = time.perf_counter()
            try:
                x = arr[:]
            except Exception as e:  # noqa: BLE001  report and go on: one timeout should not end the run
                failures[name] += 1
                print(f"  round {r + 1} {name}: FAILED after {time.perf_counter() - t:.0f}s: "
                      f"{str(e).splitlines()[0][:160]}", flush=True)
                continue
            times[name].append(time.perf_counter() - t)
            print(f"  round {r + 1} {name:42s} {times[name][-1]:6.2f} s", flush=True)
            sums[name] = int(x[:: 1 << 20].astype(np.int64).sum())
            del x
    same = len(set(sums.values())) == 1
    print(f"\n{'client':42s} {'median s':>9s} {'best s':>8s} {'MB/s':>7s} {'failed':>7s}")
    for name, v in times.items():
        if v:
            print(f"{name:42s} {statistics.median(v):9.2f} {min(v):8.2f} "
                  f"{total / statistics.median(v) / 1e6:7.0f} {failures[name]:7d}")
        else:
            print(f"{name:42s} {'-':>9s} {'-':>8s} {'-':>7s} {failures[name]:7d}")
    print(f"\nsame bytes from every client: {same}")


if __name__ == "__main__":
    main()
```

</details>

Example output (icechunk 2.3.1, zarr 3.4.2, AWS us-west-2, 3 rounds):

```
client                                      median s   best s    MB/s  failed
https  http_store() default (HTTP/1.1)          1.62     1.25     328       0
https  http_store(http1_only=false)             2.19     1.87     242       0
s3     s3_store(endpoint data.source.coop)      2.52     2.01     210       0
```

Context: ocean-icechunks/pacioos#40 (a suggestion to switch PacIOOS references from `https://` to `s3://`)
and the investigation in ocean-icechunks/ocean-icechunks-skills#27.
