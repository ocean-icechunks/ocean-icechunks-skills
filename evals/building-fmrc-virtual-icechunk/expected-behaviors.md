# Expected behaviors: building-fmrc-virtual-icechunk

Grader's rubric. Do not show to the agent under evaluation.

## Across all scenarios

**Should**

- Produce `time` (forecast reference time, one value per run) and `step` (lead
  time), with data as `(time, step, ...)` and valid time computed on read.
- Append new runs along `time`, not flatten runs into one valid-time dimension.
- Keep static variables (grid, masks, bathymetry) free of a `time` dimension, and
  append only variables that have `time`.
- Take the reference time from the file's contents and check it against the name.
- Refuse to write to a production store; use a local or scratch store.
- Say what it checked and what it did not, and treat the pinned-encoding and
  slice-at-read-time guidance as unverified.

**Should not**

- Call `expand_dims("time")` on the whole dataset, or rely on `data_vars="minimal"`
  to keep static variables out of a concat along a scalar `time`.
- Pad an incomplete run with fill values.
- Assume every run has the same number of steps without checking.

## 1. Daily forecast files

- Recognizes the one-file-per-run layout, renames the time dimension to `step`,
  makes the first valid time a scalar `time`, and concatenates along `time`.
- Uses the first time step as the reference time and `time + step` for valid time.
- Designs the update as a diff on reference time against what is in the store.

## 2. GoMOFS cycles

- Treats a cycle as 26 files and joins them along valid time before reshaping.
- Keeps `n006` (valid at the cycle time, lead 0) and the forecast files, and
  leaves out `n003`, because a best estimate needs `step` to start at 0.
- Adds `time` only to variables that have `step`; builds and appends two cycles
  locally; verifies one value against the source file.
- Does not claim the `n003`-slicing alternative works without testing it.

## 3. Concatenate into one time series

- Notices that this flattens the runs and discards earlier forecasts, and asks
  whether a best-estimate series or a run collection is wanted.
- If a run collection is wanted, proposes `time` and `step`.
- Does not silently build the flattened product.

## 4. Daily update job

- Reads the reference times already in the store, lists the runs in the source,
  appends only the new ones in increasing order, and commits per run.
- Re-running with nothing new changes nothing; incomplete runs are skipped and
  reported.

## 5. Best estimate will not build

- Identifies that Rolodex requires `step` to start at 0, and that `offset` does
  not bypass it.
- Offers to include the lead-0 (analysis) file, or to slice `step >= 0` at read
  time if the first lead is negative, and says the second is untested.
- Does not suggest `offset` as the fix.
