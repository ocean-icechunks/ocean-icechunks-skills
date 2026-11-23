---
name: icechunk-layout
description: The standard layout of Icechunk stores and their documentation on Source Cooperative, and how to choose, recognize or move to it. Use when designing where a new Icechunk store or set of stores will live (one dataset or several, stores or groups), before writing or updating a README for a store, when asked where a product's stores and docs are, or when a Source Cooperative product has its store at the root, no documentation, or stores in nonstandard places and may need reorganizing. Building the store is the virtual-icechunk skill; writing its README is the icechunk-readme skill.
---

# Icechunk layout on Source Cooperative

**Status: Experimental.** Settled with Eli Holmes on 2026-11-23 from 12 Source
Cooperative products (`ocean-icechunks`, `fish-pace`). Most of them do not follow it yet;
the moves are tracked in their own repositories.

## Terms

- **Source Coop product**: what Source Cooperative calls a product, e.g.
  `ocean-icechunks/pacioos`. It is either a collection or a standalone product.
- **Collection**: a Source Coop product holding several datasets, each in its own folder
  (a product). It is a collection even while it has one product, if more will come
  (`hycom`).
- **Product**: one dataset, with its README and `docs/`.
- **Store**: one Icechunk repository. **Stores are different datasets within one
  product** (OHC's regions; GOMOFS's 2-D and 3-D fields).
- **Group**: a Zarr group inside a store. **Groups are parts of one dataset**: grouped
  that way in the files (measurements and navigation), or split because of file
  problems (OHC's eras: a variable change and a NetCDF-3 to HDF5 switch). Prefer no
  groups; use them only for these reasons.

## The standard layout

```
<sc-product>/README.md            short README
<sc-product>/docs/                documentation.md, metadata.md, build code, notebooks, requirements.txt
<sc-product>/viewer/              optional browser viewer

collection:  <sc-product>/<product>/README.md, docs/, icechunk/ or icechunk/<store>/
standalone:  <sc-product>/icechunk/ or icechunk/<store>/
```

A product's only store is `icechunk/`. Several stores are `icechunk/<store>/`, named for
what differs (`icechunk/na/`, `icechunk/np/`). Never put a store at the root of a Source
Coop product or a product folder: its README and `docs/` could not sit beside it.

## The layout options

Top level: **collection** or **standalone**. Each product then has one of four shapes,
and a product in a collection may have any of them:

| Shape | Tree under the product | Example |
|---|---|---|
| `one-store` | `icechunk/` | gobai-o2 |
| `one-store-groups` | `icechunk/` with groups | noaa-oisst (`daily`, `monthly`) |
| `several-stores` | `icechunk/<store>/` | noaa-gomofs (`2d`, `3d`) |
| `several-stores-groups` | `icechunk/<store>/`, some or all with groups | noaa-ohc (`na`, `np`, `sp`; eras as groups) |

Trees, when to choose each, and what the README shows: [references/layouts.md](references/layouts.md).

## When designing a store

Ask the user, before the first build:

1. Is this one dataset or several? Several datasets that will share a Source Coop product
   make a collection.
2. Does the dataset need more than one store, and why? Stores are for different datasets
   within the product.
3. Do the files force groups? Use groups only for parts of one dataset.

Then state the layout by name (e.g. "standalone, `several-stores-groups`") and the paths
it gives. Record it in the build repository's notes and in the README source file.

## Before writing or updating a README

Scan the Source Coop product, then tell the user which layout it looks like, the other
options, and what differs from the standard layout. Ask before going on; the user may
choose another option or want to talk it through.

```bash
python3 scripts/scan_layout.py <account>/<product>            # listing only
python3 scripts/scan_layout.py <account>/<product> --groups   # also opens each store (icechunk, zarr)
```

The scan reads anonymously and writes nothing. Stores directly under the root are
ambiguous: a standalone product with several stores (noaa-ohc) and a collection whose
products are stores (old hycom) look alike on disk. The scan says which it guesses and
why. Ask.

## Suggesting a redesign

When a product is not in the standard places (a store at the root, no `docs/`, build
files loose at the root), suggest the standard layout and list the moves the scan
prints. Never move anything yourself: these are production stores. The owner moves them,
and a move touches:

- every place that names a store URL: README loaders, viewer links and catalogs,
  notebooks, scripts such as `publish_viewer.py`, and other people's code;
- readers who saved the old URL, who need to find the new one.

A copy of a repository prefix should read the same at its new place, since our stores'
references to source files are absolute URLs. Not yet tried on one of ours: open the copy
and read data before the old prefix is removed.
