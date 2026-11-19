# Production build

Write this only after the smoke test has passed and its choices have been
reviewed. It is a runnable Python script, not a notebook, and it must survive
being interrupted.

## Shape

- **Configuration at the top, logic below.** Everything that changes between
  variables, streams, or test-versus-production runs lives in one block:
  dataset/stream identifiers, URL prefixes, destination bucket and prefix,
  batch size, group layout, chunk choices.
- **No credentials in the file.** Read them from the environment or a credential
  helper at call time.
- **Do not force unlike sources through one abstraction.** Extract a helper only
  when a second real workflow has proven it reusable. Provider- and
  destination-specific code stays explicit.

## Batching and commits

- Batch size is a configuration value, not a constant. Choose it so a batch
  completes comfortably inside the destination credential lifetime.
- Commit each batch atomically, then open a **fresh writable session** — a
  committed session is read-only.
- Record for every commit: snapshot ID, the manifest range it covers, the file
  count, the first and last combine-coordinate values, and the package versions.
- Check the remaining credential lifetime *before* starting a batch, and refresh
  between batches rather than failing mid-write.

## Memory in a long build

**Provisional: measured on one build** (HYCOM-TSIS GOMb0.01, about 650 M
references, icechunk 2.3.1, virtualizarr 2.8.0, xarray 2026.9.0;
ocean-icechunks/hycom#21). Without the two fixes below, current RSS grew from
2.7 to 6.0 GB over 12 monthly batches. With them it stayed flat at 2.5 GB.

1. **Call `gc.collect()` after every batch.** `ds.vz.to_icechunk(...)` leaves
   the Dataset in a reference cycle: xarray caches the accessor on the Dataset
   (`obj._cache`), and the VirtualiZarr accessor holds the Dataset. After a
   write, a commit and `del batch`, a batch's ManifestArrays stay alive until
   the cyclic GC runs. `del` alone does not free them.
2. **Build through a handle with no chunk-reference cache.** Icechunk caches up
   to 15,000,000 chunk references per `Repository` object by default. A build
   never reads them back, and at fine chunking the cache held about 1.2 GB.
   **Set the zero cache only when opening for the build, never in the config
   passed to `Repository.create`.** `create` persists its config, so every
   reader would lose the cache too. The override at open keeps the persisted
   manifest splitting and virtual chunk containers.

```python
import gc
import icechunk

repo = icechunk.Repository.create(storage, config=reader_config)  # what readers get
repo.save_config()

build_config = icechunk.RepositoryConfig(
    caching=icechunk.CachingConfig(num_chunk_refs=0))  # build only; not saved
repo = icechunk.Repository.open(storage, config=build_config)

for a, b in batches:
    batch = build_batch(a, b)
    session = repo.writable_session("main")
    batch.vz.to_icechunk(session.store, region={"time": slice(a, b)})
    session.commit(f"references for {a}:{b}")
    del batch, session
    gc.collect()
    log(f"batch {a}:{b} rss {current_rss_gb():.2f} GB")
```

3. **Log current RSS per batch, not `ru_maxrss`.** `ru_maxrss` is the process
   peak and can only rise, so it cannot tell retained memory from a growing
   transient. On Linux, read current RSS from `/proc/self/statm` (second field
   × page size).

A fresh process per batch also keeps memory down, but it was not needed once
both fixes were in. RSS barely drops at the `gc.collect()` call itself, because
glibc keeps the freed heap for reuse; what matters is that it stops growing.

### Skeleton, then region writes

For a regular combine axis, a build can write the full-length coordinates and
empty science arrays once (the skeleton), then write references per batch with
`to_icechunk(region={"time": slice(a, b)})`. Batches can run in any order and be
restarted, and the loaded coordinate stays in one chunk. VirtualiZarr 2.7.3
refuses a region start that is not on a chunk boundary, so this pattern does
not misplace data the way a misaligned append can.

**The skeleton does not scale to fine chunking over a long axis.** A skeleton
built as an empty virtual dataset allocates path, offset and length arrays for
every chunk it will ever hold: 0.84 GB per year at one depth per chunk on
HYCOM's hourly 1/100° grid, about 20 GB for the full record. For a long record,
create the empty science arrays with their metadata but no manifest (with zarr
directly, for example), then region-write the references. **Unverified:** that
alternative was planned, not yet run.

## Scanning many HDF5 headers

When references are computed from each file's chunk index (h5py
`get_chunk_info`, or VirtualiZarr's `HDFParser`) over hundreds of thousands of
files, the scan dominates the build.

- **Scan in processes, not threads.** h5py serializes every call on one global
  lock, and the reads happen inside those calls, so threads give no
  parallelism: 8 files on 8 threads took as long as 4 files serially.
  `HDFParser` uses h5py too. Use the `forkserver` or `spawn` start method:
  forking after obstore or tokio threads exist can deadlock. Measured: 28
  files/s at 16 processes on a 4-core machine.
- **h5py directly was 2–3× faster than `HDFParser`** for the same offsets,
  which were byte-identical on every sample file. Worth timing both; keep the
  faster.
- The scan is also where each file is checked (`research-and-plan.md`,
  "Check every file, not a sample"). Save its results, so a rebuild does not
  rescan.

## Restart and recovery

**Derive progress from the committed repository state, reconciled against the
saved source manifest.** Open the repository, read the committed combine
coordinate, and match it against the manifest to find the first unprocessed
file.

An operator-supplied start index is permitted only as an explicit override for
an operator who knows why they are using it — never as the primary mechanism. A
hand-entered integer silently skips or duplicates data, and that has happened in
practice in more than one earlier workflow.

Before each batch, verify: combine coordinates are ordered and unique; no
schema, chunk, or codec drift has crept into the group; the destination
credentials cover the expected duration.

After each batch, reopen and validate the committed boundary before advancing.

## Failures

- Log progress and failures with enough context to resume by hand.
- Handle only the "repository already exists" condition when choosing between
  `Repository.create` and `Repository.open`. A bare `except Exception` around
  both hides authentication, network, and configuration errors — this is a real
  and repeated source of wasted debugging.
- Record every source file you skipped and why. A build that quietly drops files
  is worse than one that stops.

## Finishing

1. Validate the final committed state from the consumer-facing read path
   (`validation.md`).
2. Create an immutable tag naming the last data date covered by the build:

   ```python
   final_snapshot = repo.lookup_snapshot(repo.lookup_branch("main"))
   if tag_id not in repo.list_tags():
       repo.create_tag(tag_id, final_snapshot.id)
   ```

   Builds run on `main`. A staging branch is not required. If you expire
   snapshots afterwards, assert that `main` and the tag still resolve to the
   final snapshot before deleting anything.
3. Publish the environment file, the build script or notebook, and the README
   next to the store (`project-docs.md`).
