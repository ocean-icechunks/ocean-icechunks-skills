"""Read the H (https://) and S (s3://) test stores anonymously and time the same reads.

Usage: python bench.py [--dataset roms|oisst|globcolour] [--repeats N] [--label NAME] [--json FILE]
Needs only icechunk, xarray, zarr, numpy. No credentials.
"""
import argparse
import json
import platform
import socket
import statistics
import time
import warnings

warnings.simplefilter("ignore")

import icechunk
import numpy as np
import xarray as xr
import zarr

ROOT = "https://data.source.coop/ocean-icechunks/test-repo/s3-vs-https"
# name: (store folder, variable to read, region box or None)
DATASETS = {
    "roms": ("roms_reanalysis_8day", "temp", None),   # Source Coop sources, ~8.3 MB uncompressed chunks
    "oisst": ("oisst_nodd_64day", "sst", None),       # NODD AWS us-east-1, ~1 MB gzip chunks
    # CloudFerro (Warsaw) S3-compatible store, 256x256 gzip chunks. A global day is 578 chunks and
    # 150 MB, so reads use a 1024 x 2048 box: 32 chunks per day, 512 for all 16 days (~128 MB).
    "globcolour": ("globcolour_chl_16day", "CHL", {"lat": slice(1024, 2048), "lon": slice(4096, 6144)}),
}
DATASET = "roms"


def authorize(repo):
    """Anonymous access for every container the store names, by its type."""
    auth = {}
    for prefix, c in (repo.config.virtual_chunk_containers or {}).items():
        if prefix.startswith("s3://"):
            auth[prefix] = icechunk.credentials.s3_anonymous_credentials()
        elif prefix.startswith(("http://", "https://")):
            auth[prefix] = icechunk.credentials.HttpAccess
        else:
            raise ValueError(f"no anonymous rule for {prefix}")
    return repo.reopen(authorize_virtual_chunk_access=icechunk.containers_credentials(auth))


def open_ds(kind, dataset=None):
    folder = DATASETS[dataset or DATASET][0]
    repo = authorize(icechunk.Repository.open(icechunk.http_storage(f"{ROOT}/{folder}/{kind}")))
    return xr.open_zarr(repo.readonly_session("main").store, consolidated=False, chunks=None)


def pick_var(ds, prefer="temp"):
    """`prefer` if present, else the largest variable with time (ties broken by name),
    so both stores always read the same variable."""
    if prefer in ds.data_vars:
        return prefer
    cands = sorted(v for v in ds.data_vars if "time" in ds[v].dims)
    return max(cands, key=lambda v: (ds[v].ndim, ds[v].size))


def cases(ds, var, box=None):
    a = ds[var].isel(**box) if box else ds[var]
    mid = {d: a.sizes[d] // 2 for d in a.dims if d != "time"}
    surf = {d: 0 for d in ("depth", "zlev") if d in a.dims}
    return {
        "one_slice": lambda: a.isel(time=0, **surf).values,
        "point_series": lambda: a.isel(**mid).values,
        "surface_all_times": lambda: a.isel(**surf).values,
        "full_variable": lambda: a.values,
    }


def timed(fn):
    t0 = time.perf_counter()
    out = fn()
    return time.perf_counter() - t0, out


def run(repeats=3, label=None, kinds=("H", "S"), dataset=None):
    dataset = dataset or DATASET
    zarr.config.set({"async.concurrency": 64})
    results = {"label": label or socket.gethostname(), "dataset": dataset,
               "python": platform.python_version(),
               "icechunk": icechunk.__version__, "repeats": repeats, "times": {}}
    checks = {}
    # Alternate H and S each round so slow network moments hit both alike.
    for r in range(repeats):
        for kind in kinds:
            dt, ds = timed(lambda: open_ds(kind, dataset))
            results["times"].setdefault(kind, {}).setdefault("open", []).append(dt)
            var = pick_var(ds, DATASETS[dataset][1])
            for name, fn in cases(ds, var, DATASETS[dataset][2]).items():
                dt, arr = timed(fn)
                results["times"][kind].setdefault(name, []).append(dt)
                if r == 0:
                    checks.setdefault(name, {})[kind] = (float(np.nansum(arr)), arr.shape)
    results["variable"] = var
    results["same_values"] = all(len({str(v) for v in c.values()}) == 1 for c in checks.values())
    return results


def report(results):
    print(f"{results['label']} [{results.get('dataset', 'roms')}]: icechunk {results['icechunk']}, variable {results['variable']}, "
          f"{results['repeats']} repeats; H and S values identical: {results['same_values']}")
    t = results["times"]
    print(f"{'read':20s} {'H https (s)':>22s} {'S s3 (s)':>22s} {'S/H':>6s}")
    for name in t["H"]:
        h, s = t["H"][name], t["S"][name]
        fmt = lambda x: f"{statistics.median(x):6.2f} [{min(x):.2f}-{max(x):.2f}]"
        print(f"{name:20s} {fmt(h):>22s} {fmt(s):>22s} "
              f"{statistics.median(s) / statistics.median(h):6.2f}")
    print("median [min-max]; first round is cold, later rounds may be warmer at the server/CDN")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--repeats", type=int, default=3)
    p.add_argument("--label")
    p.add_argument("--json")
    p.add_argument("--dataset", default="roms", choices=sorted(DATASETS))
    a = p.parse_args()
    res = run(a.repeats, a.label, dataset=a.dataset)
    report(res)
    if a.json:
        with open(a.json, "w") as f:
            json.dump(res, f, indent=1)
