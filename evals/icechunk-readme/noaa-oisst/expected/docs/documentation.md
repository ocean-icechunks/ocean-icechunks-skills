# NOAA OISST v2.1 daily sea surface temperature: documentation

Technical detail for the [`noaa-oisst` Icechunk store](https://source.coop/ocean-icechunks/noaa-oisst). The README has what most readers need; this page has the rest.

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

## Source file format

| Format | Files checked | First | Last |
|---|---|---|---|
| NetCDF-4 (HDF5) | 40 | `https://noaa-cdr-sea-surface-temp-optimum-interpolation-pds.s3.us-east-1.amazonaws.com/data/v2.1/avhrr/198109/oisst-avhrr-v02r01.19810901.nc` | `https://noaa-cdr-sea-surface-temp-optimum-interpolation-pds.s3.us-east-1.amazonaws.com/data/v2.1/avhrr/202611/oisst-avhrr-v02r01.20261116_preliminary.nc` |

Read from the first bytes of the first and last file in each of 543 folders, 40 of them spread evenly, 40 of 16,513 files.

NetCDF-4 files are HDF5 files. Their variables may be chunked and compressed; a compressed chunk can only be read whole, so the files' chunking sets the smallest read.

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

| Field | Viewer |
|---|---|
| Daily SST | [Open `sst`](https://data.source.coop/ocean-icechunks/noaa-oisst/viewer/index.html#icechunk+https://data.source.coop/ocean-icechunks/noaa-oisst/oisst.icechunk/daily::varname=sst::dimIndices_time=15828::dimIndices_zlev=0) |
| Daily SST anomaly | [Open `anom`](https://data.source.coop/ocean-icechunks/noaa-oisst/viewer/index.html#icechunk+https://data.source.coop/ocean-icechunks/noaa-oisst/oisst.icechunk/daily::varname=anom::dimIndices_time=15828::dimIndices_zlev=0) |
| Daily sea-ice concentration | [Open `ice`](https://data.source.coop/ocean-icechunks/noaa-oisst/viewer/index.html#icechunk+https://data.source.coop/ocean-icechunks/noaa-oisst/oisst.icechunk/daily::varname=ice::dimIndices_time=15828::dimIndices_zlev=0) |
| Monthly mean SST | [Open `sst_mean`](https://data.source.coop/ocean-icechunks/noaa-oisst/viewer/index.html#icechunk+https://data.source.coop/ocean-icechunks/noaa-oisst/oisst.icechunk/monthly::varname=sst_mean::dimIndices_time=520::dimIndices_zlev=0) |

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
