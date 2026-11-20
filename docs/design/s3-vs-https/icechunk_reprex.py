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
