"""Build two tiny virtual Icechunk stores over the same 8 PacIOOS ROMS files.

H: references https://data.source.coop/ocean-icechunks/pacioos/...  (http_store)
S: references s3://ocean-icechunks/pacioos/...  (s3_store, endpoint data.source.coop)

S is made from H's references by renaming the prefix, the fix suggested in
ocean-icechunks/pacioos#40. Writes only under ocean-icechunks/test-repo/.
"""
import sys
import time
import warnings

sys.path.insert(0, "/home/jovyan/pacioos/stores")
warnings.simplefilter("ignore")

import icechunk
import xarray as xr
from obstore.store import HTTPStore
from virtualizarr import open_virtual_mfdataset
from virtualizarr.parsers import HDFParser
from virtualizarr.registry import ObjectStoreRegistry

from icechunk_utils import get_source_credentials

HOST = "https://data.source.coop"
BUCKET = "ocean-icechunks"
KEY_PREFIX = "pacioos/roms_hiig_reanalysis/netcdf/v2.0/2009/"
HTTPS_PREFIX = f"{HOST}/{BUCKET}/pacioos/"
S3_PREFIX = f"s3://{BUCKET}/pacioos/"
DEST = "test-repo/s3-vs-https/roms_reanalysis_8day"
FILES = [f"{KEY_PREFIX}hiig_his_zlevel_200901{d:02d}.nc" for d in range(1, 9)]


def config_for(kind):
    cfg = icechunk.RepositoryConfig.default()
    if kind == "H":
        store = icechunk.http_store()
        prefix = HTTPS_PREFIX
    else:
        # The endpoint lives in the repository config, so readers should not need it.
        store = icechunk.s3_store(region="us-east-1", endpoint_url=HOST,
                                  allow_http=False, anonymous=True, force_path_style=True)
        prefix = S3_PREFIX
    cfg.set_virtual_chunk_container(icechunk.VirtualChunkContainer(url_prefix=prefix, store=store))
    return cfg


def storage_for(kind, creds):
    return icechunk.s3_storage(
        bucket=BUCKET, prefix=f"{DEST}/{kind}", region=creds["region_name"],
        endpoint_url=creds["endpoint_url"], force_path_style=True,
        access_key_id=creds["aws_access_key_id"],
        secret_access_key=creds["aws_secret_access_key"],
        session_token=creds["aws_session_token"])


def main():
    creds, exp = get_source_credentials()
    print("keys expire", exp)
    registry = ObjectStoreRegistry({f"{HOST}/": HTTPStore.from_url(f"{HOST}/")})
    t0 = time.perf_counter()
    vds = open_virtual_mfdataset(
        [f"{HOST}/{BUCKET}/{k}" for k in FILES], registry=registry, parser=HDFParser(),
        combine="nested", concat_dim="time", coords="minimal", compat="override",
        data_vars="minimal", loadable_variables=["time"])
    print(f"virtualized {len(FILES)} files in {time.perf_counter()-t0:.0f}s:", dict(vds.sizes))

    for kind in ("H", "S"):
        ds = vds if kind == "H" else vds.vz.rename_paths(
            lambda p: p.replace(HTTPS_PREFIX, S3_PREFIX))
        storage = storage_for(kind, creds)
        if icechunk.Repository.exists(storage):
            print(kind, "already exists; skipping")
            continue
        repo = icechunk.Repository.create(storage, config_for(kind))
        repo.save_config()
        s = repo.writable_session("main")
        ds.vz.to_icechunk(s.store)
        print(kind, "committed", s.commit(f"8 ROMS reanalysis days, {kind} references"))


if __name__ == "__main__":
    main()
