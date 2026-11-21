# README layout for collections and products (#21)

Status: **design settled by hand, 2026-11-21; template not yet built.** Part of #21.

Issue #21 planned templates first (phase 1) and designs after (phase 2). Eli reversed that: she
printed two live PacIOOS READMEs, marked them up by hand, and the agent redrafted from the
markup. The template is to be built from these layouts. The redrafted files are the worked
examples in [`evals/virtual-icechunk/readme-examples/pacioos/`](../../evals/virtual-icechunk/readme-examples/pacioos/).

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
product README · Dates · Data, with labelled `NetCDF:` and `Icechunk:` lines in one cell); a
**Data access** table (Dataset · Viewer → "Gridlook" · Code → "Python", linking to each product
README's Python section); Citation and reuse; Credits.

Moved to `docs/documentation.md`: the rest of the intro, the PacIOOS metadata-page links, the
"virtual stores" paragraph with coverage dates, the viewer note, NetCDF access and write-once
rule, known problems, how it was built and where the build files are.

### Product README

Title; link row (View data in browser → Gridlook for this product · Data access (code) ·
provider's dataset page · How to cite · Documentation · Metadata); a short description and the
store URL; the "best time series" explanation; **Variables and coordinates** (the group line is
dropped when there are no groups; with groups, a table per group); **Data access (code) →
Python**: requirements, `pip install`, "Open the dataset in xarray", "Opening takes about a
second", then "Example analyses"; **Performance**: the timing table and how it was measured;
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

## Open

- Build the template and render script against these examples (#21 phase 1 list still applies).
- Pick one set of terms for the template and #21.
- The other PacIOOS products and `noaa-ohc` have not been marked up; expect small additions
  (e.g. `ww3_hawaii`'s "Steps to treat with care").
