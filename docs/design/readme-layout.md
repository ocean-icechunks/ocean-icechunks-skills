# README layout for collections and products (#21)

Status: **design settled by hand, 2026-11-21; schema and templates (slice 1) and an offline render script (slice 2) in `skills/icechunk-readme/`; reading values from the store (slice 3) not built.** Part of #21.

Issue #21 planned templates first (phase 1) and designs after (phase 2). Eli reversed that: she
printed two live PacIOOS READMEs, marked them up by hand, and the agent redrafted from the
markup. The template is to be built from these layouts. The redrafted files are the worked
examples in [`evals/icechunk-readme/pacioos/expected/`](../../evals/icechunk-readme/pacioos/expected/), with their source files in `source/`.

## Terms

Eli's terms, used here (#21 says product/store, and Source Coop calls a whole collection a
"product"; reconcile when the template is written):

- **Collection**: a Source Coop product holding several stores, e.g. `ocean-icechunks/pacioos`.
- **Product**: one store's folder in it, e.g. `pacioos/roms_hiig`.

## Decisions (Eli, 2026-11-21)

1. **Short README, the rest in `docs/`.** The current READMEs have the right content but too much
   of it. Each README keeps what a reader needs first; everything else moves, wording unchanged,
   to `docs/documentation.md`. Nothing is dropped.
2. **One `docs/` per level, no separate `build/`.** The collection's `docs/` holds its
   `documentation.md`, the shared modules and the shared `requirements.txt`. Each product's
   `docs/` holds its `documentation.md`, `metadata.md`, notebooks, build scripts and
   `requirements.txt`. Per-product rather than a central `docs/<product>/`, so a product folder is
   complete on its own and every README uses the same relative path.
   A product `requirements.txt` then includes `../../docs/requirements.txt`; pip resolves includes
   relative to the including file, so this works.
3. **Global metadata attributes go in a generated `docs/metadata.md`,** not in the README or in
   `documentation.md`. A script owns the whole file and rewrites it on each update, so it never
   merges into prose a person wrote. It opens with a "generated, do not edit" line and the
   snapshot it was read from.
4. **The template is a starting point.** It is there so agents write uniform READMEs; a product
   owner may customize afterwards, and a re-render must not be assumed to win. Leave room for
   blocks written by other tools.
5. **Link text, not icons.** Viewer links read "Gridlook", code links read "Python"; another
   language is added as "Python, R, MATLAB". No emoji.

### Collection README

Title; a link row (View data in browser · Data access (code) · Data access (PacIOOS) ·
Documentation); the first sentence of the intro only; a dataset table (Dataset · About → the
product README · Time coverage · Data, with labelled `NetCDF:` and `Icechunk:` lines and an
"Updated <date>" line in one cell); a **Data access** table (Dataset · Store → "icechunk" · Data
files → "netcdf" · Viewer → "Gridlook" · Code → "Python", linking to each product README's Python
section); Citation and reuse; Credits, including a Tooling line for ocean-icechunks-skills (Eli
Holmes, then Rich Signell, then other contributors).

Moved to `docs/documentation.md`: the rest of the intro, the PacIOOS metadata-page links, the
"virtual stores" paragraph with coverage dates, the viewer note, NetCDF access and write-once
rule, known problems, how it was built and where the build files are.

### Product README

