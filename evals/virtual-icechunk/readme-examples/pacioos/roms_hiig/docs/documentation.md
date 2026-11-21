# PacIOOS ROMS Hawaiʻi forecast: documentation

Technical detail for the [`roms_hiig` Icechunk store](https://source.coop/ocean-icechunks/pacioos/roms_hiig).
The README has what most readers need; this page has the rest.

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

| Field | Viewer |
|---|---|
| Potential temperature | [Open `temp`](https://data.source.coop/ocean-icechunks/pacioos/viewer/index.html#icechunk+https://data.source.coop/ocean-icechunks/pacioos/roms_hiig/icechunk::varname=temp::px=0::py=0::alt=4000000::lat=20.5::lon=-158.2::dimIndices_time=0::dimIndices_depth=0) |
| Salinity | [Open `salt`](https://data.source.coop/ocean-icechunks/pacioos/viewer/index.html#icechunk+https://data.source.coop/ocean-icechunks/pacioos/roms_hiig/icechunk::varname=salt::px=0::py=0::alt=4000000::lat=20.5::lon=-158.2::dimIndices_time=0::dimIndices_depth=0) |
| Eastward current | [Open `u`](https://data.source.coop/ocean-icechunks/pacioos/viewer/index.html#icechunk+https://data.source.coop/ocean-icechunks/pacioos/roms_hiig/icechunk::varname=u::px=0::py=0::alt=4000000::lat=20.5::lon=-158.2::dimIndices_time=0::dimIndices_depth=0) |
| Northward current | [Open `v`](https://data.source.coop/ocean-icechunks/pacioos/viewer/index.html#icechunk+https://data.source.coop/ocean-icechunks/pacioos/roms_hiig/icechunk::varname=v::px=0::py=0::alt=4000000::lat=20.5::lon=-158.2::dimIndices_time=0::dimIndices_depth=0) |
| Sea-surface height | [Open `zeta`](https://data.source.coop/ocean-icechunks/pacioos/viewer/index.html#icechunk+https://data.source.coop/ocean-icechunks/pacioos/roms_hiig/icechunk::varname=zeta::px=0::py=0::alt=4000000::lat=20.5::lon=-158.2::dimIndices_time=0) |

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
