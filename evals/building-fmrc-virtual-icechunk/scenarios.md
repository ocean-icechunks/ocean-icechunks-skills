# Evaluation scenarios: building-fmrc-virtual-icechunk

Give the agent one scenario at a time, with no other context. None of these may
write to a production Icechunk repository, dataset, or object store; any
execution must target a local temporary directory or an explicitly scratch
prefix.

## 1. Daily forecast files, keep every run

> A coastal model writes one NetCDF file a day to a bucket. Each file holds 145
> hourly time steps, starting at midnight. We want a virtual Icechunk store that
> keeps every forecast, not just the latest, and that we can update each day.
> Plan it and show the key code.

## 2. Many files per cycle, best estimate wanted

> NOAA's GoMOFS writes four cycles a day. Each cycle is 26 NetCDF files with one
> time step each: `n003`, `n006`, then `f003` to `f072` every 3 hours. We want a
> virtual store of several cycles and a continuous best-estimate series from it.
> Decide which files go in and build a local store of two cycles.

## 3. "Just concatenate them into one time series"

> We have a month of daily forecast files, each with 72 hourly steps. Concatenate
> them along time into one virtual Icechunk store so people can open one dataset.

## 4. The store gets a new run every day

> Our forecast store has `time` and `step`. Write the daily update job that adds
> whatever new runs have appeared in the bucket, and can be re-run safely.

## 5. A best estimate that will not build

> Our forecast store has `time` (cycle) and `step` running from 3 h to 72 h. When
> we select a best estimate with Rolodex we get an error about the forecast
> period. What is wrong, and what are our options?
