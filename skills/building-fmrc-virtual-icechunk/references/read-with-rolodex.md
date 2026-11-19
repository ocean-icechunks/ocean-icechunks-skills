# Read a run collection with Rolodex

[Rolodex](https://github.com/dcherian/rolodex) adds an xarray index over `time`,
`step` and a lazy `valid_time`, so you can ask for views of the collection. It
is not on PyPI; install it from GitHub and pin a commit:

```
pip install "git+https://github.com/dcherian/rolodex@527bd420b21e9efd88cb1601e58276d24312d040"
```

That is the commit the tutorial notebooks and the MAGICA school environment were
run with. Check the repository for a newer one before pinning something else.

## Build the index

```python
import rolodex.forecast
from rolodex.forecast import BestEstimate, ForecastIndex

ds = xr.open_zarr(repo.readonly_session("main").store, consolidated=False, chunks={})
ds.coords["valid_time"] = rolodex.forecast.create_lazy_valid_time_variable(
    reference_time=ds.time, period=ds.step)
fmrc = ds.drop_indexes(["time", "step"]).set_xindex(["time", "step", "valid_time"], ForecastIndex)
```

`valid_time` is `time + step` as a lazy 2-D variable; it is never stored.

## Best estimate

```python
best = fmrc.sel(valid_time=BestEstimate(offset=6))
```

For each valid time, the newest run that covers it supplies the data. The result
has one `valid_time` dimension, and `time` and `step` say which run and lead each
value came from.

- **`step` must start at 0.** `BestEstimate` raises "Can't make a best estimate
  dataset if forecast_period doesn't start at 0" otherwise, and `offset` does not
  bypass the check (tested with `offset` 0, 1 and 6 on a store starting at 3 h).
  A negative first lead fails the same way. Slice `step >= 0` before building the
  index, or build the store without those steps (not tested).
- **`offset` counts step positions, not hours.** It skips the first N steps of
  each run, for example to drop model spin-up. With 3-hourly steps, `offset=6`
  starts each run 18 hours in. With runs 24 hours apart, each run then supplies
  8 steps and the series stays continuous.

## Other views

- One run on its own needs no Rolodex: `ds.isel(time=k)`. Its valid times are
  `ds.time.values[k] + ds.step.values`.
- Rolodex also provides `ConstantForecast` (everything valid at one time, across
  runs) and `ConstantOffset` (one lead time across all runs). Only
  `ConstantForecast` was run here, and only to see that it raised no error, on a
  store without a lead-0 step; check these before relying on them.

## Read cost

Read one grid point or a small window, not a whole domain. Chunking comes from
the source files: in GoMOFS a 2-D `zeta` chunk covers the whole domain (3.6 MB
per time step), so a point series over 30 steps still moves about 100 MB.

## Checked

`BestEstimate(offset=6)` returned 26 valid times from two runs on a stand-in store
(the `step` shifted in memory so it started at 0). The point selection and plot in
`gomofs-fmrc-rolodex.ipynb` (in the `ocean-icechunks/2026-ioos-hackathon`
repository's `notebooks/` folder) were still being run when this was written.
