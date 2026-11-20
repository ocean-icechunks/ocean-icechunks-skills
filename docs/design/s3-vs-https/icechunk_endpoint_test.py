"""Icechunk virtual-chunk reads from a public bucket, several containers over the same bytes.

    pip install icechunk zarr numpy
    python icechunk_endpoint_test.py --target gcs|osn [--rounds 3]

Same design as icechunk_reprex.py: 64 virtual chunks of 8.3 MB (no codecs), 8 per file from 8 files, read
through

  https  http_store()                      object_store HTTP client, HTTP/1.1 only (default)
  https  http_store(http1_only=false)      same client, HTTP/2 allowed
  s3     s3_store(endpoint ...)            AWS SDK client (offers HTTP/2 first)
  gs     gcs_store()                       object_store GCS client, HTTP/1.1 (gcs target only)

Targets, both public and read without credentials:
  gcs  gs://noaa-oar-gobai on storage.googleapis.com (NOAA GOBAI NetCDF, US multi-region)
  osn  coastalbench-data on udel1.osn.mghpcc.org (CoastalBench NetCDF, OSN University of Delaware pod)
"""
import argparse
import statistics
import time

import icechunk
import numpy as np
import zarr

TARGETS = {
    "gcs": {"host": "https://storage.googleapis.com", "bucket": "noaa-oar-gobai", "gcs": True,
            "keys": [f"netcdf/v202606/no3/GOBAI-NO3-HR-v202606_{span}.nc" for span in (
                "1993-01-01_1994-11-25", "1994-12-02_1996-10-25", "1996-11-01_1998-09-25",
                "1998-10-02_2000-08-25", "2000-09-01_2002-07-26", "2002-08-02_2004-06-25",
                "2004-07-02_2006-05-26", "2006-06-02_2008-04-25")]},
    "osn": {"host": "https://udel1.osn.mghpcc.org", "bucket": "coastalbench-data", "gcs": False,
            "keys": [f"200801{d:02d}.nc" for d in range(2, 10)]},
}
CHUNK = 8_283_600
PER_FILE = 8
OFFSET0 = 100_000_000   # skip the file header region
T = {}                  # the chosen target, filled in main()


def prefix(scheme):
    return {"https": f"{T['host']}/{T['bucket']}/", "s3": f"s3://{T['bucket']}/",
            "gs": f"gs://{T['bucket']}/"}[scheme]


def cases():
    host = T["host"].removeprefix("https://")
    out = {
        "https  http_store() default (HTTP/1.1)": ("https", icechunk.http_store()),
        "https  http_store(http1_only=false)": ("https", icechunk.http_store(opts={"http1_only": "false"})),
        f"s3     s3_store(endpoint {host})": ("s3", icechunk.s3_store(
            region="us-east-1", endpoint_url=T["host"], anonymous=True, force_path_style=True)),
    }
    if T["gcs"]:
        out["gs     gcs_store()"] = ("gs", icechunk.gcs_store())
    return out


def credential(scheme):
    if scheme == "https":
        return icechunk.credentials.HttpAccess
    if scheme == "s3":
        return icechunk.credentials.s3_anonymous_credentials()
    return icechunk.credentials.gcs_anonymous_credentials()


def build(scheme, store_cfg):
    cfg = icechunk.RepositoryConfig.default()
    cfg.set_virtual_chunk_container(icechunk.VirtualChunkContainer(prefix(scheme), store_cfg))
    repo = icechunk.Repository.create(
        icechunk.in_memory_storage(), cfg,
        authorize_virtual_chunk_access=icechunk.containers_credentials({prefix(scheme): credential(scheme)}))
    s = repo.writable_session("main")
    n = len(T['keys']) * PER_FILE
    zarr.create_array(s.store, name="bytes", shape=(n * CHUNK,), chunks=(CHUNK,), dtype="uint8",
                      compressors=None, filters=None, fill_value=0)
    i = 0
    for k in T['keys']:
        for j in range(PER_FILE):
            s.store.set_virtual_ref(f"bytes/c/{i}", prefix(scheme) + k,
                                    offset=OFFSET0 + j * CHUNK, length=CHUNK)
            i += 1
    s.commit("endpoint test")
    return repo


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--target", choices=sorted(TARGETS), required=True)
    p.add_argument("--rounds", type=int, default=3)
    p.add_argument("--concurrency", type=int, default=64)
    a = p.parse_args()
    T.update(TARGETS[a.target])
    zarr.config.set({"async.concurrency": a.concurrency})
    built = {name: build(*spec) for name, spec in cases().items()}
    total = len(T['keys']) * PER_FILE * CHUNK
    print(f"icechunk {icechunk.__version__}; {T['host']}/{T['bucket']}; {len(T['keys']) * PER_FILE} chunks x "
          f"{CHUNK / 1e6:.1f} MB = {total / 1e6:.0f} MB per read; zarr concurrency {a.concurrency}")
    times, sums = {k: [] for k in built}, {}
    for r in range(a.rounds):
        for name, repo in built.items():
            arr = zarr.open_array(repo.readonly_session("main").store, path="bytes", mode="r")
            t = time.perf_counter()
            try:
                x = arr[:]
            except Exception as e:  # noqa: BLE001
                print(f"  round {r + 1} {name}: FAILED: {str(e).splitlines()[0][:200]}", flush=True)
                continue
            times[name].append(time.perf_counter() - t)
            print(f"  round {r + 1} {name:48s} {times[name][-1]:6.2f} s", flush=True)
            sums[name] = int(x[:: 1 << 20].astype(np.int64).sum())
            del x
    print(f"\n{'client':48s} {'median s':>9s} {'best s':>8s} {'MB/s':>7s}")
    for name, v in times.items():
        if v:
            print(f"{name:48s} {statistics.median(v):9.2f} {min(v):8.2f} {total / statistics.median(v) / 1e6:7.0f}")
    print(f"\nsame bytes from every client that succeeded: {len(set(sums.values())) == 1}")


if __name__ == "__main__":
    main()
