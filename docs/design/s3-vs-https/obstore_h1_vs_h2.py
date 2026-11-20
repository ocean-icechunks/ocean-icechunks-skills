"""No Icechunk: obstore (Rust object_store) S3 API vs plain HTTP, HTTP/1.1 vs HTTP/2 only, against
data.source.coop. 320 x 1.66 MB ranges, 64 in flight. Shows HTTP/2 alone cuts throughput."""
import asyncio, time, statistics, obstore
from obstore.store import S3Store, HTTPStore
KEYS = [f"pacioos/roms_hiig_reanalysis/netcdf/v2.0/2009/hiig_his_zlevel_200901{d:02d}.nc" for d in range(1, 9)]
R = 1_656_720
REQS = [(k, i * R, (i + 1) * R) for k in KEYS for i in range(40)][:320]
def s3(opts): return S3Store("ocean-icechunks", endpoint="https://data.source.coop", region="us-east-1",
                             skip_signature=True, virtual_hosted_style_request=False, client_options=opts)
def http(opts): return HTTPStore.from_url("https://data.source.coop/ocean-icechunks", client_options=opts)
async def run(store, conc=64):
    sem = asyncio.Semaphore(conc)
    async def one(k, a, b):
        async with sem: return len(await obstore.get_range_async(store, k, start=a, end=b))
    t = time.perf_counter(); n = sum(await asyncio.gather(*(one(*q) for q in REQS))); return time.perf_counter() - t
cases = {"s3 http1 (default)": lambda: s3({}), "s3 http2_only": lambda: s3({"http2_only": True}),
         "http http1 (default)": lambda: http({}), "http http2_only": lambda: http({"http2_only": True})}
res = {k: [] for k in cases}
for r in range(3):
    for k, mk in cases.items():
        res[k].append(asyncio.run(run(mk())))
for k, v in res.items():
    print(f"{k:22s} median {statistics.median(v):5.2f}s  best {min(v):5.2f}s  ({320*R/statistics.median(v)/1e6:5.0f} MB/s)  {[round(x,2) for x in v]}")
