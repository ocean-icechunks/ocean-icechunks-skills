---
# A standalone product: noaa-oisst is its own Source Cooperative product, with no collection
# above it, so it carries the fields a collection would. Written by the icechunk-readme skill
# from the live store and the maintainers' repository (2026-11-23), as a proposal for
# ocean-icechunks/noaa_oisst; the maintainers decide whether to adopt it.
level: product
id: noaa-oisst
title: "NOAA OISST v2.1 daily sea surface temperature: Icechunk store"
source_coop:
  account: ocean-icechunks
  product: noaa-oisst
store_url: https://data.source.coop/ocean-icechunks/noaa-oisst/oisst.icechunk
repository: https://github.com/ocean-icechunks/noaa_oisst
provider:
  name: NOAA NCEI
  long_name: NOAA National Centers for Environmental Information
  url: https://www.ncei.noaa.gov
  data_services_url: https://www.ncei.noaa.gov/products/optimum-interpolation-sst
  data_services_label: Data access (NCEI)
  citation_url: https://doi.org/10.25921/RE9P-PT57
provider_page:
  label: Data access (AWS Open Data)
  url: https://registry.opendata.aws/noaa-cdr-oceanic/
viewer:
  name: Gridlook
  url: https://data.source.coop/ocean-icechunks/noaa-oisst/viewer/index.html
  group: daily
  variable: sst
  view: dimIndices_time=15828::dimIndices_zlev=0
  fields:
    - {label: Daily SST, variable: sst}
    - {label: Daily SST anomaly, variable: anom}
    - {label: Daily sea-ice concentration, variable: ice}
    - {label: Monthly mean SST, variable: sst_mean, group: monthly, view: dimIndices_time=520::dimIndices_zlev=0}
order:
  groups: [/daily, /monthly]
  variables: [sst, anom, err, ice]
  coordinates: [time, preliminary, zlev, lat, lon]
groups_note: >-
  `daily` holds NOAA's own files, referenced in place: one global field per day and variable.
  `monthly` is computed from the final daily fields and stored in the store itself, chunked for
  long time series at a point. A single group cannot hold both: one is virtual and chunked by
  day, the other is real data chunked by place.
coordinate_notes:
  daily/time: 1981-09-01 to a day or two ago, daily at 12:00 UTC
  monthly/time: first of each month, from 1981-09 to the last complete final month
  preliminary: true where NOAA has published only its preliminary file (the newest two weeks or so)
variable_notes:
  daily/ice: sea ice concentration, a fraction 0 to 1 despite the units attribute
code:
  python:
    python_version: "3.12"
    packages: [icechunk >= 2.3, xarray, zarr]
    pip: pip install "icechunk>=2.3" xarray zarr
    function: open_oisst
    docstring: Open one group of the NOAA OISST v2.1 store, daily or monthly. `ref` is a branch or tag.
    concurrency: 64
    dask_example: The last example below does this; it needs `dask` (`pip install dask`).
performance:
  rows:
    - {read: "Open `daily`, then `monthly`", chunks: "metadata", data_moved: not measured, time: 1.6 s and 1.7 s}
    - {read: "One day, global (`daily`)", chunks: 1, data_moved: not measured, time: 0.7 s}
    - {read: "31 days at a point (`daily`)", chunks: 31, data_moved: not measured, time: 0.2 s}
    - {read: "542 months at a point (`monthly`)", chunks: 23, data_moved: not measured, time: 0.8 s}
    - {read: "One month, global (`monthly`)", chunks: 128, data_moved: not measured, time: 1.1 s}
  measured: '2026-11-23 from a JupyterHub in AWS us-west-2 (NOAA''s bucket is in us-east-1), with `zarr.config.set({"async.concurrency": 64})` and `chunks=None`; the second of two runs'
provenance:
  built: 2026-08-28
  build_script: oisst
  build_url: https://github.com/ocean-icechunks/noaa_oisst/tree/main/src/ohw26_oisst_icechunk
  tested_with: icechunk 2.3.1, xarray 2026.9.0, zarr 3.4.2, dask 2026.8.0 (last example), Python 3.13
  how_made:
    file: docs/operations.md
    url: https://github.com/ocean-icechunks/noaa_oisst/blob/main/docs/operations.md
code_license:
  spdx: BSD-3-Clause
  author: Alex Kerney
  attribution_required: true
citation_extra: >-
  The DOI is for the Climate Data Record: Huang, B., C. Liu, V. Banzon, E. Freeman, G. Graham,
  W. Hankins, T. Smith and H.-M. Zhang (2020), NOAA 0.25-degree Daily Optimum Interpolation Sea
  Surface Temperature (OISST), Version 2.1, NOAA NCEI. The `monthly` statistics are derived from
  it by this project and are not a NOAA product. NOAA asks for attribution and does not allow a
  claim of endorsement by or affiliation with NOAA.
