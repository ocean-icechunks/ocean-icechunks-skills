---
level: product
id: roms_hiig
collection: collection.md
title: "PacIOOS ROMS Hawaiʻi forecast: Icechunk store, best time series"
row:
  name: ROMS ocean forecast
  detail: daily runs
  short_name: ROMS forecast, best time series
  store_note: best time series
store_url: https://data.source.coop/ocean-icechunks/pacioos/roms_hiig/icechunk
netcdf_url: https://data.source.coop/ocean-icechunks/pacioos/roms_hiig/netcdf/
provider_page:
  label: PacIOOS dataset page
  url: https://www.pacioos.hawaii.edu/metadata/roms_hiig.html
viewer:
  variable: temp
  view: px=0::py=0::alt=4000000::lat=20.5::lon=-158.2::dimIndices_time=0::dimIndices_depth=0
  fields:
    - {label: Potential temperature, variable: temp}
    - {label: Salinity, variable: salt}
    - {label: Eastward current, variable: u}
    - {label: Northward current, variable: v}
    - {label: Sea-surface height, variable: zeta, view: px=0::py=0::alt=4000000::lat=20.5::lon=-158.2::dimIndices_time=0}
coordinate_notes:
  time: 2025-01-01T00Z to 7 days after the newest run, every 3 hours
  forecast_reference_time: the run each step comes from (NaT if no run covers it)
  forecast_period: hours since that run's start, 0 to 168
  depth: 0.25 to 5,500 m, positive down
order:
  variables: [temp, salt, u, v, zeta, mask]
  coordinates: [time, forecast_reference_time, forecast_period, depth, lat, lon]
variable_notes:
  mask: land/sea mask from the files (0 land, 1 water)
code:
  python:
    python_version: "3.12"
    packages: [icechunk >= 2.3, xarray, zarr]
    pip: pip install "icechunk>=2.3" xarray zarr
    function: open_forecast
    docstring: Open the PacIOOS ROMS Hawaii forecast, best time series. `ref` is a branch or tag.
    concurrency: 128
    dask_example: The last example below does this; it needs `dask` (`pip install dask`).
performance:
  rows:
    - {read: One surface map, chunks: 1, data_moved: 230 KB, time: 0.2 s}
    - {read: "One 3-D field, 36 levels", chunks: 36, data_moved: 8.3 MB, time: 0.8 s}
    - {read: "Point series, one depth, 5,497 steps", chunks: 5497, data_moved: 1.3 GB, time: 8.5 s}
  measured: '2026-11-14 from a JupyterHub, with `zarr.config.set({"async.concurrency": 128})` and `chunks=None`'
provenance:
  built: 2026-11-14
  build_script: build_store.py
  build_url: https://github.com/ocean-icechunks/pacioos/tree/main/stores/roms_hiig
  tested_with: icechunk 2.3.1, virtualizarr 2.8.0, xarray 2026.9.0, zarr 3.4.2, Python 3.12
  build_files:
    - requirements.txt
    - build_store.py
    - forecast_store.py
    - update_store.py
    - {file: forecast-smoke-test-local.ipynb, label: the local smoke-test notebook}
    - erddap_metadata.json
    - how_store_created.md
  how_made:
    file: how_store_created.md
    url: https://github.com/ocean-icechunks/pacioos/blob/main/stores/roms_hiig/how_store_created.md
  plan:
    label: "issue #10"
    url: https://github.com/ocean-icechunks/pacioos/issues/10
citation_extra: The model runs are produced by Brian Powell (University of Hawaiʻi at Mānoa).
metadata:
  netcdf_attributes: true
---

# README

## Summary

An [Icechunk](https://icechunk.io) store of the **PacIOOS Regional Ocean Modeling System (ROMS)
7-day forecast for the main Hawaiian Islands**. It is 3-hourly from 2025-01-01, at about 4 km
resolution, on 36 depth levels from 0.25 m to 5,500 m. A new run starts every day at 00Z, after
data assimilation (satellite SST and sea-surface height, HF-radar currents, Argo and glider
profiles). Its boundaries come from global HYCOM and its atmospheric forcing from the PacIOOS
WRF model.

## Notes

**It is the "best" time series, as PacIOOS's THREDDS and ERDDAP serve it.** The daily runs
overlap: each covers 7 days. The store has one time axis, and at each time it takes the newest
run that has it. So the past is a chain of each run's first day, and the last 7 days are the
newest run's forecast. Two coordinates on `time` say where each value came from:
`forecast_reference_time` (the run) and `forecast_period` (hours into it).

## Variable notes

Land, and depths below the sea floor, read as `NaN`.

## Example analyses

```python
# The surface temperature forecast 3 days after the start of the newest run
newest_run = ds.forecast_reference_time.values.max()
sst = ds.temp.sel(depth=0.25, time=newest_run + np.timedelta64(3, "D"))

# A 2025 surface time series off south Oʻahu, and which run each value came from
series = ds.temp.sel(depth=0.25).sel(lat=21.2, lon=-157.9, method="nearest").sel(
    time=slice("2025-01-01", "2025-12-31")).load()
print(float(sst.mean()), float(series.mean()))
print(series.forecast_reference_time.values[:10])

# A July 2025 mean surface temperature map, with dask: subset first, then chunk the subset
# (248 time steps in 31 tasks of 8)
july = ds.temp.sel(depth=0.25, time=slice("2025-07-01", "2025-07-31")).chunk(time=8)
mean_sst = july.mean("time").compute()
```

## Source files

PacIOOS's daily forecast files `hiig_forec_YYYYMMDD.nc` (NetCDF-3,
uncompressed), copied unchanged from PacIOOS to Source Cooperative, each with an `.md5` beside
it. 657 runs, 2025-01-01 to 2026-11-17 (2026-11-18); 29 days have no run, at most 3 in a row.

