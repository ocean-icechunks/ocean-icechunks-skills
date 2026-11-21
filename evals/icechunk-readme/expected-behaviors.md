# Expected behaviors: icechunk-readme

## Scenario 1

- Produces a source file whose front matter validates against `assets/schema.yaml`.
- Leaves out everything the schema marks `auto` (variables, coordinates, snapshot,
  last update, global attributes) instead of copying it from the old README.
- Leaves out inherited fields (provider, repository, code license, viewer URL).
- Puts README prose under the fixed `# README` headings and the rest under
  `# Documentation`, wording unchanged.

## Scenario 2

- Keeps a short README and moves the rest to `docs/documentation.md`, without
  dropping content; global attributes go to a generated `docs/metadata.md`.
- Lists what moved where, for the person to check.
- Asks before overwriting a published README; keeps any block another tool maintains.

## Scenario 3

- Writes both levels (collection and product) even though there is one store.
- Does not invent performance timings or tested versions; asks for them or
  measures them.

## Scenario 4

- Reruns `collect_auto.py` and then `render_readme.py`, into a scratch directory;
  does not edit the `auto/` JSON or the rendered README by hand.
- Reads the store anonymously and writes nothing to the store or the bucket.
- Shows what changed (snapshot, last update, time coverage, file counts) and asks
  before replacing the published README.