Title; link row (View data in browser → Gridlook for this product · Data access (code) ·
provider's dataset page · How to cite · Documentation · Metadata); a short description and the
store URL; the "best time series" explanation; **Variables and coordinates** (the group line is
dropped when there are no groups; with groups, a table per group); **Data access (code) →
Python**: requirements, `pip install`, "Open the dataset in xarray", a "Subset, then chunk"
paragraph pointing to the example that does so, then "Example analyses"; **Performance**: the timing table and how it was measured;
**Provenance**: source files, one line for built / last update / snapshot, tested versions,
build-file list, how it was made; Citation and reuse.

Moved to `docs/documentation.md`: what the store adds over the files, "this store is virtual",
the per-variable viewer table, where the metadata came from, the time-axis check, the icechunk
1.x warning and why the code authorizes virtual chunk access, why chunk shape makes point series
slow, full build / validation / test details, the update history.

Code changes: the `chunks={}` advice became a comment above `ds = open_forecast()`; the
concurrency comment shortened; the comment explaining virtual chunk access moved to
`documentation.md`.

## Constraints found

- **Rendering.** Source Coop renders README with `react-markdown`, GFM and `rehype-raw`
  filtered by `rehype-sanitize`'s default (GitHub-style) schema, plus `img` width/height
  (`source-cooperative/source.coop`, `src/components/features/markdown/MarkdownViewer.tsx`, read
  2026-11-21). Allowed: `<details>`, tables, `align`, `<picture>`. Stripped: `style`, `class`,
  `<svg>`, scripts, `data:` images. No GitHub `> [!NOTE]` alerts. No custom fonts or real tabs
  on either Source Coop or GitHub. Read from source, not checked in a browser.
- **Headings get a `user-content-` prefix on Source Coop.** A link to a heading on another page
  needs it (`README.md#user-content-python`). From the source; not checked in a browser.
- **Other `.md` files render on Source Coop**, e.g.
  `source.coop/ocean-icechunks/pacioos/roms_hiig/how_store_created.md` (Eli checked).
- **PacIOOS writes to product READMEs.** `ocean-icechunks/pacioos` PR #36 (`ops/dataset_readme.py`)
  rewrites a block between `<!-- icechunker:global-attributes:start/end -->` in each product's
  `README.md` on every update; WRF's README is PacIOOS's own (PR #37). Decision 3 moves that
  block to `docs/metadata.md`; Eli will propose the change to the PacIOOS team in a PR.
- **Hand-written dates go stale.** The `roms_hiig` README said last update 2026-11-18, snapshot
  `XA93…`, while the store's `history` shows a 2026-11-19 update (snapshot `XDCV…`). Snapshot
  and last-update fields should be filled from the store.

## Template decisions (Eli, 2026-11-21)

- **Its own skill, `icechunk-readme`**, not part of `virtual-icechunk`: the collection/product
  README is not specific to virtual stores.
- **Markdown with YAML front matter** as the source format: structured fields in YAML, prose
  under fixed `# README` / `# Documentation` headings.
- **Collection/product** as the terms.
- Built in slices: (1) schema and source files, (2) offline render reproducing the examples,
  (3) auto-fill from the store, (4) skill text in `virtual-icechunk/references/project-docs.md`
  points here.

## Old checklist mapped to fields

Every item of the README checklist in `skills/virtual-icechunk/references/project-docs.md`
maps to a field in `skills/icechunk-readme/assets/schema.yaml`:

| Checklist item | Field |
|---|---|
| That this is a virtual store, and who operates the source | product `# Documentation` → "A virtual store" (required); collection `provider` |
| Exact public repository URL | `store_url` |
| Groups, coverage, variables | auto: `groups`, `coordinates`, `variables` |
| Known gaps or excluded files | `## Caveats` (README) or `## Source files`; collection "Known problems in the files" |
| Why the groups exist | `groups_note` (required with more than one group) |
| Source and destination authentication | `access.auth`; the Python section says "no credentials" when it is absent |
| Compute-region or network restrictions | `access.region` |
| Minimum and tested package versions | `code.python.python_version`, `packages`; `provenance.tested_with` |
| A representative read, lazy-loading guidance | generated loader + `## Example analyses`; `code.python.chunks_advice` |
| Source chunk limitations and observed performance, with the concurrency setting | `performance`; `code.python.concurrency`; documentation "Performance: why reads cost what they do" |
| Provenance: build script, manifest, snapshot, update date | `provenance`; auto `snapshot`, `last_update` |
| Anything unverified | `## Caveats` |

Sections found in published READMEs but not on the checklist (probably added on request):
the **global attributes** tables → generated `docs/metadata.md` (`metadata.netcdf_attributes` for
the second table); **Latest completed NetCDF copy** → same; the **per-variable viewer table** →
`viewer.fields`, shown in documentation; **Reading it fast** → `performance`. `ww3_hawaii`'s
"Where the metadata came from" and "Steps to treat with care" are not yet mapped (product not
marked up); the first fits a documentation section, the second probably `## Caveats`.

## Slice 2: what the render script changed (2026-11-21)

The script reproduces the hand-made files in `evals/icechunk-readme/pacioos/expected/` except for
line wrapping (the test joins wrapped lines; the rendered page is the same). Making the two levels
consistent changed three things in the expected files:

- The collection's code-license paragraph now names the repository, as the product's does.
- The collection `documentation.md` opens with the same sentence shape as the product's
  ("Technical detail for the `pacioos` collection. The README has what most readers need; this
  page has the rest."). The old sentence also said "PacIOOS product", from before the terms changed.
- The product README's last update and snapshot now come from the same store values as
  `metadata.md` (2026-11-19, `XDCV…`). The hand-made README had `XA93…`, a day stale: the bug
  rule 2 exists for.

Schema additions: `provenance.build_files` entries may be `{file, label}`, `provider.citation_url`; the collection's
`## Citation` is now optional, defaulting to a generated sentence. The test also caught that YAML
reads ` #` as a comment (`label: issue #10` became `issue`); the templates now warn about it.

Three partial product source files (`roms_hiig_reanalysis`, `wrf_hi`, `ww3_hawaii`) hold only what
the collection tables need.

### Review changes (Eli, 2026-11-21)

- **Time coverage** (was "Dates") is the first and last value of each store's time axis. The
  hand-made README mixed two meanings (ROMS gave the last NetCDF run, WRF the forecast end). The
  `auto/` fixtures' `time_range` and `last_update` were read from the four public stores on
  2026-11-21.
- **Last commit** is shown as "Updated <date>" under the Icechunk line in the collection table, so
  no column is added, and under the store URL in the product README. Eli will say if the
  collection table gets too cluttered.
- **Data access** gains Store ("icechunk") and Data files ("netcdf", or the format of the source
  files) columns. They link to the Source Coop browse pages (`source.coop/...`): a browser gets 404
  from the `data.source.coop` store URL, and the browse page drops a trailing slash by redirect.
- **Chunking advice** is general, not product-specific: large stores hold many references, so open
  with `chunks=None`, subset, then `.chunk()` for dask work. One example must show it
  (`code.python.dask_example` points to it). The roms_hiig July-mean example was run against the
  public store on 2026-11-21: 248 steps in 31 dask tasks, 4.3 s. "Opening takes about a second"
  (`performance.open_time`) was dropped.

## Open

- Slice 3 is built; see "Slice 3 (built 2026-11-21)" below. Slice 4 is not planned yet.
- The hand-written source text (e.g. roms_hiig "Source files": 657 runs to 2026-11-17) and the
  frozen file counts are already stale. Eli: refresh them when this work is finished and the new
  READMEs are posted, not before.
- The collection's "The Icechunk stores" section carries hand-written coverage dates; they go stale like the product snapshot did.
- The other PacIOOS products and `noaa-ohc` have not been marked up; expect small additions
  (e.g. `ww3_hawaii`'s "Steps to treat with care").

## Slice 3 plan (agreed with Eli, 2026-11-21)

- A separate script, `collect_auto.py`, reads each store and its source-file prefix and writes the
  `<product id>.json` that `render_readme.py --auto` takes. The render script stays offline, so its
  tests keep working and a README can be re-rendered without reading the stores again.
- Read-only and anonymous over HTTPS: `time_range` (first and last time value, dates),
  `last_update` and `snapshot` (main's latest snapshot), `groups`, `variables`, `coordinates`,
  `store_attributes`, and `source_files` (format from the extension, path, count, size). Optionally
  `netcdf_attributes` from the newest file.
- New dependencies, `icechunk`, `xarray` and `zarr`, go in `evals/icechunk-readme/requirements.txt`
  (and say so in SKILL.md); check whether plain HTTP can list the bucket before adding a package.
- Tests run against the live PacIOOS stores and check structure, not exact dates (the stores update
  daily). Run the whole eval in a clean venv (`/srv/conda/bin/python3.12 -m venv`); it was never
  run for slice 2 (permission check refused it) and Eli folded it into slice 3.

## Slice 3 (built 2026-11-21)

`scripts/collect_auto.py` follows the plan. Evidence from the four live PacIOOS stores:

- **Listing needs no package.** `https://data.source.coop/<account>?list-type=2&prefix=...` answers
  a plain S3 ListObjectsV2 request anonymously. Only `.nc`/`.h5`-type keys are counted, so the
  `.md5` sidecars beside each file are left out.
- **The store cannot say where its files are.** All four stores have a single virtual chunk
  container, `https://data.source.coop/ocean-icechunks/pacioos/`, the whole collection. So the
  source prefix is the product's `netcdf_url`; the three partial PacIOOS sources gained one.
- **Source formats differ within a collection.** `roms_hiig` and `ww3_hawaii` files are NetCDF-3
  classic (`CDF\x01`); `wrf_hi` and the reanalysis are NetCDF-4/HDF5. h5py alone could not read the
  `roms_hiig` attributes, so the script parses NetCDF-3 headers itself over range requests (a few
  kB) and uses h5py only for HDF5. NetCDF-4 internal attributes (`_NCProperties`, ...) are dropped,
  as xarray does.
- **xarray drops a global `coordinates` attribute** (it moves into encoding). Store attributes are
  read with zarr, so `docs/metadata.md` keeps it, as the hand-made file has.
- **Standard name cell:** `standard_name`, else `variable_notes`, else `long_name`. The script writes
  `long_name` separately so a person's note still wins over the file's (e.g. `mask`, whose long name
  is "field mask").
- **Variable order** is not stable in the store, so variables are sorted by rank, then name, and other
  coordinates follow their dimension by name. Rendered from live values, roms_hiig's README differs
  from the hand-made one only in that order (`salt` before `temp`, `forecast_period` before
  `forecast_reference_time`) and in values that moved since the fixture was frozen (file counts, the
  newest NetCDF file). Eli asked for an optional `order` field (`order.variables`,
  `order.coordinates`); a listed name the store lacks fails the render, so a typo cannot hide.
- **Source formats in documentation.md** (Eli, 2026-11-21: "add source formats information if it
  is not already there"). Checking every header costs a request per file, so the collector reads
  the first 8 bytes of the first and last file in each folder (4 to 32 requests for PacIOOS) and
  says so on the page. A provider that changes format usually does it between years or versions,
  which the folder ends catch; a change inside a folder would be missed. The section goes after
  "A virtual store" unless the source has its own `## Source file format` section.
- **Timing:** all four stores and listings in about 11 s on the hub.
- **Clean run:** a venv from `$NB_PYTHON_PREFIX/bin/python` (3.13 on this hub) with only
  `evals/icechunk-readme/requirements.txt`: `test_render.py` 19/19, `test_collect.py` 16/16 (after the more-stores round).

## Other collections (run 2026-11-21)

Eli: run the scripts on the other stores to find what PacIOOS hid. Trial sources were throwaway
copies of `roms_hiig.md` (prose wrong, code paths real) in a scratch directory; nothing was written
to `~/hycom`, `~/icechunks` or any store. Stores: `hycom/hycom-gofs-3pt1-reanalysis`,
`noaa-ohc/{na,np,sp}`, `fish-pace/gobai-o2/monthly`, `oa-indicators/climatology`,
`noaa-oisst/oisst.icechunk`.

Fixed:

- **`s3://` containers** (OISST): `HttpAccess` is refused; the collector and the README loader use
  `icechunk.containers_credentials` with `s3_anonymous_credentials()`. The loader keeps the plain
  form when every container is HTTPS (PacIOOS unchanged) and drops the lines for a materialized
  store (GOBAI-O2). The rendered OISST, GOBAI-O2 and OHC loaders were run and read data.
- **Arrays only in groups** (OHC, OISST): the loader gains `group=` (first of `order.groups`), or it
  opens an empty root. Groups sort alphabetically (`14day`, `14day_v1`, `daily`), so `order.groups`.
- **Attributes per group, none at the root** (OHC, OISST): `group_attributes`, one table per group in
  metadata.md; an empty `store_attributes` is allowed.
- **`time_range` over every group**: OHC's groups are eras; the first group alone said 2025.
- **No time axis** (OA indicators, a climatology): optional `row.time_coverage`.
- **Source files outside the collection**: AWS buckets (HYCOM `https://<bucket>.s3.<region>.amazonaws.com/`,
  OISST `s3://`) list fine; `path` is then the full URL and the table links the HTTPS form. HYCOM's
  63,341 files list in ~17 s. CoastWatch and NCEI are plain web servers: left out, with a message.
- **Newest file by name** missed `YYYYMMDDHH` (HYCOM); now 8, 10 or 12 digits, ties by name (t021 after t000).
- **Format sample capped at 40 files**: OISST has 543 monthly folders. Sizes under 0.1 TB print in GB
  (OISST 28 GB was "0.03 TB"). Scalar CF variables (`crs`) show "scalar" for dimensions.

Open, for Eli (answered 2026-11-23, see "Decisions (Eli, 2026-11-23)" below):

- **Where a product's README goes.** The renderer links `<collection>/<id>/README.md` and `docs/`.
  PacIOOS keeps the store one level down (`<id>/icechunk`); OHC, HYCOM and GOBAI-O2 *are* the
  product folder (the README would sit inside the Icechunk repository prefix), HYCOM publishes its
  docs at `hycom/docs/<dataset>/`, and OISST has one store, `oisst.icechunk`, at the collection root.
- **"Copies" wording.** "The code that copied the files", "the NetCDF copies" and "Latest completed
  NetCDF copy" are true only where the files were copied (PacIOOS). HYCOM, OHC, OISST and OA
  reference the provider's own files.
- `coordinate_notes` is keyed by name across groups; OISST `time` means days in `daily`, months in
  `monthly`.
- `netcdf_url` is also used for HDF5 sources; the name fits PacIOOS only.
- OISST is built by NERACOOS/GMRI (ocean-icechunks/noaa_oisst); a README there may be another tool's.

## More stores (run 2026-11-21)

Eli: try more stores to make the skill robust; skip any that need a repository not on the hub. The
repositories were found by walking both accounts' listings for `snapshots/` + `refs/` prefixes
(`chla-z` has none within three levels; `globcolour/test` skipped). Tried: `necofs-waves`,
`neracoos-necofs-casco`, `noaa-eccofs` (best, fmrc), `noaa-gomofs` (2-D, 3-D), `txla-roms`,
`fish-pace/coastwatch/ocean-heat/na`, `fish-pace/globcolour` P1D, `fish-pace/pace-oci` CHL, KD, RRS.
Their build repositories are not on the hub, so no `netcdf_url` was guessed; that led to the change
below. All read anonymously; nothing was written.

- **File counts from the store's references.** `session.all_virtual_chunk_locations()` lists every
  referenced file on any host. Measured: necofs-waves 565 chunks in 6 s; noaa-ohc/na 19,293 chunks,
  2,294 files, 17 s; txla 105,000 chunks, 10 s; roms_hiig 804,025 chunks, 5 s, ~400 MB; gomofs 2-D
  223,018 chunks, 17,148 files, 26 s. Memory is ~0.4 GB per million chunks, so it is skipped above
  `--max-refs` (3 million, from array shapes), for HYCOM (~10.6 M), ECCOFS (9 to 67 M), GlobColour (127 M)
  and PACE RRS (52 M). A listing still supplies counts and sizes where `netcdf_url` is listable.
  The references also caught a wrong guess: the trial OHC `netcdf_url` (`socd/lsa/heat-content/`) is
  not where the store reads (`socd2/coastwatch/ocean_heat/`), and showed OHC mixes NetCDF-3 and
  NetCDF-4 files across its eras.
- **s3:// references to HTTPS** for the format sample: a Source Cooperative container
  (`s3://ocean-icechunks/...`, endpoint `https://data.source.coop`, path-style) and an AWS one
  (`s3://noaa-nos-ofs-pds/`, region only) map differently; both come from the container config.
- **Anonymous reads refused** (PACE: NASA's `ob-cumulus-prod-public` answers 403, though the store
  opens). The collector records it; the render fails until `access.auth` is set, so a README cannot
  claim "No credentials".
- **Coordinates:** timedelta leads (`step`, `lead`) as hours, not nanoseconds; dimensions with no
  coordinate variable (`node`, `nele`, `eta_rho`, `X`, `Y`) listed with their size; the range of
  non-dimension coordinates (2-D or unstructured lat/lon, run times) up to 10 M values. NaT run times
  (best series) are skipped: `ww3_hawaii` broke on them once ranges were read.
- **Format sample** takes at least 10 files, so one flat folder (PACE) is not just its two ends.

Seen, not changed: PACE stores carry a `palette` display variable and up to ten nested groups
(`/8Day/0p1deg/chunks_16`); FMRC stores (casco, necofs) have `time` = run time, so their time
coverage is the run dates, not the forecast end; `fish-pace/coastwatch/ocean-heat` looks like an older
copy of `noaa-ohc`.

## Decisions (Eli, 2026-11-23)

Answers to the open questions above, and what was built from them:

- **Layout.** HYCOM moves to `hycom/<dataset>/icechunk`, `<dataset>/README.md`, `<dataset>/docs/`, like
  PacIOOS (ocean-icechunks/hycom#27). `noaa-ohc` stays as it is: `na`, `np`, `sp` are regions of one
  product, not products. `gobai-o2` is the same case. Both get a short README plus `docs/` at the product
  root (ocean-icechunks/icechunks#49). Built: the **standalone product**. A product source with no
  `collection` is itself the Source Coop product. It sets the collection's fields and `credits`, and
  its pages render at the product root. An optional `stores` list replaces `store_url` for stores that
  cannot share arrays. Its pages carry:
  - A stores table with time coverage, source files and update date.
  - The first store's tables; a coordinate that differs (OHC's lat/lon) shows each store's value, and
    a part they share once.
  - A loader with a `store=` argument.
  - Per-store sections in documentation.md and metadata.md.
  - `collect_auto.py` writes `<id>.<store>.json` per store.
  Rendered from the live OHC stores, the loader read `np/14day` and `sp`. Rule: `stores` only for a
  standalone product; in a collection each store is a product.
- **"Copies" wording: neutral.** The generated text now says "the source files", "this store or its source
  files", "The code that built the store", "Newest source file". The source's prose says whether files
  were copied.
- **Per-group notes.** Eli: "I don't know how to decide." Chosen: keys may be `group/name`, which beats
  `name`. It is backward compatible, and OISST needed it.
- **`source_url`** replaces `netcdf_url` (format neutral); `metadata.source_attributes` replaces
  `metadata.netcdf_attributes` for the same reason.
- **OISST: write it.** Eli will offer it to ocean-icechunks/noaa_oisst by PR; the maintainers decide.
  Source and rendered files are in `evals/icechunk-readme/noaa-oisst/`. Written from the live store
  (2026-11-23) and the maintainers' repo, which now publishes its pipeline (`src/ohw26_oisst_icechunk`,
  `docs/operations.md`, BSD-3-Clause, Alex Kerney). Three things on the old page (`ocean-icechunks/icechunks`,
  `noaa-oisst/README.md`, 2026-09-19) are no longer true:
  - `daily/time` is now chunked 4,096 a chunk, so opening `daily` takes 1.6 s, not 7 s.
  - `monthly` has its own long names, `cell_methods` and group attributes.
  - `valid_min`/`valid_max` are gone from `monthly`.
  Both hosts still send `Access-Control-Allow-Origin: *`. The store's newest snapshot was 2026-11-18,
  five days before the check, although the workflow runs four times a day (noaa_oisst#4 "Current
  icechunk status" is open). Added for it: `viewer.group` (the viewer opens `oisst.icechunk/daily`),
  the provider's data link in a standalone header, and boolean coordinates described as "true for the
  last 14, false before".
- **Counts for stores with many references.** On this VM (15.6 GB cap):
  - HYCOM: 10,451,265 chunks, 63,341 files, 31 s, peak 4.0 GB.
  - ECCOFS best: 9,441,043 chunks, 170 files, 29 s, peak 2.7 GB.

  Icechunk 2.3.1 has no partial or streaming reference API: `all_virtual_chunk_locations()` returns
  one string per chunk, and an unauthorized read names only the container prefix. The others are
  beyond the cap (PACE RRS 52 M, ECCOFS FMRC 68 M, GlobColour 127 M). Eli asked for a sampled estimate.
  Built: one file per time step, for stores with a single time dimension, shown as "about N files
  (estimate)". Checked against exact counts:

  | Store | Steps | Files | |
  |---|---|---|---|
  | gomofs 2-D | 17,148 | 17,148 | exact |
  | PACE CHL | 1,648 | 1,648 | exact |
  | OHC na | 2,294 | 2,294 | exact |
  | ECCOFS best | 170 | 170 | exact |
  | HYCOM | 64,272 | 63,341 | 1.5% high |
  | PACE KD | 1,790 | 895 | 2× (two groups read each file) |
  | casco FMRC (time × step) | 576 | 3 | one file per run |
  | ECCOFS FMRC (time × step) | 1,224 | 1,224 listed | one file per step |
  | roms_hiig, txla (best series) | 5,545, 2,184 | 657, 69 | |

  So FMRC stores (more than one time dimension) and best time series (a run time or lead along
  `time`) get no estimate. Results: PACE RRS about 1,648 (estimate). GlobColour about 10,490
  (estimate); its folder lists 10,610. ECCOFS FMRC 1,224 files, 9.29 TB, from a listing of
  `s3://noaa-nos-eccofs-pds/avg/`. PACE's bucket refuses anonymous listing (requester pays) and,
  per the pace-icechunks README, reads need Earthdata credentials from us-west-2.

