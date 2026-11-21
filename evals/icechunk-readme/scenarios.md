# Scenarios: icechunk-readme

Status: draft. The scripts' own tests are `test_render.py` (offline) and
`test_collect.py` (reads the live PacIOOS stores; `ICECHUNK_README_OFFLINE=1` skips
that part). Run each with `python3 -I evals/icechunk-readme/<test>.py`; they need
`requirements.txt`.

## 1. Fill in a product source file from an existing README

The agent is given a published product README (for example the pre-November-2026
`ocean-icechunks/pacioos/roms_hiig/README.md`) and asked to produce the product
source file for it.

## 2. Shorten a long README

The agent is asked to "make this README shorter" for a product whose README holds
a global attributes table, a long build history and a per-variable viewer table.

## 3. New collection with one store

The agent is asked to write the READMEs for a new Source Cooperative product that
holds a single Icechunk store.

## 4. Refresh a README after the store updated

The agent is told that a product's store has new data and asked to bring its
README up to date.

The PacIOOS files under `pacioos/` are the worked example: `source/` holds the
filled-in source files and `expected/` the hand-made output they must reproduce.
