# Handoff

Rolling session state. Keep it lean: repo state, working principles, recent
work, and pointers into `docs/design/`. Not a task list. Ask Eli before acting
on anything under "Open threads".

## Repo state

- Repo: `ocean-icechunks/ocean-icechunks-skills`, at `/home/jovyan/ocean-icechunks-skills`.
  (ocean-icechunks/icechunks#46 calls it `ocean-icechunks/skills`; Eli kept the current name, 2026-11-13.)
- **Four skills, all Experimental:**
  - `virtual-icechunk`: moved from `nmfs-opensci/agent-skills` on 2026-11-13 with history (old commit
    messages cite `nmfs-opensci/agent-skills#N`). Decisions: [virtual-icechunk-skill.md](../docs/design/virtual-icechunk-skill.md).
  - `archive-to-cloud` (#8): audit, copy unchanged, verify. Decisions: [archive-to-cloud.md](../docs/design/archive-to-cloud.md).
  - `building-fmrc-virtual-icechunk` and `adding-ugrid-conventions`: contributed by Rich Signell (rsignell),
    merged 2026-11-19 (#17, #18).
- **License: CC0-1.0** (Eli, 2026-11-13: "not really code"). `virtual-icechunk` was Apache-2.0 in
  agent-skills; every commit to it was by Eli or her agents, so nobody else's work was relicensed.
- Hub install: `~/.agents/skills/<skill>` points at this checkout's `skills/<skill>`, and
  `~/.claude/skills/<skill>` points through it (`~/.gemini/config/skills` *is* `~/.agents/skills`).
  They follow whatever branch is checked out here. README install recipes were verified on 2026-11-13.

## Working principles

- `AGENTS.md` and `CONTRIBUTING.md` are strict: one `SKILL.md` per bundle with only `name` and
  `description` in its frontmatter, no README inside a skill directory, evals kept under `evals/`,
  uncertain guidance marked Experimental or Provisional.
- Run `ruby .github/scripts/validate_skills.rb` before every commit (it also scans for secrets,
  untracked and binary files included).
- Script tests live in `evals/<skill>/`, outside the bundle, and must not write `__pycache__` into a
  skill directory.
- Every change goes through an issue, a branch and a PR, with the real reasoning in the PR body.
- Never modify production Icechunk stores, datasets or object storage while validating a skill.
  Scratch work goes under `ocean-icechunks/test-repo/` on Source Cooperative.
- `docs/virtual-icechunk-patterns.md` is the 2026-09-03 evidence base the skill was built from; read it
  before changing technical claims. For CoastWatch, `ocean-icechunks/icechunks` is fresher.
- Build lessons are written first in the store repos (`icechunks`, `hycom`, `cefi-icechunks`, `pacioos`, …)
  and harvested into the skill on purpose; someone has to carry them across.
- The public artifact "Four Icechunk playbooks" (https://claude.ai/artifact/Q9ZqcXiqYZVBc2tXygyHVd, linked
  from the README) mirrors `docs/other-icechunk-playbooks.md`; keep them in step. Its source HTML is gone:
  read it by URL and republish to the same URL.

## Recently shipped

- **s3:// vs https:// references** (#27 → #28, 2026-11-20): `s3_store` is 2–7× slower than `http_store` on
  endpoints that offer HTTP/2 (Source Coop, GCS, OSN); filed as earth-mover/icechunk#2571. Eli: an Icechunk
  issue, nothing to Source Coop; keep the test stores in `ocean-icechunks/test-repo/s3-vs-https/`. Skill's
  "prefer HTTPS" lines untouched until #2571 is answered (Arraylake forbids `https://` prefixes).
  [s3-vs-https/README.md](../docs/design/s3-vs-https/README.md).
- **HYCOM GOMb0.01 lessons** (#20 → #25, 2026-11-19): what the diff doesn't say is in
  [virtual-icechunk-skill.md](../docs/design/virtual-icechunk-skill.md).

## Open threads

Reviewed 2026-11-21; all are under two weeks old.

- **Ready, small, verified fixes**: #13 (`to_icechunk(encoding=…)` raises TypeError; still in 4 places,
  starting at `SKILL.md:171`) and #15 (`copy-script.md:30` still says re-upload a copy with no sidecar).
- **#14** PacIOOS reanalysis lessons (append attrs, `_FillValue`, `chunks={}`, …): provisional; overlaps
  [inbound-from-hycom-2026-09.md](../docs/design/inbound-from-hycom-2026-09.md), which also awaits a Learn pass
  (two places the skill is wrong; one is #13). Mark that note harvested once #13/#14 land.
- **#3** append alignment: decisions made, no skill edits; waits on Eli's upstream VirtualiZarr issue
  (drafted, not posted). [append-alignment-issue-21.md](../docs/design/append-alignment-issue-21.md).
- **#21** standardized READMEs: layout settled by hand from Eli's markups (2026-11-21), template not built.
  [readme-layout.md](../docs/design/readme-layout.md); examples in `evals/virtual-icechunk/readme-examples/`.
  Overlaps **#19** (documentation bundle), whose files now go in per-level `docs/` folders.
- **#27** skill rule for s3:// vs https://: waits on earth-mover/icechunk#2571.
- **#10** lessons from other playbooks: backlog; Eli's open question is whether keeping stores current is in scope.
- **PR #5** (Renovate bot config, 2026-11-13): Eli to merge or close.
- **`gh skill install`**: test once `gh` in the py-rocket image is 2.90 or later, then fill in the README's
  "Coming" note.
- **Formats beyond NetCDF/HDF5 and FMRC**: deliberately deferred by Eli (2026-09-18).
  [expanding-format-coverage.md](../docs/design/expanding-format-coverage.md).
- **Running the evals**: never done; earth-mover's harness would largely port.
  [earth-mover-comparison.md](../docs/design/earth-mover-comparison.md).
