"""Peak TCP connections to each source host during a bulk read, H vs S, for roms/oisst/globcolour.
Shows the S3 client opens 64 HTTP/1.1 connections where the server only speaks HTTP/1.1 (AWS,
CloudFerro) but about 6 HTTP/2 connections on data.source.coop. Needs psutil. No credentials."""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # for bench.py
import bench, zarr, threading, time, gc, socket, psutil
zarr.config.set({"async.concurrency": 64})
SRC = {"roms": "data.source.coop", "oisst": "noaa-cdr-sea-surface-temp-optimum-interpolation-pds.s3.amazonaws.com",
       "globcolour": "s3.waw3-1.cloudferro.com"}
S3HOST = {"oisst": "noaa-cdr-sea-surface-temp-optimum-interpolation-pds.s3.us-east-1.amazonaws.com"}
me = psutil.Process()
for dataset in ("roms", "oisst", "globcolour"):
    hosts = {SRC[dataset]} | ({S3HOST[dataset], "s3.amazonaws.com", "s3.us-east-1.amazonaws.com"} if dataset in S3HOST else set())
    ips = {a[4][0] for h in hosts for a in socket.getaddrinfo(h, 443)}
    box = bench.DATASETS[dataset][2]; var = bench.DATASETS[dataset][1]
    for kind in "HS":
        ds = bench.open_ds(kind, dataset)
        a = ds[var].isel(**box) if box else ds[var]
        if dataset == "roms": a = a.isel(time=slice(0, 32))
        peak = [0]; seen = set(); stop = [False]
        def watch():
            while not stop[0]:
                cs = [c for c in me.net_connections("tcp") if c.raddr and c.raddr.port == 443 and c.status == "ESTABLISHED"]
                src = [c for c in cs if c.raddr.ip in ips] if dataset != "oisst" else [c for c in cs if c.raddr.ip not in {x[4][0] for x in socket.getaddrinfo("data.source.coop", 443)}]
                peak[0] = max(peak[0], len(src)); seen.update(c.laddr.port for c in src); time.sleep(0.05)
        th = threading.Thread(target=watch); th.start()
        t = time.perf_counter(); a.values; dt = time.perf_counter() - t
        stop[0] = True; th.join(); del ds, a; gc.collect()
        print(f"{dataset:10s} {kind}: {dt:5.2f}s  peak connections to source {peak[0]:3d}  distinct {len(seen):3d}", flush=True)
