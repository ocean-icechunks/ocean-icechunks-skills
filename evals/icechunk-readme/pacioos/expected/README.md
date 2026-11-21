# PacIOOS Hawaiʻi ocean, wave and weather models

**[View data in browser](#data-access)** · **[Data access (code)](#data-access)** · **[Data access (PacIOOS)](https://www.pacioos.hawaii.edu/data-services/)** · **[Documentation](https://source.coop/ocean-icechunks/pacioos/docs/documentation.md)**

Model output from the [Pacific Islands Ocean Observing System (PacIOOS)](https://www.pacioos.hawaii.edu)
for the main Hawaiian Islands.

| Dataset (PacIOOS id) | About | Time coverage | Data |
|---|---|---|---|
| **ROMS ocean reanalysis v2.0** (`roms_hiig_reanalysis`), 3-hourly, ~4 km, 36 depths | [README](https://source.coop/ocean-icechunks/pacioos/roms_hiig_reanalysis/README.md) | 2009-01-01 to 2020-12-28 | **NetCDF:** `roms_hiig_reanalysis/netcdf/v2.0/`, 4,380 files, 1.17 TB<br>**Icechunk:** `https://data.source.coop/ocean-icechunks/pacioos/roms_hiig_reanalysis/icechunk`<br>Updated 2026-11-14 |
| **ROMS ocean forecast** (`roms_hiig`), daily runs | [README](https://source.coop/ocean-icechunks/pacioos/roms_hiig/README.md) | 2025-01-01 to 2026-11-25 | **NetCDF:** `roms_hiig/netcdf/`, 657 files, 1.25 TB<br>**Icechunk:** `https://data.source.coop/ocean-icechunks/pacioos/roms_hiig/icechunk`, best time series<br>Updated 2026-11-19 |
| **WRF weather model** (`wrf_hi`), daily runs | [README](https://source.coop/ocean-icechunks/pacioos/wrf_hi/README.md) | 2017-08-16 to 2026-11-22 | **NetCDF:** `wrf_hi/netcdf/`, 3,041 files, 0.46 TB<br>**Icechunk:** `https://data.source.coop/ocean-icechunks/pacioos/wrf_hi/icechunk`, hourly best time series<br>Updated 2026-11-18 |
| **WaveWatch III waves** (`ww3_hawaii`), daily runs | [README](https://source.coop/ocean-icechunks/pacioos/ww3_hawaii/README.md) | 2011-06-21 to 2026-11-25 | **NetCDF:** `ww3_hawaii/netcdf/`, 5,237 files, 0.49 TB<br>**Icechunk:** `https://data.source.coop/ocean-icechunks/pacioos/ww3_hawaii/icechunk`, best time series, hourly, with flags on cold starts<br>Updated 2026-11-19 |

## Data access

| Dataset | Store | Data files | Viewer | Code |
|---|---|---|---|---|
| ROMS reanalysis v2.0 | [icechunk](https://source.coop/ocean-icechunks/pacioos/roms_hiig_reanalysis/icechunk) | [netcdf](https://source.coop/ocean-icechunks/pacioos/roms_hiig_reanalysis/netcdf/v2.0) | [Gridlook](https://data.source.coop/ocean-icechunks/pacioos/viewer/index.html#icechunk+https://data.source.coop/ocean-icechunks/pacioos/roms_hiig_reanalysis/icechunk::varname=temp::px=0::py=0::alt=4000000::lat=20.5::lon=-158.2::dimIndices_time=0::dimIndices_depth=0) | [Python](https://source.coop/ocean-icechunks/pacioos/roms_hiig_reanalysis/README.md#user-content-python) |
| ROMS forecast, best time series | [icechunk](https://source.coop/ocean-icechunks/pacioos/roms_hiig/icechunk) | [netcdf](https://source.coop/ocean-icechunks/pacioos/roms_hiig/netcdf) | [Gridlook](https://data.source.coop/ocean-icechunks/pacioos/viewer/index.html#icechunk+https://data.source.coop/ocean-icechunks/pacioos/roms_hiig/icechunk::varname=temp::px=0::py=0::alt=4000000::lat=20.5::lon=-158.2::dimIndices_time=0::dimIndices_depth=0) | [Python](https://source.coop/ocean-icechunks/pacioos/roms_hiig/README.md#user-content-python) |
| WRF forecast, best time series | [icechunk](https://source.coop/ocean-icechunks/pacioos/wrf_hi/icechunk) | [netcdf](https://source.coop/ocean-icechunks/pacioos/wrf_hi/netcdf) | [Gridlook](https://data.source.coop/ocean-icechunks/pacioos/viewer/index.html#icechunk+https://data.source.coop/ocean-icechunks/pacioos/wrf_hi/icechunk::varname=Tair::px=0::py=0::alt=4000000::lat=20.5::lon=-158.2::dimIndices_time=0) | [Python](https://source.coop/ocean-icechunks/pacioos/wrf_hi/README.md#user-content-python) |
| WaveWatch III, best time series | [icechunk](https://source.coop/ocean-icechunks/pacioos/ww3_hawaii/icechunk) | [netcdf](https://source.coop/ocean-icechunks/pacioos/ww3_hawaii/netcdf) | [Gridlook](https://data.source.coop/ocean-icechunks/pacioos/viewer/index.html#icechunk+https://data.source.coop/ocean-icechunks/pacioos/ww3_hawaii/icechunk::varname=Thgt::px=0::py=0::alt=4000000::lat=20.5::lon=-158.2::dimIndices_time=0) | [Python](https://source.coop/ocean-icechunks/pacioos/ww3_hawaii/README.md#user-content-python) |

## Citation and reuse

**The data are PacIOOS's.** Any use of the NetCDF copies or the Icechunk stores should cite
PacIOOS, as described at <https://www.pacioos.hawaii.edu/data-services/>.

**The code** that copied the files and built the stores was written by E. E. Holmes and is
released under the Apache License 2.0 at
[ocean-icechunks/pacioos](https://github.com/ocean-icechunks/pacioos). It can be used without
attribution.

## Credits

- **Data:** PacIOOS, University of Hawaiʻi at Mānoa. ROMS ocean model: Brian S. Powell. WRF
  weather model: Yi-Leng Chen. WaveWatch III wave model: Kwok Fai Cheung.
- **Icechunk packaging:** built with [Icechunk](https://icechunk.io),
  [VirtualiZarr](https://virtualizarr.readthedocs.io) and [Xarray](https://xarray.dev), hosted
  on [Source Cooperative](https://source.coop/ocean-icechunks/pacioos).
- **Tooling:** [ocean-icechunks-skills](https://github.com/ocean-icechunks/ocean-icechunks-skills), agent
  skills for building and documenting Icechunk stores, by Eli Holmes, Rich Signell and
  [other contributors](https://github.com/ocean-icechunks/ocean-icechunks-skills/graphs/contributors).
- **Viewer:** [gridlook](https://github.com/d70-t/gridlook), developed by Andrej Fast, Tobi
  Kölling, Fabian Wachsmann and contributors at DKRZ and the Max Planck Institute for
  Meteorology. The copy published at `pacioos/viewer/` is built from a fork,
  [eeholmes/gridlook](https://github.com/eeholmes/gridlook).