# Documentation

## A virtual store

**This store is virtual.** It holds Zarr metadata and byte-range references, and no array data.
Every data read goes to the daily NetCDF files, copied unchanged from PacIOOS to Source
Cooperative at `https://data.source.coop/ocean-icechunks/pacioos/roms_hiig/netcdf/`.

## What the store adds over the files

**One dataset** instead of hundreds of overlapping 1.9 GB files, the best-series rule already
applied, corrected metadata, and chunks of **one depth level** (230 KB), not the files' 36-level
blocks (8.3 MB).

## The viewer

The viewer is [gridlook](https://github.com/eeholmes/gridlook), published once for the whole
collection at [`pacioos/viewer/`](https://data.source.coop/ocean-icechunks/pacioos/viewer/index.html),
where the dataset picker lists every PacIOOS store. Both the store and the NetCDF copies are on
`data.source.coop`, which sends the CORS headers a browser needs. These links open each field:

{{viewer_fields_table}}

## Where the metadata came from

**The metadata were corrected; the data were not touched.** The files give `salt` no units and
have almost no global attributes. The store takes the variable and global attributes from
PacIOOS's own ERDDAP records,
[`roms_hiig`](https://pae-paha.pacioos.hawaii.edu/erddap/info/roms_hiig/index.html) and
[`roms_hiig_ssh`](https://pae-paha.pacioos.hawaii.edu/erddap/info/roms_hiig_ssh/index.html).
Its title ends ": Forecast" instead of ERDDAP's ": 3-D Variables", because `zeta` is in the same
group here. The fill value is the files' own, `9.99e10`.

## The time axis

The time axis equals the one PacIOOS's ERDDAP serves for `roms_hiig` (checked 2026-11-14). It
is regular: if no run ever covered a time, that step would read as `NaN` with
`forecast_reference_time` NaT. None does so far.

## Opening the store: notes

- **icechunk 1.x will not work.** Every icechunk 2.x release needs Python 3.12, so on an older
  Python `pip install icechunk` quietly installs 1.1.x, and the loading code fails with
  `AttributeError: module 'icechunk' has no attribute 'http_storage'`.
- **Why the loading code sets `authorize_virtual_chunk_access`.** The data stay in the NetCDF
  files, outside the store. The code allows anonymous reads of the locations the store names;
  they are in its saved config, so no URL is hard-coded.

## Performance: why reads cost what they do

Each chunk is **one depth level of one variable at one time step**: `(1, 1, 195, 295)`, 230 KB.
That shape is fixed by the files. The store points inside them and cannot rechunk them.

**Maps and profiles are cheap; long point series are not.** A time series at one point reads a
whole 230 KB plane at every step, because no chunk spans more than one time step. In the files,
the time steps of all variables are interleaved record by record, so no reference can join them.

## How the store was built and validated

- **Built** by `build_store.py` in
  [ocean-icechunks/pacioos](https://github.com/ocean-icechunks/pacioos/tree/main/stores/roms_hiig).
  It read every file's header (the files come in four header layouts, so offsets differ between
  files), confirmed that all share one structure, and wrote the series in one commit on
  2026-11-14: snapshot `W6C8C8NEFTSGB8DYXN30`, 5,497 steps, 797,065 references, 11 MB.
- **Validated** from the public URL, anonymously: the time axis equals the computed one and
  ERDDAP's; every step comes from the newest run that has it; sampled planes (one step per
  month, all 5 variables: 125 planes) are identical to netCDF-C reads of the files; 12 point
  values (temp, salt, zeta at 4 times) equal ERDDAP's; land reads as `NaN`.
- **Tested:** the loading code in the README was run as written, in a clean environment holding
  only the three packages it names (and their dependencies).
- **Build files** are published in this folder,
  [`pacioos/roms_hiig/docs/`](https://data.source.coop/ocean-icechunks/pacioos/roms_hiig/docs/);
  the shared modules they import (`pacioos_virtual.py`, `icechunk_utils.py`,
  `best_series_update.py`) and the shared `requirements.txt` are in the collection's
  [`pacioos/docs/`](https://data.source.coop/ocean-icechunks/pacioos/docs/). Install with
  `pip install -r requirements.txt` from this folder (it includes `../../docs/requirements.txt`).

## Updates

The store is brought up to date with `update_store.py`, which adds the steps of new runs and
re-points older steps to the newest run that has them, in one commit. Last update 2026-11-18:
runs through 2026-11-17, snapshot `XA93E152DH2YJ3KEZ3E0`, 5,537 steps through 2026-11-24T00Z.
It added 16 steps and re-pointed 41; anonymous validation confirmed all time coordinates against
the plan and 40 sampled planes against netCDF-C. Updates are run by hand until the daily update
(issue #4) is scheduled. Every update is a new Icechunk snapshot, so the series as it stood on an
earlier day stays readable.
