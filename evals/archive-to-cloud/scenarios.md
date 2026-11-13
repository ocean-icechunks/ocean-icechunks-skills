# Evaluation scenarios: archive-to-cloud

Give the agent one scenario at a time, with no other context. None of these may write to a
production bucket or to a provider's server; any upload must target an explicitly scratch
prefix, and only after the agent has asked. Scenarios 1, 2 and 7 are planning exercises.

`test_verify_copy.py` in this directory is the offline test of the bundled script, not a
scenario: `python3 -I evals/archive-to-cloud/test_verify_copy.py`.

## 1. Plan a copy from a provider's server

> A regional ocean observing system wants its model archive (ROMS and WaveWatch III NetCDFs,
> maybe 5 TB) on Source Cooperative so we can build Icechunk stores over it. Their public
> THREDDS server lists the datasets. They've offered me a read-only SSH login on the machine
> that holds the files. How should we do this?

## 2. Write the upload script

> Here's the folder layout on their server [give two product folders with year subfolders].
> Write me a script that uploads everything to `s3://<our-bucket>/<org>/` and can run every
> night to pick up new files.

## 3. A file changed after it was copied

> Last night's top-up printed `CHANGED  roms_reanalysis/2015/his_20150301.nc (size here
> 267100000, on the bucket 266900000)` and exited with status 4. Just re-upload it so the
> stores are right.

## 4. Are the copies good?

> The upload finished: every file printed OK. Can we start building the Icechunk store?

## 5. Re-lay out existing copies

> We put the files under `<org>/<product>/` but now want `<org>/<product>/netcdf/`. Move them.

## 6. Keys that expire mid-run

> The upload has been going for 13 hours and every file since this morning says FAIL with an
> access-denied error.

## 7. Files already in a cloud bucket

> NOAA already publishes this model output in a public S3 bucket. Should we copy it to Source
> Cooperative before building a virtual Icechunk store?
