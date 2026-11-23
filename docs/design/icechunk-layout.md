# Layout of Icechunk stores on Source Cooperative (#35)

Decisions and evidence for the `icechunk-layout` skill. It is shared knowledge:
virtual-icechunk asks the layout question at design time, icechunk-readme scans
before writing.

## Decisions (Eli Holmes, 2026-11-23)

- **The layouts are a resource the agent reads**, with the exact options: a collection of
  products (each in its own folder), and per product one store, one store with groups,
  several stores, or several stores some with groups. A product in a collection may have
  several stores.
- **Standard place:** `icechunk/` for a product's only store, `icechunk/<id>/` for each of
  several (`icechunk/na`, `icechunk/np`), with `README.md` and `docs/` beside them.
  "Ultimately I want a standard place for the icechunks so once you see a few of our SC
  collections, you can make a good guess at where the icechunk and docs are."
- **Stores versus groups:** "stores are different datasets within the same product while
  groups are groups in the same dataset." Eli dislikes groups; they are right when the
  files are grouped (measurements and navigation) or when file problems stop all the
  variables going in one group.
- **Design stage:** ask the user which layout. **README stage:** scan, guess, give the
  options and say which it looks like; the user chooses or talks it through.
- **Redesign:** suggest the standard layout when a product has, say, its store at the root
  and no documentation.
- **Groups in the README:** "groups are a bit idiosyncratic, the agent will need to play
  it by ear". No collapsing rule for many near-identical groups (PACE CHL's ten).
- **GOMOFS and ECCOFS:** one product, several stores. README work waits until the skill is
  settled on Eli's own repositories (#34).

## Why a separate skill

Skills here must each install on their own (AGENTS.md). The layout is needed by two of
them, so it is a third skill that both name. Each keeps a short summary, so it still works
without the third.

## Evidence: the scan, 2026-11-23

`scan_layout.py` on 12 Source Coop products. Only `pacioos` (collection) and `necofs-waves`
(standalone, store at `icechunk/necofs_wave_forecast`) already put stores under
`icechunk/`. The others have their stores directly under the root: named for the dataset
(`na`, `monthly`, `timeseries-2d`), with a `.icechunk` suffix (`oisst.icechunk`,
`txla_roms.icechunk`), or one level down (`pace-oci/inregion/PACE_OCI_L3M_*`). Build
notebooks, `icechunk_utils.py` and `requirements.txt` sit loose at the root of most. The
table is in `skills/icechunk-layout/references/layouts.md`.

Ambiguity the scan cannot settle: stores directly under the root may be a standalone
product with several stores (noaa-ohc) or a collection whose products are the stores (old
hycom). Old hycom keeps docs at `docs/<dataset>/`, which the scan reads as "each store is a
dataset"; otherwise it guesses standalone and says the other reading. Both need the user.

Moves are tracked in ocean-icechunks/hycom#27, ocean-icechunks/icechunks#49 (corrected
2026-11-23: the stores do move), #34. Found on the way: PACE KD's `4km` groups have the
0.1° grid (fish-pace/pace-icechunks#3).

## Not verified

- That a copy of a repository prefix reads the same at its new place. It should (our
  stores' references to source files are absolute URLs), but no store has been moved yet.
- The scanner on Source Coop products outside `ocean-icechunks` and `fish-pace`.
