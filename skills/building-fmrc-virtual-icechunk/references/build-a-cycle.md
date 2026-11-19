# Build one run as `(time, step)`, then create and append

Two source layouts. Open every file with `loadable_variables=[<time variable>]`
so valid times are read as values; the code below needs them to compute `step`.

## A. One file per run (for example daily SHYFEM files)

Each file's `time` holds the run's valid times. Reshape each file, then
concatenate along the new `time` dimension.

```python
def fix_ds(ds):
    """(time) valid times -> scalar time (reference) + step (lead time)."""
    t0 = pd.Timestamp(ds.time.values[0])
    # snap to the exact grid: float round-off otherwise gives every run slightly
    # different step values, and the concat or append then fails
    ds = ds.assign_coords(time=pd.date_range(t0, periods=len(ds.time), freq="1h"))
    ds = ds.rename_vars(time="valid_time").rename_dims(time="step")
    step = (ds.valid_time - ds.valid_time[0]).assign_attrs({"standard_name": "forecast_period"})
    time = ds.valid_time[0].assign_attrs({"standard_name": "forecast_reference_time"})
    ds = ds.assign_coords(step=step, time=time)
    return ds.drop_indexes("valid_time").drop_vars("valid_time")
```

Set the frequency to the model's real output interval. Check two consecutive
raw values before hard-coding `"1h"`.

Concatenating along a scalar `time` stacks the static variables unless you keep
them out (see "Rules that bite" in `SKILL.md`):

```python
def cat(ds_list, static_from_first=True):
    dyn = [v for v in ds_list[0].data_vars if "step" in ds_list[0][v].dims]
    out = xr.concat([d[dyn] for d in ds_list], dim="time", coords="minimal",
                    compat="override", combine_attrs="override")
    if static_from_first:
        static = [v for v in ds_list[0].data_vars if v not in dyn]
        out = out.assign(ds_list[0].drop_vars("time")[static].variables)
    return out
```

Pass `static_from_first=False` when appending, so the batch contains only the
`(time, step, ...)` variables. If a run is split over several files by variable
group (for example `nos` and `ous`), build each group this way and combine with
`xr.merge([a, b], compat="override")`.

Checked: three synthetic daily files gave `temp (time: 3, step: 5, node: 4)` with
one chunk per run, the static variable stayed `(node)`, and a value matched the
source file.

## B. Many files per run (for example NOAA GoMOFS, one time step per file)

Join a run's files along their valid-time dimension, then reshape.

```python
TIME_DIM = "ocean_time"

def open_cycle(cycle, files):          # files: [(lead_hours, key)] sorted by lead
    with ThreadPoolExecutor(16) as pool:
        parts = list(pool.map(open_file, [key for _, key in files]))
    parts.sort(key=lambda d: d[TIME_DIM].values[0])
    ds = xr.concat(parts, dim=TIME_DIM, data_vars="minimal", coords="minimal",
                   compat="override", combine_attrs="override")

    # file names and file contents must agree, or the step axis would lie
    valid = pd.DatetimeIndex(ds[TIME_DIM].values)
    ref = pd.Timestamp(cycle)
    assert (valid == [ref + pd.Timedelta(hours=lead) for lead, _ in files]).all()

    ds = ds.rename_dims({TIME_DIM: "step"}).drop_vars(TIME_DIM)
    ds = ds.assign_coords(step=("step", (valid - ref).values, {"standard_name": "forecast_period"}))

    # time goes only on variables that vary with step; grid, mask and parameters stay static
    varying = [v for v in ds.data_vars if "step" in ds[v].dims]
    static = ds.drop_vars(varying)
    ds = xr.merge([ds[varying].expand_dims(time=[np.datetime64(ref)]), static],
                  compat="override", combine_attrs="override")
    ds["time"].attrs.update(standard_name="forecast_reference_time")
    ds["time"].encoding = {"units": "hours since 2024-01-01", "dtype": "int64"}
    ds["step"].encoding = {"units": "hours", "dtype": "int64"}
    return ds
```

Here the concat is along a real dimension, so `data_vars="minimal"` does keep the
static variables unstacked. The `time` axis is added afterwards, only to the
varying variables.

Which files to include is a source decision. GoMOFS names a cycle's files
`n003` (valid 3 h before the cycle time), `n006` (valid at it, lead 0) and
`f003` to `f072`. For a best estimate keep `n006` and `f003` to `f072`; a run
that starts at lead 0 gives 25 steps.

## Create, then append

```python
def for_append(ds, dim):
    return ds.drop_vars([v for v in ds.variables if dim not in ds[v].dims])

def commit_cycle(repo, cycle, ds, append):
    session = repo.writable_session("main")
    if append:
        for_append(ds, "time").vz.to_icechunk(session.store, append_dim="time")
    else:
        ds.vz.to_icechunk(session.store)
    session.commit(f"cycle {cycle:%Y-%m-%d %Hz}")
```

Use `.vz`, not the deprecated `.virtualize` accessor, and one commit per run or
small batch. The store must have been created with the virtual chunk container
for the source bucket (see `virtual-icechunk`).

## Updating: diff on reference time

```python
ds = xr.open_zarr(repo.readonly_session("main").store, consolidated=False, chunks={})
in_store = set(pd.to_datetime(ds.time.values))
new = sorted(set(runs_in_source) - in_store)      # keyed the same way: by reference time
```

Key the source runs by reference time too. If a path carries a date that differs
from the reference time, apply the offset in one place and comment on it.
Appending only works in increasing `time` order, so sort first. Report runs you
skipped as incomplete.

## Checked end to end

The GoMOFS pattern ran on NOAA's public `noaa-nos-ofs-pds` bucket: two 00Z cycles
(24 forecast files each) created and appended, a `zeta` value matched the source
file, and the store was 224 kB pointing at 48 files. The notebook is
`gomofs-fmrc-icechunk.ipynb` in the `notebooks/` folder of the
`ocean-icechunks/2026-ioos-hackathon` repository. That run used the 24 forecast
files per cycle; the version that adds `n006` (25 steps, lead 0 to 72 h) had its
file-selection step checked but had not been run end to end when this was written.
