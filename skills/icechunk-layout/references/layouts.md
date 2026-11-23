# Layout options in detail

Each option: the tree, when to choose it, what the README shows (icechunk-readme), and
an example. Paths are under the Source Coop product, `<account>/<sc-product>/`.

## Top level

### Collection

```
README.md, docs/            collection README: what it is, a row per product, data access, citation, credits
viewer/                     optional, shared by the products
<product>/README.md         product README
<product>/docs/             documentation.md, metadata.md, the product's build files
<product>/icechunk/         or icechunk/<store>/, per the product's shape
<product>/netcdf/           only if the source files were copied here (pacioos)
```

Choose it when the Source Coop product holds several datasets, or will: different
models (pacioos: ROMS, WRF, WaveWatch III), or different HYCOM experiments. The README
skill writes the collection pages and then each product's.

Example: `ocean-icechunks/pacioos`.

### Standalone

```
README.md, docs/            product README and docs at the root
viewer/                     optional
icechunk/                   or icechunk/<store>/, per the shape
```

Choose it when the Source Coop product is one dataset, even if it has several stores.
There is no collection README. The product's source carries what a collection would
(provider, repository, license, credits).

Examples: `ocean-icechunks/noaa-ohc`, `fish-pace/gobai-o2`, `ocean-icechunks/noaa-oisst`.

## Product shapes

### `one-store`

`icechunk/` holds every variable at its root. The README shows one variables table and a
loader with no arguments beyond `ref` and `chunks`. Example: `fish-pace/gobai-o2`.

### `one-store-groups`

`icechunk/` with two or more groups, each a part of the dataset. The README needs a
`groups_note` saying why the store is split, shows one table per group, and its loader
takes `group=`. Examples: `noaa-oisst` (`daily` virtual, `monthly` statistics),
`pace-oci` CHL.

Groups are idiosyncratic. Choose the tables, their order and any merging case by case;
there is no rule yet for collapsing many near-identical groups (PACE CHL has ten).

### `several-stores`

`icechunk/<store>/` for each dataset in the product. The README lists the stores in a
table, and its loader takes `store=`.

- Same variables, different place or grid (noaa-ohc's regions): one set of tables, with
  each store's value where a coordinate differs.
- Different variables (noaa-gomofs 2-D and 3-D, noaa-eccofs best and FMRC): tables per
  store.

### `several-stores-groups`

As `several-stores`, and some or all stores have groups. Example: `noaa-ohc`, whose three
regional stores each have the same three era groups. If the stores' groups differ, the
README shows tables per store.

## Stores or groups

| | Groups in one store | Separate stores |
|---|---|---|
| Meaning | parts of one dataset | different datasets in one product |
| URL and snapshot | one URL, one snapshot for all | one each |
| Updates | one commit updates everything | each on its own schedule |
| Failures, rollback | shared | separate |

A grid change does not force a new store: groups can hold different grids. Choose by
meaning first (Eli Holmes, 2026-11-23).

## Seen on Source Cooperative, 2026-11-23

Read with `scripts/scan_layout.py`. Nearly all predate the standard layout; the move to it
is tracked where noted.

| Source Coop product | Layout | Stores now | Standard place | Tracked in |
|---|---|---|---|---|
| `ocean-icechunks/pacioos` | collection, each `one-store` | `<product>/icechunk` | already | PacIOOS repo (docs/ per level) |
| `ocean-icechunks/hycom` | collection, `one-store` | `hycom-gofs-3pt1-reanalysis/` at the root, docs at `docs/<dataset>/` | `<dataset>/icechunk/`, `<dataset>/docs/` | ocean-icechunks/hycom#27 |
| `ocean-icechunks/noaa-ohc` | standalone, `several-stores-groups` | `na/`, `np/`, `sp/` | `icechunk/na/` ... | ocean-icechunks/icechunks#49 |
| `fish-pace/gobai-o2` | standalone, `one-store` | `monthly/` | `icechunk/` | ocean-icechunks/icechunks#49 |
| `ocean-icechunks/noaa-oisst` | standalone, `one-store-groups` | `oisst.icechunk/` | `icechunk/` | proposed to ocean-icechunks/noaa_oisst |
| `ocean-icechunks/noaa-gomofs` | standalone, `several-stores` | `timeseries-2d/`, `timeseries-3d/` | `icechunk/<store>/` | ocean-icechunks-skills#34 |
| `ocean-icechunks/noaa-eccofs` | standalone, `several-stores` | `eccofs-avg-best/`, `eccofs-avg-fmrc/` | `icechunk/<store>/` | ocean-icechunks-skills#34 |
| `ocean-icechunks/txla-roms` | standalone, `one-store-groups` | `txla_roms.icechunk/` | `icechunk/` | |
| `ocean-icechunks/necofs-waves` | standalone, `one-store` | `icechunk/necofs_wave_forecast/` | `icechunk/` | |
| `ocean-icechunks/oa-indicators` | standalone, `one-store` | `climatology/` | `icechunk/` | |
| `fish-pace/pace-oci` | standalone or a collection with product `inregion` (ask) | `inregion/PACE_OCI_L3M_*` | depends on the answer | |
| `fish-pace/globcolour` | unclear: a production store and `test/` | `<long dataset id>/`, `test/` | ask | |

Patterns that help a guess: our stores that predate the standard sit directly under the
root, named for the dataset or with a `.icechunk` suffix; build notebooks,
`icechunk_utils.py` and `requirements.txt` sit loose at the root; a `viewer/` folder holds
a gridlook build.
