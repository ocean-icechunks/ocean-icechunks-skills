---
name: building-fmrc-virtual-icechunk
description: Build or update a forecast model run collection (FMRC) as a virtual Icechunk store from NetCDF/HDF5 files in which each file, or each group of files, is one forecast run, keeping every run in the store. Use when asked to make a virtual store of a forecast model's output, to append new forecast runs, to give a store both a run (reference) time and a lead time, or to read a best-estimate or single-run series back. Covers reshaping each run's single time dimension into `time` (forecast reference time, one value per run, appended along) and `step` (lead time), keeping static variables out of the append, idempotent updates keyed on reference time, and reading with Rolodex. Use together with virtual-icechunk, which covers the registry, parser, virtual chunk container and commit plumbing.
---

# Forecast model run collections as virtual Icechunk stores

**Experimental.** This guidance comes from two builds (daily SHYFEM Taranto
files; NOAA GoMOFS cycles) and a pair of tutorial notebooks. Each rule below
says what was checked and what was only reported. Check versions before relying
on it.

A forecast file has one `time` dimension of valid times. For a collection that
keeps every run, give the store two time dimensions:

- `time`: the **forecast reference time**, one value per run. New runs are
  **appended along it**.
- `step`: the **lead time** (`forecast_period`), the same values in every run.

Data variables become `(time, step, ...)`. Valid time is `time + step`, computed
when reading and never stored. A reader can then pick one run or build a
best-estimate series that uses the newest run for each hour.

**Do not flatten** to one valid-time `time` dimension (every run appended end to
end). That is a different product, a best-estimate series. It discards earlier
runs and needs the old forecast tail trimmed and rewritten on every update.
Build it only when the user asks for it.

The registry, parser, virtual chunk container, create-versus-append and commit
mechanics are in the `virtual-icechunk` skill. This skill adds only what is
specific to runs and lead times.

## Workflow

1. **Inspect the source.** How are runs laid out: one file per run, or many
   files per run (GoMOFS has 26 files per cycle, one time step each)? Does every
   run have the same number and spacing of steps? Is there a lead-0 (analysis)
   file? Read one raw file's time values and compare them with its name.
2. **Reshape one run** into `(time=1, step, ...)`:
   `references/build-a-cycle.md`.
3. **Create** the store from the first run and **append** later runs along
   `time`, one commit per run or small batch.
4. **Update** by diffing the runs already in the store against the runs found in
   the source, keyed on reference time, and appending only the new ones in
   increasing order.
5. **Verify** (checklist below), then **read** it back:
   `references/read-with-rolodex.md`.

## Rules that bite

- **Lead 0 must be the first step if you want a best estimate.** Rolodex's
  `BestEstimate` raises "Can't make a best estimate dataset if forecast_period
  doesn't start at 0", whatever `offset` is. Reproduced on a store whose `step`
  started at 3 h. Keep the file valid at the reference time (for GoMOFS, `n006`).
  An earlier nowcast file with a negative lead (`n003`, -3 h) also breaks the
  check; leave it out, or slice `step >= 0` at read time (not tested).
- **Add `time` only to variables that have `step`.** `expand_dims("time")` on the
  whole dataset gives every grid, mask and parameter variable a `time`
  dimension, stored once per run. Verified. A concat along a scalar `time`
  coordinate has the same effect, and `data_vars="minimal"` does not prevent it,
  because xarray expands every data variable before it concatenates.
- **Appends carry only variables that have `time`.** Writing static variables
  again rewrites their metadata, which VirtualiZarr refused for scalar
  parameters (reported in the GoMOFS build; the tutorial notebook uses the
  filter and runs).
- **Every run needs the same `step` values.** `step` is one shared dimension.
  Snap valid times to the model's true grid before subtracting, or float
  round-off gives each run slightly different steps. Slice or separate runs of
  different length, and check the count before concatenating so the failure is
  a clear message.
- **Take the reference time from the file contents.** Use the file's own first
  or analysis valid time, and check it against the name. Filename dates can
  differ from the reference time by a day, and modification times change on
  re-upload.
- **Pin the `time` and `step` encodings** (units and integer dtype) on every
  run. Reported in the GoMOFS build: left to xarray, the units depend on each
  run's own values, and an appended run decoded to the wrong date. Provisional:
  not reproduced in the tutorial notebooks.
- **Skip incomplete runs and report them.** Do not pad a run that is missing
  files.

## Verify

- `time` equals the number of runs, `step` equals the run length, and `time` is
  strictly increasing with no duplicates.
- No static variable has a `time` dimension.
- One value read through the store equals the same value read from the source
  file.
- If the user wants a best estimate, build one (`references/read-with-rolodex.md`)
  and check its first and last valid times.

## Evidence and limits

- Per-run reshape and append along `time`: run on synthetic files and on NOAA
  GoMOFS (two cycles appended, a value matched the source file), and the
  Taranto SHYFEM store is built this way.
- `BestEstimate` start-at-0 requirement: read in the Rolodex source and
  reproduced; `offset` semantics read in the source.
- Not covered: chunking of the loaded `time` coordinate when one value is
  appended per run (see the one-element-chunk notes in `virtual-icechunk`);
  stores that mix runs with different step spacing.
