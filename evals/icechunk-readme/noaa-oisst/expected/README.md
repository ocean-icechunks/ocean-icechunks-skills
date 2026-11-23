# NOAA OISST v2.1 daily sea surface temperature: Icechunk store

**[View data in browser](https://data.source.coop/ocean-icechunks/noaa-oisst/viewer/index.html#icechunk+https://data.source.coop/ocean-icechunks/noaa-oisst/oisst.icechunk/daily::varname=sst::dimIndices_time=15828::dimIndices_zlev=0)** · **[Data access (code)](#data-access-code)** · **[Data access (NCEI)](https://www.ncei.noaa.gov/products/optimum-interpolation-sst)** · **[Data access (AWS Open Data)](https://registry.opendata.aws/noaa-cdr-oceanic/)** · **[How to cite](#citation-and-reuse)** · **[Documentation](https://source.coop/ocean-icechunks/noaa-oisst/docs/documentation.md)** · **[Metadata](https://source.coop/ocean-icechunks/noaa-oisst/docs/metadata.md)**

An [Icechunk](https://icechunk.io) store of **NOAA's 1/4° Daily Optimum Interpolation Sea Surface
Temperature (OISST) v2.1** Climate Data Record: SST, SST anomaly, analysis error and sea-ice
concentration on a global 0.25° grid, every day from 1981-09-01 to a day or two ago, with
monthly statistics beside it. [NERACOOS](https://neracoos.org) / [GMRI](https://gmri.org) build
it and keep it current with a scheduled run.

```
https://data.source.coop/ocean-icechunks/noaa-oisst/oisst.icechunk
```

Updated 2026-11-18. **NetCDF:** `https://noaa-cdr-sea-surface-temp-optimum-interpolation-pds.s3.us-east-1.amazonaws.com/data/v2.1/avhrr/`, 16,513 files.

**Preliminary and final days.** NOAA publishes a preliminary file a day or two after each date
and replaces it with a final file about two weeks later. The store does the same: a final file
replaces the preliminary one in place, and the `preliminary` coordinate says which days are
still preliminary. `monthly` is computed from final days only.

## Variables and coordinates

`daily` holds NOAA's own files, referenced in place: one global field per day and variable. `monthly` is computed from the final daily fields and stored in the store itself, chunked for long time series at a point. A single group cannot hold both: one is virtual and chunked by day, the other is real data chunked by place.

### Group `/daily`

| Variable | Dimensions | Units | Standard name |
|---|---|---|---|
| `sst` | time, zlev, lat, lon | Celsius | Daily sea surface temperature |
| `anom` | time, zlev, lat, lon | Celsius | Daily sea surface temperature anomalies |
| `err` | time, zlev, lat, lon | Celsius | Estimated error standard deviation of analysed_sst |
| `ice` | time, zlev, lat, lon | % | sea ice concentration, a fraction 0 to 1 despite the units attribute |

| Coordinate | Size | Values |
|---|---|---|
| `time` | 16,513 (2026-11-18) | 1981-09-01 to a day or two ago, daily at 12:00 UTC |
| `preliminary` | on `time` | true where NOAA has published only its preliminary file (the newest two weeks or so) |
| `zlev` | 1 | 0 meters |
| `lat` | 720 | −89.88 to 89.88 °N |
| `lon` | 1,440 | 0.12 to 359.88 °E |

### Group `/monthly`

| Variable | Dimensions | Units | Standard name |
|---|---|---|---|
| `anom_max` | time, zlev, lat, lon | Celsius | Monthly maximum of daily sea surface temperature anomaly |
| `anom_mean` | time, zlev, lat, lon | Celsius | Monthly mean of daily sea surface temperature anomaly |
| `anom_min` | time, zlev, lat, lon | Celsius | Monthly minimum of daily sea surface temperature anomaly |
| `anom_std` | time, zlev, lat, lon | Celsius | Monthly standard deviation of daily sea surface temperature anomaly |
| `err_max` | time, zlev, lat, lon | Celsius | Monthly maximum of daily estimated error standard deviation of sea surface temperature |
| `err_mean` | time, zlev, lat, lon | Celsius | Monthly mean of daily estimated error standard deviation of sea surface temperature |
| `err_min` | time, zlev, lat, lon | Celsius | Monthly minimum of daily estimated error standard deviation of sea surface temperature |
| `err_std` | time, zlev, lat, lon | Celsius | Monthly standard deviation of daily estimated error standard deviation of sea surface temperature |
| `ice_max` | time, zlev, lat, lon | 1 | Monthly maximum of daily sea ice concentration |
| `ice_mean` | time, zlev, lat, lon | 1 | Monthly mean of daily sea ice concentration |
| `ice_min` | time, zlev, lat, lon | 1 | Monthly minimum of daily sea ice concentration |
| `ice_std` | time, zlev, lat, lon | 1 | Monthly standard deviation of daily sea ice concentration |
| `sst_max` | time, zlev, lat, lon | Celsius | Monthly maximum of daily sea surface temperature |
| `sst_mean` | time, zlev, lat, lon | Celsius | Monthly mean of daily sea surface temperature |
| `sst_min` | time, zlev, lat, lon | Celsius | Monthly minimum of daily sea surface temperature |
| `sst_std` | time, zlev, lat, lon | Celsius | Monthly standard deviation of daily sea surface temperature |

| Coordinate | Size | Values |
|---|---|---|
| `time` | 542 (2026-11-18) | first of each month, from 1981-09 to the last complete final month |
| `zlev` | 1 | 0 meters |
| `lat` | 720 | −89.88 to 89.88 °N |
| `lon` | 1,440 | 0.12 to 359.88 °E |

Times in `daily` are 12:00 UTC, the middle of each day, so select by date (`sel(time="2024-07-04")`)
rather than by midnight. Longitude runs 0 to 360, so 69.5°W is `lon=290.5`. Every variable has
a length-1 `zlev` dimension (0 m); `.squeeze()` drops it. Land is NaN.

## Data access (code)

### Python

Needs **Python 3.12 or newer**, `icechunk >= 2.3`, `xarray` and `zarr`. No credentials and no account.

```bash
pip install "icechunk>=2.3" xarray zarr
```

**Open the dataset in xarray**

```python
import icechunk
import xarray as xr
import zarr

# Zarr's default of 10 concurrent reads is too low.
zarr.config.set({"async.concurrency": 64})


def open_oisst(group="daily", ref="main", chunks=None):
    """Open one group of the NOAA OISST v2.1 store, daily or monthly. `ref` is a branch or tag."""
    url = "https://data.source.coop/ocean-icechunks/noaa-oisst/oisst.icechunk"
    repo = icechunk.Repository.open(icechunk.http_storage(url))
    auth = icechunk.containers_credentials({
        p: icechunk.s3_anonymous_credentials() if p.startswith("s3://") else icechunk.credentials.HttpAccess
        for p in repo.config.virtual_chunk_containers})
    repo = repo.reopen(authorize_virtual_chunk_access=auth)
    tags = set(repo.list_tags())
    session = repo.readonly_session(tag=ref) if ref in tags else repo.readonly_session(ref)
    return xr.open_zarr(session.store, consolidated=False, chunks=chunks, group=group)


# Large Icechunk stores hold many chunk references. Open with chunks=None (the default),
# subset, then call .chunk() on the subset if the work uses dask.
ds = open_oisst()
print(ds)
```

**Subset, then chunk.** A large store holds many chunk references, and `chunks={}` makes one dask task for each, which is slow. Open with `chunks=None`, select what you need, then call `.chunk()` on the selection if the work uses dask. The last example below does this; it needs `dask` (`pip install dask`).

**Example analyses**

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

## Performance

| Read | Chunks | Data moved | Time (measured) |
|---|---|---|---|
| Open `daily`, then `monthly` | metadata | not measured | 1.6 s and 1.7 s |
| One day, global (`daily`) | 1 | not measured | 0.7 s |
| 31 days at a point (`daily`) | 31 | not measured | 0.2 s |
| 542 months at a point (`monthly`) | 23 | not measured | 0.8 s |
| One month, global (`monthly`) | 128 | not measured | 1.1 s |

Measured 2026-11-23 from a JupyterHub in AWS us-west-2 (NOAA's bucket is in us-east-1), with `zarr.config.set({"async.concurrency": 64})` and `chunks=None`; the second of two runs. Rates elsewhere will differ.

## Provenance

- **Source files:** NOAA's daily NetCDF-4 files in the [NOAA Climate Data Record bucket](https://registry.opendata.aws/noaa-cdr-oceanic/)
  on AWS, `s3://noaa-cdr-sea-surface-temp-optimum-interpolation-pds/data/v2.1/avhrr/`, one folder
  per month (`YYYYMM/oisst-avhrr-v02r01.YYYYMMDD.nc`, with `_preliminary` before the final file
  exists). They are read in place, anonymously; nothing is copied.
- **Built** 2026-08-28 by `oisst` in [ocean-icechunks/noaa_oisst](https://github.com/ocean-icechunks/noaa_oisst/tree/main/src/ohw26_oisst_icechunk). Last update 2026-11-18, snapshot `Z0RZCMCJM9TMVS2ECABG`.
- **Tested with** icechunk 2.3.1, xarray 2026.9.0, zarr 3.4.2, dask 2026.8.0 (last example), Python 3.13.
- **How it was made, and how to rebuild it:** [`docs/operations.md`](https://github.com/ocean-icechunks/noaa_oisst/blob/main/docs/operations.md).

## Caveats

NOAA deletes a preliminary file when it publishes the final one. Until the store's next update
swaps in the final file, a read of that day fails; read again later, or use final days only.

## Citation and reuse

**The data are NOAA NCEI's.** Any use of this store or its source files should cite NOAA NCEI, as described at <https://doi.org/10.25921/RE9P-PT57>. The DOI is for the Climate Data Record: Huang, B., C. Liu, V. Banzon, E. Freeman, G. Graham, W. Hankins, T. Smith and H.-M. Zhang (2020), NOAA 0.25-degree Daily Optimum Interpolation Sea Surface Temperature (OISST), Version 2.1, NOAA NCEI. The `monthly` statistics are derived from it by this project and are not a NOAA product. NOAA asks for attribution and does not allow a claim of endorsement by or affiliation with NOAA.

**The code** that built the store was written by Alex Kerney and is released under the BSD 3-Clause License at [ocean-icechunks/noaa_oisst](https://github.com/ocean-icechunks/noaa_oisst). Please credit Alex Kerney when reusing it.

## Credits

- **Data:** NOAA National Centers for Environmental Information, OISST v2.1 Climate Data Record, on AWS through the [NOAA Open Data Dissemination](https://www.noaa.gov/information-technology/open-data-dissemination) program.
- **Icechunk store and update pipeline:** [NERACOOS](https://neracoos.org) / [GMRI](https://gmri.org) (Alex Kerney), started at [OceanHackWeek 2026](https://oceanhackweek.org); built with [VirtualiZarr](https://virtualizarr.readthedocs.io), [Icechunk](https://icechunk.io) and [Xarray](https://xarray.dev), hosted on [Source Cooperative](https://source.coop/ocean-icechunks/noaa-oisst).
- **Tooling:** This README was generated with [ocean-icechunks-skills](https://github.com/ocean-icechunks/ocean-icechunks-skills), agent skills for building and documenting Icechunk stores, by Eli Holmes, Rich Signell and [other contributors](https://github.com/ocean-icechunks/ocean-icechunks-skills/graphs/contributors).
- **Viewer:** [gridlook](https://github.com/d70-t/gridlook), developed by Andrej Fast, Tobi Kölling, Fabian Wachsmann and contributors at DKRZ and the Max Planck Institute for Meteorology. The copy published at `noaa-oisst/viewer/` is built from a fork, [eeholmes/gridlook](https://github.com/eeholmes/gridlook).
