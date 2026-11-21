# PacIOOS Hawaiʻi ocean, wave and weather models: documentation

Technical detail for the [PacIOOS product](https://source.coop/ocean-icechunks/pacioos): how the
stores work, how to reach the NetCDF copies directly, known problems, and how it was all built.

## About the data

The ocean, wave and weather models are run at the University of Hawaiʻi at Mānoa. The original
NetCDF files are copied here **unchanged**, and [Icechunk](https://icechunk.io) stores are built
over them, so that a whole archive opens in about a second as one lazy `xarray` dataset.

PacIOOS's own pages for each dataset:
[ROMS reanalysis v2.0](https://www.pacioos.hawaii.edu/metadata/roms_hiig_reanalysis.html) ·
[Currents forecast (ROMS)](https://www.pacioos.hawaii.edu/currents/model-hawaii/) ·
[Wind forecast (WRF)](https://www.pacioos.hawaii.edu/weather/model-wind-hawaii/) ·
[Wave forecast (WaveWatch III)](https://www.pacioos.hawaii.edu/waves/model-hawaii/)

## The Icechunk stores

The Icechunk stores are **virtual**. Each holds only Zarr metadata and byte-range references
to the NetCDF copies beside it, so both the store and its data are served by Source
Cooperative. As of 2026-11-18, NetCDF copies extend to the 2026-11-17 ROMS run and 2026-11-16
WW3 run. The ROMS forecast and WW3 stores include those runs, with forecast coverage
through 2026-11-24T00Z and 2026-11-23T18Z, respectively. The latest copied WRF run is dated
2026-11-15 and the WRF Icechunk forecast extends through 2026-11-22T00Z.
A daily update is planned. Where the files lack
metadata (WW3 above all), the stores take PacIOOS's ERDDAP attributes, and each store's
`metadata_source` attribute says so.

Each dataset's README has tested loading code. Python 3.12 or newer and icechunk 2.3 or newer
are required; no credentials are needed.

## The viewer

One viewer, [`pacioos/viewer/`](https://data.source.coop/ocean-icechunks/pacioos/viewer/index.html),
serves every store; its dataset picker lists them all. It draws in an ordinary browser, with no
extension.

## NetCDF copies

Anonymous HTTPS (with byte ranges) or S3 (endpoint `https://data.source.coop`, bucket
`ocean-icechunks`), at

```
https://data.source.coop/ocean-icechunks/pacioos/<dataset>/netcdf/[<version>/]<year>/<file>.nc
```

Each file has an `.md5` beside it. The copies are **write-once**: a new version of a dataset
goes in a new folder (for example `netcdf/v3.0/`), and existing files are never changed.

## Known problems in the files

Relabelled WRF runs in 2010–13, WW3 cold starts, and others are listed in the
[file audit](https://github.com/ocean-icechunks/pacioos/blob/main/audit/report-pacioos.md).

## How this was built

The code, notes and audit are in
[ocean-icechunks/pacioos](https://github.com/ocean-icechunks/pacioos). The files were copied
from the PacIOOS server with `rclone` and checked against MD5 sums. Each store is built in the
same order: a written plan, a local smoke test, a scratch store with a viewer, then the
published store, which is validated anonymously from its public URL against netCDF-C reads of
the files.

The build files are published here too, in `docs/` folders: in each product's `docs/`
(`roms_hiig/docs/`, `roms_hiig_reanalysis/docs/`, `ww3_hawaii/docs/`) the store's
`requirements.txt`, smoke-test notebook(s), `build_store.py` and the modules it uses, the saved
ERDDAP metadata, and `how_store_created.md` (how it was made and how to rebuild it); in this
collection's [`docs/`](https://data.source.coop/ocean-icechunks/pacioos/docs/), the shared
modules and scripts (`pacioos_virtual.py`, `icechunk_utils.py`, `best_series_update.py`,
`publish_viewer.py`, ...) and the shared `requirements.txt`. The builds
are Python scripts rather than one production notebook; `build_store.py` is that step. The WRF
store's build files are in [`wrf_hi/build-source.zip`](https://data.source.coop/ocean-icechunks/pacioos/wrf_hi/build-source.zip).
