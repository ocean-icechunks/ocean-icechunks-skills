"""Same https:// store, three HTTP client settings; plus the s3:// store. Full ROMS temp (64 chunks)."""
import gc, statistics, threading, time, warnings
warnings.simplefilter("ignore")
import icechunk, psutil, xarray as xr, zarr
zarr.config.set({"async.concurrency": 64})
BASE = "https://data.source.coop/ocean-icechunks/test-repo/s3-vs-https/roms_reanalysis_8day"
PFX = {"H": "https://data.source.coop/ocean-icechunks/pacioos/", "S": "s3://ocean-icechunks/pacioos/"}
SC_IPS = {a[4][0] for a in __import__("socket").getaddrinfo("data.source.coop", 443)}
me = psutil.Process()

def open_ds(kind, opts=None):
    cfg = None
    if kind == "H" and opts is not None:   # override the saved container's HTTP options at open time
        cfg = icechunk.RepositoryConfig.default()
        cfg.set_virtual_chunk_container(icechunk.VirtualChunkContainer(PFX["H"], icechunk.http_store(opts=opts)))
    repo = icechunk.Repository.open(icechunk.http_storage(f"{BASE}/{kind}"), config=cfg)
    cred = icechunk.credentials.HttpAccess if kind == "H" else icechunk.credentials.s3_anonymous_credentials()
    repo = repo.reopen(authorize_virtual_chunk_access=icechunk.containers_credentials({PFX[kind]: cred}))
    return xr.open_zarr(repo.readonly_session("main").store, consolidated=False, chunks=None)

CASES = {
    "H http1_only (default)": ("H", None),
    "H allow h2 (ALPN)": ("H", {"http1_only": "false"}),
    "H http2_only": ("H", {"http1_only": "false", "http2_only": "true"}),
    "S (AWS SDK, default)": ("S", None),
}
res = {k: [] for k in CASES}; conns = {}
for r in range(3):
    for name, (kind, opts) in CASES.items():
        ds = open_ds(kind, opts)
        peak = [0]; stop = [False]
        def watch():
            while not stop[0]:
                n = sum(1 for c in me.net_connections("tcp") if c.raddr and c.raddr.ip in SC_IPS and c.status == "ESTABLISHED")
                peak[0] = max(peak[0], n); time.sleep(0.05)
        th = threading.Thread(target=watch); th.start()
        t = time.perf_counter(); x = ds.temp.values; dt = time.perf_counter() - t
        stop[0] = True; th.join(); del x, ds; gc.collect()
        res[name].append(dt); conns[name] = max(conns.get(name, 0), peak[0])
for k, v in res.items():
    print(f"{k:24s} median {statistics.median(v):5.2f}s  best {min(v):5.2f}s  peak connections {conns[k]:3d}  {[round(x, 2) for x in v]}")
