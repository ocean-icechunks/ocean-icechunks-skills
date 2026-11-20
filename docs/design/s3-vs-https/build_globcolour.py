"""Build H/S virtual Icechunk stores over 16 days of Copernicus GlobColour CHL on CloudFerro.

Sources: OCEANCOLOUR_GLO_BGC_L3_MY_009_103, daily 4 km, in bucket mdl-native-16 on CloudFerro's
S3-compatible storage (https://s3.waw3-1.cloudferro.com, Warsaw). Readable anonymously both ways.
H: https://s3.waw3-1.cloudferro.com/mdl-native-16/...  (http_store; what fish-pace/globcolour-Icechunks uses)
S: s3://mdl-native-16/...  (s3_store, endpoint CloudFerro, path-style, anonymous)
Only CHL is kept. Stores go in ocean-icechunks/test-repo/s3-vs-https/globcolour_chl_16day/ on
Source Cooperative (write keys via icechunk_utils from a local ocean-icechunks/pacioos checkout).
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

ENDPOINT = "https://s3.waw3-1.cloudferro.com"
SRC_BUCKET = "mdl-native-16"
HTTPS_PREFIX = f"{ENDPOINT}/{SRC_BUCKET}/"
S3_PREFIX = f"s3://{SRC_BUCKET}/"
PRODUCT = ("native/OCEANCOLOUR_GLO_BGC_L3_MY_009_103/"
           "cmems_obs-oc_glo_bgc-plankton_my_l3-multi-4km_P1D_202603")
DAYS = pd.date_range("2024-01-01", periods=16, freq="D")
KEYS = [f"{PRODUCT}/{d:%Y/%m}/{d:%Y%m%d}_cmems_obs-oc_glo_bgc-plankton_my_l3-multi-4km_P1D.nc"
        for d in DAYS]
DEST_BUCKET = "ocean-icechunks"
DEST = "test-repo/s3-vs-https/globcolour_chl_16day"
KEEP = {"CHL", "time", "lat", "lon"}


def s3_store():
    return icechunk.s3_store(region="us-east-1", endpoint_url=ENDPOINT, anonymous=True,
                             force_path_style=True, s3_compatible=True)


def config_for(kind):
    cfg = icechunk.RepositoryConfig.default()
    if kind == "H":
        c = icechunk.VirtualChunkContainer(url_prefix=HTTPS_PREFIX, store=icechunk.http_store())
    else:
        c = icechunk.VirtualChunkContainer(url_prefix=S3_PREFIX, store=s3_store())
    cfg.set_virtual_chunk_container(c)
    return cfg


def main():
    creds, exp = get_source_credentials()
    print("keys expire", exp)
    registry = ObjectStoreRegistry({f"{ENDPOINT}/": HTTPStore.from_url(f"{ENDPOINT}/")})
    t0 = time.perf_counter()
    first = open_virtual_mfdataset([HTTPS_PREFIX + KEYS[0]], registry=registry, parser=HDFParser())
    drop = [v for v in first.variables if v not in KEEP]
    vds = open_virtual_mfdataset(
        [HTTPS_PREFIX + k for k in KEYS], registry=registry, parser=HDFParser(),
        drop_variables=drop, combine="nested", concat_dim="time", coords="minimal",
        compat="override", data_vars="minimal", loadable_variables=["time", "lat", "lon"])
    print(f"virtualized {len(KEYS)} files in {time.perf_counter()-t0:.0f}s:", dict(vds.sizes),
          list(vds.data_vars))
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
        print(kind, "committed", s.commit(f"GlobColour CHL, 16 days from 2024-01-01, {kind} references"))


if __name__ == "__main__":
    main()
