# Expected behaviors: icechunk-layout

## Scenario 1

- Asks whether this is one dataset or several, and whether more datasets will share the
  Source Coop product (collection or standalone).
- Proposes separate stores for 2-D and 3-D (different datasets in one product), not groups;
  explains the rule rather than picking silently.
- Names the layout (e.g. "standalone, `several-stores`") and the paths
  (`icechunk/2d/`, `icechunk/3d/`, `README.md` and `docs/` at the root).

## Scenario 2

- Runs `scan_layout.py` before writing anything.
- Says it looks like a standalone product with several stores, not in the standard places,
  and that a collection of two products is the other reading; lists the options and asks.
- Mentions the moves to the standard layout, but does not make them.

## Scenario 3

- Explains why a store at the root has nowhere for its README and `docs/`.
- Suggests `icechunk/` for the store and the notebook in `docs/`, and lists what a move
  touches (URLs in code, notebooks, viewer links).
- Does not move, copy or delete anything in the bucket itself.

## Scenario 4

- Scans rather than guessing; reports the three regional stores and that there is no
  `docs/` yet (the README is at the root).
