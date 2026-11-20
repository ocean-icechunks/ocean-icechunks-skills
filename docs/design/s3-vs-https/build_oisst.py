"""Build H/S virtual Icechunk stores over 64 days of NOAA OISST v2.1 on NODD (AWS us-east-1).

H: https://noaa-cdr-sea-surface-temp-optimum-interpolation-pds.s3.amazonaws.com/...  (http_store)
S: s3://noaa-cdr-sea-surface-temp-optimum-interpolation-pds/...  (s3_store, us-east-1, anonymous)

The stores themselves go in ocean-icechunks/test-repo/s3-vs-https/oisst_nodd_64day/ on Source
Cooperative (write keys from icechunk_utils in a local ocean-icechunks/pacioos checkout); the
data stay on NODD. Kept as a record of how the test stores were made.
"""
import sys
import time
import warnings

import pandas as pd

sys.path.insert(0, "/home/jovyan/pacioos/stores")
warnings.simplefilter("ignore")

import icechunk
from obstore.store import HTTPStore
from virtualizarr import open_virtual_mfdataset
from virtualizarr.parsers import HDFParser
from virtualizarr.registry import ObjectStoreRegistry

from icechunk_utils import get_source_credentials

SRC_BUCKET = "noaa-cdr-sea-surface-temp-optimum-interpolation-pds"
HTTPS_PREFIX = f"https://{SRC_BUCKET}.s3.amazonaws.com/"
S3_PREFIX = f"s3://{SRC_BUCKET}/"
DAYS = pd.date_range("2024-01-01", periods=64, freq="D")
KEYS = [f"data/v2.1/avhrr/{d:%Y%m}/oisst-avhrr-v02r01.{d:%Y%m%d}.nc" for d in DAYS]
DEST_BUCKET = "ocean-icechunks"
DEST = "test-repo/s3-vs-https/oisst_nodd_64day"


def config_for(kind):
    cfg = icechunk.RepositoryConfig.default()
    if kind == "H":
        c = icechunk.VirtualChunkContainer(url_prefix=HTTPS_PREFIX, store=icechunk.http_store())
    else:
        c = icechunk.VirtualChunkContainer(
            url_prefix=S3_PREFIX, store=icechunk.s3_store(region="us-east-1", anonymous=True))
    cfg.set_virtual_chunk_container(c)
    return cfg


def main():
    creds, exp = get_source_credentials()
    print("keys expire", exp)
    registry = ObjectStoreRegistry({HTTPS_PREFIX: HTTPStore.from_url(HTTPS_PREFIX)})
    t0 = time.perf_counter()
    vds = open_virtual_mfdataset(
        [HTTPS_PREFIX + k for k in KEYS], registry=registry, parser=HDFParser(),
        combine="nested", concat_dim="time", coords="minimal", compat="override",
        data_vars="minimal", loadable_variables=["time", "zlev", "lat", "lon"])
    print(f"virtualized {len(KEYS)} files in {time.perf_counter()-t0:.0f}s:", dict(vds.sizes))
    for kind in ("H", "S"):
        ds = vds if kind == "H" else vds.vz.rename_paths(lambda p: p.replace(HTTPS_PREFIX, S3_PREFIX))
        storage = icechunk.s3_storage(
            bucket=DEST_BUCKET, prefix=f"{DEST}/{kind}", region=creds["region_name"],
            endpoint_url=creds["endpoint_url"], force_path_style=True,
            access_key_id=creds["aws_access_key_id"],
            secret_access_key=creds["aws_secret_access_key"],
            session_token=creds["aws_session_token"])
        if icechunk.Repository.exists(storage):
            print(kind, "already exists; skipping")
            continue
        repo = icechunk.Repository.create(storage, config_for(kind))
        repo.save_config()
        s = repo.writable_session("main")
        ds.vz.to_icechunk(s.store)
        print(kind, "committed", s.commit(f"OISST v2.1, 64 days from 2024-01-01, {kind} references"))


if __name__ == "__main__":
    main()
