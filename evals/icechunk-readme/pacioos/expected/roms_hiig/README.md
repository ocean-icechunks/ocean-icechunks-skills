# PacIOOS ROMS Hawaiʻi forecast: Icechunk store, best time series

**[View data in browser](https://data.source.coop/ocean-icechunks/pacioos/viewer/index.html#icechunk+https://data.source.coop/ocean-icechunks/pacioos/roms_hiig/icechunk::varname=temp::px=0::py=0::alt=4000000::lat=20.5::lon=-158.2::dimIndices_time=0::dimIndices_depth=0)** · **[Data access (code)](#data-access-code)** · **[PacIOOS dataset page](https://www.pacioos.hawaii.edu/metadata/roms_hiig.html)** · **[How to cite](#citation-and-reuse)** · **[Documentation](https://source.coop/ocean-icechunks/pacioos/roms_hiig/docs/documentation.md)** · **[Metadata](https://source.coop/ocean-icechunks/pacioos/roms_hiig/docs/metadata.md)**

An [Icechunk](https://icechunk.io) store of the **PacIOOS Regional Ocean Modeling System (ROMS)
7-day forecast for the main Hawaiian Islands**. It is 3-hourly from 2025-01-01, at about 4 km
resolution, on 36 depth levels from 0.25 m to 5,500 m. A new run starts every day at 00Z, after
data assimilation (satellite SST and sea-surface height, HF-radar currents, Argo and glider
profiles). Its boundaries come from global HYCOM and its atmospheric forcing from the PacIOOS
WRF model.

```
https://data.source.coop/ocean-icechunks/pacioos/roms_hiig/icechunk
```

Updated 2026-11-19.

**It is the "best" time series, as PacIOOS's THREDDS and ERDDAP serve it.** The daily runs
overlap: each covers 7 days. The store has one time axis, and at each time it takes the newest
run that has it. So the past is a chain of each run's first day, and the last 7 days are the
newest run's forecast. Two coordinates on `time` say where each value came from:
`forecast_reference_time` (the run) and `forecast_period` (hours into it).

## Variables and coordinates

| Variable | Dimensions | Units | Standard name |
|---|---|---|---|
| `temp` | time, depth, lat, lon | Celsius | sea_water_potential_temperature |
| `salt` | time, depth, lat, lon | 1e-3 | sea_water_salinity |
| `u` | time, depth, lat, lon | meter second-1 | eastward_sea_water_velocity |
| `v` | time, depth, lat, lon | meter second-1 | northward_sea_water_velocity |
| `zeta` | time, lat, lon | meter | sea_surface_height |
| `mask` | lat, lon | | land/sea mask from the files (0 land, 1 water) |

| Coordinate | Size | Values |
|---|---|---|
| `time` | 5,545 (2026-11-19) | 2025-01-01T00Z to 7 days after the newest run, every 3 hours |
| `forecast_reference_time` | on `time` | the run each step comes from (NaT if no run covers it) |
| `forecast_period` | on `time` | hours since that run's start, 0 to 168 |
| `depth` | 36 | 0.25 to 5,500 m, positive down |
| `lat` | 195 | 17.02 to 23.98 °N |
| `lon` | 295 | −163.83 to −152.52 °E |

Land, and depths below the sea floor, read as `NaN`.

## Data access (code)

### Python

Needs **Python 3.12 or newer**, `icechunk >= 2.3`, `xarray` and `zarr`. No credentials and no
account.

```bash
pip install "icechunk>=2.3" xarray zarr
```

**Open the dataset in xarray**

```python
import icechunk
import numpy as np
import xarray as xr
import zarr

# Zarr's default of 10 concurrent reads is too low.
zarr.config.set({"async.concurrency": 128})


def open_forecast(ref="main", chunks=None):
    """Open the PacIOOS ROMS Hawaii forecast, best time series. `ref` is a branch or tag."""
    url = "https://data.source.coop/ocean-icechunks/pacioos/roms_hiig/icechunk"
    repo = icechunk.Repository.open(icechunk.http_storage(url))
    auth = {p: icechunk.credentials.HttpAccess for p in repo.config.virtual_chunk_containers or []}
    repo = repo.reopen(authorize_virtual_chunk_access=auth)
    tags = set(repo.list_tags())
    session = repo.readonly_session(tag=ref) if ref in tags else repo.readonly_session(ref)
    return xr.open_zarr(session.store, consolidated=False, chunks=chunks)


# Large Icechunk stores hold many chunk references. Open with chunks=None (the default),
# subset, then call .chunk() on the subset if the work uses dask.
ds = open_forecast()
print(ds)
```

**Subset, then chunk.** A large store holds many chunk references, and `chunks={}` makes one
dask task for each, which is slow. Open with `chunks=None`, select what you need, then call
`.chunk()` on the selection if the work uses dask. The last example below does this; it needs
`dask` (`pip install dask`).

**Example analyses**

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

## Performance

| Read | Chunks | Data moved | Time (measured) |
|---|---|---|---|
| One surface map | 1 | 230 KB | 0.2 s |
| One 3-D field, 36 levels | 36 | 8.3 MB | 0.8 s |
| Point series, one depth, 5,497 steps | 5,497 | 1.3 GB | 8.5 s |

Measured 2026-11-14 from a JupyterHub, with `zarr.config.set({"async.concurrency": 128})` and
`chunks=None`. Rates elsewhere will differ.

## Provenance

- **Source files:** PacIOOS's daily forecast files `hiig_forec_YYYYMMDD.nc` (NetCDF-3,
  uncompressed), copied unchanged from PacIOOS to Source Cooperative, each with an `.md5` beside
  it. 657 runs, 2025-01-01 to 2026-11-17 (2026-11-18); 29 days have no run, at most 3 in a row.
- **Built** 2026-11-14 by `build_store.py` in
  [ocean-icechunks/pacioos](https://github.com/ocean-icechunks/pacioos/tree/main/stores/roms_hiig).
  Last update 2026-11-19, snapshot `XDCVTP2XZ131GBWFFVD0`.
- **Tested with** icechunk 2.3.1, virtualizarr 2.8.0, xarray 2026.9.0, zarr 3.4.2, Python 3.12.
- **Build files** (in [`docs/`](https://data.source.coop/ocean-icechunks/pacioos/roms_hiig/docs/)): `requirements.txt`, `build_store.py`, `forecast_store.py`, `update_store.py`,
  the local smoke-test notebook `forecast-smoke-test-local.ipynb`, `erddap_metadata.json` and
  `how_store_created.md`.
- **How it was made, and how to rebuild it:**
  [`how_store_created.md`](https://github.com/ocean-icechunks/pacioos/blob/main/stores/roms_hiig/how_store_created.md).
  The plan and decisions are in [issue #10](https://github.com/ocean-icechunks/pacioos/issues/10).

## Citation and reuse

**The data are PacIOOS's.** Any use of this store or the NetCDF copies should cite PacIOOS, as
described at <https://www.pacioos.hawaii.edu/data-services/>. The model runs are produced by
Brian Powell (University of Hawaiʻi at Mānoa).

**The code** that copied the files and built the store was written by E. E. Holmes and is
released under the Apache License 2.0 at
[ocean-icechunks/pacioos](https://github.com/ocean-icechunks/pacioos). It can be used without
attribution.
