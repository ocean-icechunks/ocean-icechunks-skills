---
name: icechunk-readme
description: Write the README and documentation files for a published collection of Icechunk stores and for each store (product) in it, or for a standalone product with no collection above it, from a standard source file, so every README has the same short shape. Use when asked to write, redo, shorten or standardize the README of an Icechunk store or of a Source Cooperative product holding several stores, to split a long README into README plus docs/documentation.md and docs/metadata.md, to fill in or check a README source file, or to list a store's variables, snapshot and global attributes for its documentation. Building or validating the store itself is the virtual-icechunk skill.
---

# Icechunk README: collection and product

**Status: Experimental, in progress.** The layout was settled by hand on one
collection (PacIOOS, Source Cooperative, November 2026). The scripts were also
run on 19 other stores on Source Cooperative (`ocean-icechunks`, `fish-pace`);
several PacIOOS assumptions remain (see the design note). Say so when you use them.

## Two levels

- **Collection**: a Source Cooperative product holding several stores, e.g.
  `ocean-icechunks/pacioos`.
- **Product**: one store's folder in it, e.g. `pacioos/roms_hiig`. A Source
  Cooperative product that holds, or will hold, several datasets is a
  collection even while it has one store (`hycom`).
- **Standalone product**: a Source Cooperative product that is one dataset, not
  a collection, e.g. `ocean-icechunks/noaa-ohc` (one store per region),
  `fish-pace/gobai-o2` or `ocean-icechunks/noaa-oisst`. It has the product
  pages at its root and no collection README. Its source drops `collection`
  and `row`, sets the fields a collection would (`source_coop`, `provider`,
  `repository`, `code_license`, `credits`, viewer `name` and `url`), and lists
  `stores` when it has several that cannot share arrays (noaa-ohc's regions are
  on different grids). In a collection, each store is a product instead.

Each level has a short `README.md` and a `docs/` folder:

```
<collection>/README.md                 what it is, products table, data access table, citation, credits
<collection>/docs/documentation.md     everything else about the collection; shared build code
<collection>/<product>/README.md       summary, variables, Python access, performance, provenance, citation
<collection>/<product>/docs/documentation.md   everything else; build files, notebooks, requirements.txt
<collection>/<product>/docs/metadata.md        global attributes, generated, never hand-edited

<product>/README.md, <product>/docs/...         a standalone product: the same product pages at its root
<product>/<store>/                              its store, or each of its stores
```

## Rules

1. **Keep the README short.** It carries only what a reader needs first. Move
   the rest, unchanged, to `docs/documentation.md`; do not drop it.
2. **Never hand-write what the store knows.** Variables, coordinates, groups,
   snapshot, last update and global attributes are read from the store. A
   hand-written snapshot goes stale at the next update.
