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
  `evals/icechunk-readme/requirements.txt`: `test_render.py` 14/14, `test_collect.py` 8/8.

