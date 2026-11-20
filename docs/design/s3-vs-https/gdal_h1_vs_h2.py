"""GDAL /vsicurl/ and /vsis3/ reads from data.source.coop, HTTP/1.1 vs HTTP/2 (GDAL_HTTP_VERSION)."""
import os, statistics, sys, time
from concurrent.futures import ThreadPoolExecutor
from osgeo import gdal
gdal.UseExceptions()
KEYS = [f"ocean-icechunks/pacioos/roms_hiig_reanalysis/netcdf/v2.0/2009/hiig_his_zlevel_200901{d:02d}.nc" for d in range(1, 9)]
R = 1_656_720
os.environ.update(AWS_S3_ENDPOINT="data.source.coop", AWS_NO_SIGN_REQUEST="YES", AWS_VIRTUAL_HOSTING="FALSE")
gdal.SetConfigOption("VSI_CACHE", "FALSE")
gdal.SetConfigOption("CPL_VSIL_CURL_NON_CACHED", "/vsicurl/:/vsis3/")   # no GDAL block cache between runs

def path(kind, k): return f"/vsicurl/https://data.source.coop/{k}" if kind == "vsicurl" else f"/vsis3/{k}"

def big(kind):   # one 100 MB read (GDAL may split it)
    f = gdal.VSIFOpenL(path(kind, KEYS[0]), "rb"); gdal.VSIFSeekL(f, 50_000_000, 0)
    t = time.perf_counter(); n = len(gdal.VSIFReadL(1, 100_000_000, f)); dt = time.perf_counter() - t
    gdal.VSIFCloseL(f); assert n == 100_000_000; return dt

def ranges(kind, threads=16, n=128):   # 128 x 1.66 MB from 16 threads, each with its own handle
    reqs = [(k, i * R) for k in KEYS for i in range(16)][:n]
    def one(q):
        f = gdal.VSIFOpenL(path(kind, q[0]), "rb"); gdal.VSIFSeekL(f, q[1], 0)
        b = gdal.VSIFReadL(1, R, f); gdal.VSIFCloseL(f); return len(b)
    t = time.perf_counter()
    with ThreadPoolExecutor(threads) as ex: tot = sum(ex.map(one, reqs))
    assert tot == n * R; return time.perf_counter() - t

res = {}
for rnd in range(3):
    for ver in ("1.1", "2TLS"):
        gdal.SetConfigOption("GDAL_HTTP_VERSION", ver)
        for kind in ("vsicurl", "vsis3"):
            for test, fn in (("100 MB read", big), ("128 ranges x16 threads", ranges)):
                gdal.VSICurlClearCache()
                res.setdefault((test, kind, ver), []).append(fn(kind))
for (test, kind, ver), v in sorted(res.items()):
    print(f"{test:24s} {kind:8s} HTTP {ver:5s} median {statistics.median(v):5.2f}s  {[round(x, 2) for x in v]}")
print("GDAL", gdal.__version__)