3. **Write each fact once.** Provider, citation, code license and viewer live in
   the collection source file (a standalone product's own); products inherit them. A product's row in the
   collection tables comes from the product's source file.
4. **Plain link text, no emoji or icons.** Viewer links read by viewer name
   ("Gridlook"); code links by language ("Python", or "Python, R").
5. **Say what the store does, not how it got its files.** Some products copy the
   provider's files (PacIOOS); most reference them in place (HYCOM, OHC, OISST).
   The generated text says "source files" either way; the source file's prose
   says which.
6. **The rendered files are a starting point.** A product's owner may customize
   them, and other tools may write into them. Ask before overwriting a
   published README, and keep any block another tool maintains.

## Source files

Markdown with YAML front matter. Start from `assets/collection-template.md`
and `assets/product-template.md`; `assets/schema.yaml` says which fields are
required, which a person writes and which come from the store. Anything that
fits no field goes in `extra_sections`, with the reason, rather than as a
one-off edit to a rendered README.

## Rendering constraints

READMEs are shown by Source Cooperative and by GitHub. Both strip `style`,
`class`, scripts and inline SVG, so there are no custom fonts, colours or tabs.
`<details>`, tables and images on `https://` URLs work in both. On Source
Cooperative a link to a heading on another page needs the `user-content-`
prefix (`README.md#user-content-python`). GitHub's `> [!NOTE]` alerts do not
render on Source Cooperative.

## Collect, then render

Two scripts, run in this order. Their dependencies are listed in the eval's
`requirements.txt`.

`scripts/collect_auto.py` (PyYAML, `icechunk`, `xarray`, `zarr`; `h5py` for
NetCDF-4 attributes) reads what the store knows and writes one
`<product id>.json` per product (`<product id>.<store id>.json` per store of a
standalone product with `stores`). It reads anonymously only: the store's
`main` branch and its references, an S3 listing of the product's `source_url`,
and the header of the newest source file. It writes nothing except `--out`.

```bash
python3 scripts/collect_auto.py collection.md --out auto/     # every listed product
python3 scripts/collect_auto.py <product>.md  --out auto/     # one product
```

- `source_files` counts the files the store references, read from the store
  itself, so it works on any host. Icechunk returns every reference at once,
  about 0.3 to 0.4 GB of memory per million chunks, so above `--max-refs`
  (3 million) it is skipped; raise it on a large machine (HYCOM, 10.5 million
  chunks, peaked at 4 GB). A listing of the product's `source_url` adds sizes
  and the newest file. It must answer an S3 listing (Source Cooperative, an AWS
  bucket, `s3://`); a plain web server (CoastWatch, NCEI) cannot be listed.
- With neither, a store with one time dimension gets an estimate, one file per
  time step, shown as "about N files (estimate)". It was within 1.5% on six
  stores counted exactly, but 2× high where two groups read each file (PACE
  KD). FMRC stores and best time series of forecast runs get none, since their
  files hold many steps. Check an estimate against the provider's own count
  when one exists.
- If sampled source files refuse an anonymous read (NASA's PACE bucket), the
  script says so, and the render fails until `access.auth` says what
  credentials are needed.
- `s3://` virtual chunk containers are opened with anonymous S3 credentials, and
  the README's loader is written to match. A materialized store gets no
  credentials, and a store whose arrays are in groups gets a `group` argument.
- The newest file is chosen by the date in its name, or by last-modified time
  when a name has no date. NetCDF-3 headers are parsed directly; NetCDF-4 files
  need `h5py`.
- The format of the source files (NetCDF-3 classic, NetCDF-4/HDF5, ...) is read
  from the first bytes of the first and last file in each folder, not every
  file. The render puts it in `docs/documentation.md` after "A virtual store",
  unless the source has its own `## Source file format` section or places it
  with `{{source_formats}}`.
- Variables are listed by rank, then name, because the store keeps no stable
  order. Set `order` (`variables`, `coordinates`, `groups`) in the product
  source to choose it; the first group listed is the loader's default.
- `coordinate_notes` and `variable_notes` are keyed by name; a key
  `group/name` applies in that group only (OISST `time` is days in `daily`,
  months in `monthly`).
- With several `stores`, the README's tables are the first store's, a
  coordinate that differs (noaa-ohc's lat/lon grids) shows each store's, and
  the loader takes a `store` argument.
- The JSON is never edited by hand. Rerun the script instead.

`scripts/render_readme.py` (Python 3.10+, PyYAML) turns a source file and that
JSON into the README and `docs/` files. It makes no network request, so a README
can be re-rendered without reading the stores again.

```bash
python3 scripts/render_readme.py collection.md --auto auto/ --out <collection>/
python3 scripts/render_readme.py <product>.md  --auto auto/ --out <collection>/<product>/
python3 scripts/render_readme.py <standalone>.md --auto auto/ --out <product>/
```

- A missing required field or section fails the render with exit status 1 and a
  list of every problem; nothing is written.
- Worked examples, outside this bundle in the
  [ocean-icechunks-skills](https://github.com/ocean-icechunks/ocean-icechunks-skills)
  repository: `evals/icechunk-readme/pacioos/` (a collection) and
  `evals/icechunk-readme/noaa-oisst/` (a standalone product with groups).
- Rendering a collection reads each product's source file for its table row,
  so a product needs at least `row`, `store_url`, `viewer` and `code` before
  its full README is written.
- Render into a scratch directory and compare before replacing a published file.
