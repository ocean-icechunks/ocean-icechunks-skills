"""Trace what Icechunk's HTTP and S3 clients send for the same virtual-chunk reads.

Start logging_proxy.py first:  python logging_proxy.py https://data.source.coop 8765 trace.jsonl
Then:                          python trace_requests.py 8765 trace.jsonl

Builds two in-memory virtual stores over 8 PacIOOS ROMS files, both routed through the local proxy:
  H': http://127.0.0.1:PORT/ocean-icechunks/pacioos/...   (http_store)
  S': s3://ocean-icechunks/pacioos/...  (s3_store, endpoint http://127.0.0.1:PORT, path-style, anonymous)
then reads the whole `temp` variable (64 chunks) through each and summarizes the proxy log.
"""
import json
import statistics
import sys
import time
import warnings

warnings.simplefilter("ignore")

import icechunk
import xarray as xr
import zarr
from obstore.store import HTTPStore
from virtualizarr import open_virtual_mfdataset
from virtualizarr.parsers import HDFParser
from virtualizarr.registry import ObjectStoreRegistry

PORT, LOG = int(sys.argv[1]), sys.argv[2]
HOST = "https://data.source.coop"
LOCAL = f"http://127.0.0.1:{PORT}"
KEYS = [f"ocean-icechunks/pacioos/roms_hiig_reanalysis/netcdf/v2.0/2009/hiig_his_zlevel_200901{d:02d}.nc"
        for d in range(1, 9)]
PREFIX = {"H": f"{LOCAL}/ocean-icechunks/pacioos/", "S": "s3://ocean-icechunks/pacioos/"}


def build(vds, kind):
    cfg = icechunk.RepositoryConfig.default()
    store = (icechunk.http_store() if kind == "H" else icechunk.s3_store(
        region="us-east-1", endpoint_url=LOCAL, allow_http=True, anonymous=True, force_path_style=True))
    cfg.set_virtual_chunk_container(icechunk.VirtualChunkContainer(url_prefix=PREFIX[kind], store=store))
    cred = icechunk.credentials.HttpAccess if kind == "H" else icechunk.credentials.s3_anonymous_credentials()
    repo = icechunk.Repository.create(icechunk.in_memory_storage(), cfg,
                                      authorize_virtual_chunk_access=icechunk.containers_credentials({PREFIX[kind]: cred}))
    ds = vds.vz.rename_paths(lambda p: p.replace(f"{HOST}/ocean-icechunks/pacioos/", PREFIX[kind]))
    s = repo.writable_session("main")
    ds.vz.to_icechunk(s.store)
    s.commit("trace")
    return repo


def lines():
    with open(LOG) as f:
        return [json.loads(x) for x in f]


def main():
    zarr.config.set({"async.concurrency": 64})
    reg = ObjectStoreRegistry({f"{HOST}/": HTTPStore.from_url(f"{HOST}/")})
    vds = open_virtual_mfdataset([f"{HOST}/{k}" for k in KEYS], registry=reg, parser=HDFParser(),
                                 combine="nested", concat_dim="time", coords="minimal",
                                 compat="override", data_vars="minimal", loadable_variables=["time"])
    for kind in ("H", "S", "H", "S"):
        repo = build(vds, kind)
        ds = xr.open_zarr(repo.readonly_session("main").store, consolidated=False, chunks=None)
        n0 = len(lines())
        t = time.perf_counter()
        ds.temp.values
        wall = time.perf_counter() - t
        time.sleep(0.5)
        new = [r for r in lines()[n0:] if r["method"] == "GET"]
        sizes = [r["bytes"] for r in new]
        print(f"\n{kind}: full temp in {wall:.2f}s through proxy; {len(new)} GETs, "
              f"{sum(sizes)/1e6:.0f} MB, per-request bytes median {statistics.median(sizes)/1e6:.2f} MB")
        print(f"   ttfb median {statistics.median(r['ttfb_s'] for r in new):.3f}s  "
              f"total median {statistics.median(r['total_s'] for r in new):.3f}s  "
              f"max {max(r['total_s'] for r in new):.3f}s")
        span = max(r["t"] + r["total_s"] for r in new) - min(r["t"] for r in new)
        # how many requests were in flight at once
        ev = sorted([(r["t"], 1) for r in new] + [(r["t"] + r["total_s"], -1) for r in new])
        cur = peak = 0
        for _, d in ev:
            cur += d
            peak = max(peak, cur)
        print(f"   span {span:.2f}s, peak concurrent requests {peak}")
        ex = new[0]
        print("   example:", ex["path"][-60:], "?" + ex["query"] if ex["query"] else "")
        print("   headers:", {k: v for k, v in ex["req_headers"].items() if k.lower() != "host"})
        print("   server-timing:", ex["server_timing"], "| cf-cache:", ex["cf_cache"])


if __name__ == "__main__":
    main()
