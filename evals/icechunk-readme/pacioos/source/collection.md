---
level: collection
title: PacIOOS Hawaiʻi ocean, wave and weather models
source_coop:
  account: ocean-icechunks
  product: pacioos
repository: https://github.com/ocean-icechunks/pacioos
provider:
  name: PacIOOS
  long_name: Pacific Islands Ocean Observing System (PacIOOS)
  url: https://www.pacioos.hawaii.edu
  data_services_url: https://www.pacioos.hawaii.edu/data-services/
  data_services_label: Data access (PacIOOS)
viewer:
  name: Gridlook
  url: https://data.source.coop/ocean-icechunks/pacioos/viewer/index.html
  project_url: https://github.com/d70-t/gridlook
  fork_url: https://github.com/eeholmes/gridlook
products:
  - roms_hiig_reanalysis
  - roms_hiig
  - wrf_hi
  - ww3_hawaii
code_license:
  spdx: Apache-2.0
  author: E. E. Holmes
  attribution_required: false
credits:
  - label: Data
    text: >-
      PacIOOS, University of Hawaiʻi at Mānoa. ROMS ocean model: Brian S. Powell. WRF weather
      model: Yi-Leng Chen. WaveWatch III wave model: Kwok Fai Cheung.
  - label: Icechunk packaging
    text: >-
      built with [Icechunk](https://icechunk.io), [VirtualiZarr](https://virtualizarr.readthedocs.io)
      and [Xarray](https://xarray.dev), hosted on [Source Cooperative](https://source.coop/ocean-icechunks/pacioos).
  - label: Viewer
    text: >-
      [gridlook](https://github.com/d70-t/gridlook), developed by Andrej Fast, Tobi Kölling, Fabian
      Wachsmann and contributors at DKRZ and the Max Planck Institute for Meteorology. The copy
      published at `pacioos/viewer/` is built from a fork, [eeholmes/gridlook](https://github.com/eeholmes/gridlook).
netcdf_layout: <dataset>/netcdf/[<version>/]<year>/<file>.nc
---

# README

## Summary

Model output from the [Pacific Islands Ocean Observing System (PacIOOS)](https://www.pacioos.hawaii.edu)
for the main Hawaiian Islands.

# Documentation

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
