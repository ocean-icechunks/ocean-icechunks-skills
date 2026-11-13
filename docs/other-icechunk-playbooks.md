# Four Icechunk playbooks

Four groups have written down how to build Icechunk stores of scientific data:
these **Ocean Icechunks skills**, Earthmover's agent skill, dynamical.org's dataset
guides, and Development Seed's pipeline template. They overlap less than you might
expect, because each was written for a different kind of data and a different
scale of job. Read on 2026-11-13.

## Side by side

| | Ocean Icechunks | Earthmover | dynamical.org | Development Seed |
| --- | --- | --- | --- | --- |
| What it is | Agent skills (open Agent Skills format) | One agent skill with sub-documents | Docs in their code repo that an agent follows | A GitHub template repo with AWS infrastructure |
| Data | Ocean model and satellite NetCDF/HDF5 | Any datacube: HDF5, NetCDF3, GRIB, TIFF, Kerchunk, Zarr | Weather forecasts, mostly GRIB | Any format VirtualiZarr can parse |
| Store types | Virtual only | Virtual and materialized; Icechunk and Arraylake | Virtual and materialized | Virtual |
| Organized by | Task: plan, smoke test, production, docs, audit, learn; plus source and destination patterns | File format, with a 7-step checklist and a requirements interview | Pipeline stage: explore, implement, backfill, validate, publish | Code you write: a processor class with set methods |
| Scale | Sequential batches committed to `main` | Small subset first, then Dask | Up to ~10⁹ refs; parallel backfill on a temp branch | Parallel backfill: forks merged once per partition |
| Keeping current | Not covered yet | Not covered | Cron polling, new data visible within seconds | SNS → SQS → Lambda, a commit per batch |
| Human checks | Stops for review after every step | Asks before starting a Dask cluster | Two hard checkpoints: scope, then draft report | Human runs the deploy and backfill |
| Validation | Values compared with the source files, including across file boundaries | Schema check on all files; values compared with a source file | Exhaustive ref-existence check; sampled decode check | Tests you write for your processor |

## What they agree on

- Virtual stores are built with VirtualiZarr and written to Icechunk. The source
  files stay where they are, and the store's chunks are the source file's chunks.
- Look at real files from across the archive before designing anything.
  Documentation goes out of date.
- Build a small store first and read it back before scaling up.
- Check a finished store by reading data through it and comparing with the source.
- Register source locations as virtual chunk containers and pass credentials when
  the store is opened, never inside it.

## What each one is best at

**Ocean Icechunks** ([`virtual-icechunk`](../skills/virtual-icechunk/),
[`archive-to-cloud`](../skills/archive-to-cloud/))
- Where the bytes live and where the store goes: THREDDS, ERDDAP, S3, NODD,
  Source Cooperative.
- Read performance, and browser access with CORS.
- Separate source and destination credentials, and expiring tokens.
- Copying an archive to a bucket first, and checking the copies.
- Auditing older stores, and feeding build lessons back into the skill.

**Earthmover** ([`icechunk-datacube-ingestion`](https://github.com/earth-mover/agent-skills/tree/main/icechunk-datacube-ingestion))
- A parser note for each file format.
- Forecast model run collections (FMRC).
- Converting existing Kerchunk references (Kerchunk is now in maintenance mode).
- A runnable evaluation harness for the skill.

**dynamical.org** ([dataset development guide](https://github.com/dynamical-org/reformatters/blob/main/docs/dataset_development_guide.md))
- Very large virtual stores: manifest splitting sized from a cost model.
- Whole-file atomic commits, and resuming from what the manifest already holds.
- What "validated" means: complete refs, sampled decoding.
- [Bit rounding](https://github.com/dynamical-org/reformatters/blob/main/src/reformatters/common/binary_rounding.py)
  for better compression of materialized stores.

**Development Seed** ([`virtualizarr-data-pipelines`](https://github.com/developmentseed/virtualizarr-data-pipelines))
- Ready-made AWS infrastructure (CDK, Step Functions, Lambda).
- Parallel backfill with Icechunk fork and merge.
- Deciding per file between append and an in-place region write, so a file
  delivered twice is not stored twice.

## Outstanding: bringing their lessons into these skills

Updating `virtual-icechunk` and `archive-to-cloud` with what these projects learned
is an open issue: [#10](https://github.com/ocean-icechunks/ocean-icechunks-skills/issues/10).
It lists the candidates (manifest splitting, validation wording, append versus
region writes, parallel builds, a data-license check) and what to verify before each
one goes in. None of it has been tested on an ocean build yet.