credits:
  - label: Data
    text: >-
      NOAA National Centers for Environmental Information, OISST v2.1 Climate Data Record, on AWS
      through the [NOAA Open Data Dissemination](https://www.noaa.gov/information-technology/open-data-dissemination)
      program.
  - label: Icechunk store and update pipeline
    text: >-
      [NERACOOS](https://neracoos.org) / [GMRI](https://gmri.org) (Alex Kerney), started at
      [OceanHackWeek 2026](https://oceanhackweek.org); built with
      [VirtualiZarr](https://virtualizarr.readthedocs.io), [Icechunk](https://icechunk.io) and
      [Xarray](https://xarray.dev), hosted on [Source Cooperative](https://source.coop/ocean-icechunks/noaa-oisst).
  - label: Tooling
    text: >-
      This README was generated with
      [ocean-icechunks-skills](https://github.com/ocean-icechunks/ocean-icechunks-skills), agent skills
      for building and documenting Icechunk stores, by Eli Holmes, Rich Signell and
      [other contributors](https://github.com/ocean-icechunks/ocean-icechunks-skills/graphs/contributors).
  - label: Viewer
    text: >-
      [gridlook](https://github.com/d70-t/gridlook), developed by Andrej Fast, Tobi Kölling, Fabian
      Wachsmann and contributors at DKRZ and the Max Planck Institute for Meteorology. The copy
      published at `noaa-oisst/viewer/` is built from a fork, [eeholmes/gridlook](https://github.com/eeholmes/gridlook).
---

# README

## Summary

An [Icechunk](https://icechunk.io) store of **NOAA's 1/4° Daily Optimum Interpolation Sea Surface
Temperature (OISST) v2.1** Climate Data Record: SST, SST anomaly, analysis error and sea-ice
concentration on a global 0.25° grid, every day from 1981-09-01 to a day or two ago, with
monthly statistics beside it. [NERACOOS](https://neracoos.org) / [GMRI](https://gmri.org) build
it and keep it current with a scheduled run.

## Notes

**Preliminary and final days.** NOAA publishes a preliminary file a day or two after each date
and replaces it with a final file about two weeks later. The store does the same: a final file
replaces the preliminary one in place, and the `preliminary` coordinate says which days are
still preliminary. `monthly` is computed from final days only.

## Variable notes

Times in `daily` are 12:00 UTC, the middle of each day, so select by date (`sel(time="2024-07-04")`)
rather than by midnight. Longitude runs 0 to 360, so 69.5°W is `lon=290.5`. Every variable has
a length-1 `zlev` dimension (0 m); `.squeeze()` drops it. Land is NaN.

## Example analyses

```python
# One day, global (daily: one chunk per variable and day).
daily = open_oisst("daily")
sst = daily.sst.sel(time="2024-07-04").squeeze().load()
print(float(sst.mean()))

# 45 years of monthly means at one point (monthly: chunked for this).
monthly = open_oisst("monthly")
series = monthly.sst_mean.sel(lat=43.5, lon=290.5, method="nearest").squeeze().load()
print(series.sizes, float(series.max()))

# Final days only: drop the newest, still-preliminary ones.
final = daily.isel(time=~daily.preliminary.values)

# A month of daily fields over the Gulf of Maine, then dask on the subset.
gom = daily.sst.sel(time="2024-07", lat=slice(40, 46), lon=slice(288, 296)).squeeze().chunk({"time": 7})
print(gom.mean("time").compute().shape)
```

## Source files

NOAA's daily NetCDF-4 files in the [NOAA Climate Data Record bucket](https://registry.opendata.aws/noaa-cdr-oceanic/)
on AWS, `s3://noaa-cdr-sea-surface-temp-optimum-interpolation-pds/data/v2.1/avhrr/`, one folder
per month (`YYYYMM/oisst-avhrr-v02r01.YYYYMMDD.nc`, with `_preliminary` before the final file
exists). They are read in place, anonymously; nothing is copied.

## Caveats

NOAA deletes a preliminary file when it publishes the final one. Until the store's next update
swaps in the final file, a read of that day fails; read again later, or use final days only.

# Documentation

## A virtual store

The `daily` group holds no data: Icechunk keeps Zarr metadata and byte-range references to
NOAA's files, and every read of a daily value goes to NOAA's bucket in us-east-1. Its chunks are
NOAA's own, one global field per day and variable, `int16` with `scale_factor` 0.01, shuffle
and zlib. The references are `s3://` URLs, so the loader authorizes them with anonymous S3
credentials rather than `HttpAccess`.

The `monthly` group is ordinary Zarr data in the store: the minimum, maximum, mean and standard
deviation of each daily variable for every complete, all-final month, `int16` chunked
`(24, 1, 90, 90)` and compressed with Blosc/zstd. It has its own metadata: names like
`sst_mean`, a `cell_methods` entry, and group attributes that say it is not a NOAA product.

## Which group to use

`daily` is the group for maps, single days and short windows. A long series at one point reads
one whole global field per day from it, 16,000 or more, so use `monthly` for that: 24 months
of a 90 × 90 tile per chunk.

## The viewer

The [viewer](https://data.source.coop/ocean-icechunks/noaa-oisst/viewer/index.html) is gridlook,
published beside the store. Both hosts it reads from, Source Cooperative and NOAA's bucket, send
`Access-Control-Allow-Origin: *`, so it needs no workaround. Its links open at fixed dates (a
link cannot say "the latest day"); the time slider, the other variables and the other group are
controls in the viewer.

{{viewer_fields_table}}

## How the store is built and updated

The store is built and kept current by the maintainers' `oisst` command, in
[ocean-icechunks/noaa_oisst](https://github.com/ocean-icechunks/noaa_oisst). A scheduled GitHub
Actions run (four times a day, per its
[operations runbook](https://github.com/ocean-icechunks/noaa_oisst/blob/main/docs/operations.md))
appends new preliminary days, swaps in final files as NOAA publishes them, and adds a month to
`monthly` once all of its days are final. Every run reads the store's state and does only the
missing work, so a skipped run is caught up by the next. Why the groups are chunked as they are
is in [chunking.md](https://github.com/ocean-icechunks/noaa_oisst/blob/main/docs/chunking.md).

The store's history is its log, from "Repository initialized" on 2026-08-28:

```python
for snapshot in repo.ancestry(branch="main"):
    print(snapshot.written_at, snapshot.message)
```

## What was changed from the source

Nothing in NOAA's daily arrays or their attributes. The store adds the `preliminary` coordinate
and the `monthly` group. The `daily` group's attributes are NOAA's, from the most recent file.
