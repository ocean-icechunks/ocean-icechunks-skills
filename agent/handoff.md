# Handoff

Rolling session state. Keep it lean: repo state, working principles, recent
work, and pointers into `docs/design/`. Not a task list. Ask Eli before acting
on anything under "Open threads".

## Repo state

- Repo: `ocean-icechunks/ocean-icechunks-skills`, at
  `/home/jovyan/ocean-icechunks-skills`. Issue ocean-icechunks/icechunks#46 calls
  it `ocean-icechunks/skills`; Eli chose to keep the current name (2026-11-13).
- One skill, `virtual-icechunk` (Experimental). Moved here from
  `nmfs-opensci/agent-skills` on 2026-11-13, history kept with `git-filter-repo`.
  Old commit messages name `nmfs-opensci/agent-skills#N` for that repo's issues;
  the design notes were rewritten the same way.
- **License: CC0-1.0** (Eli, 2026-11-13: "not really code"). The skill was
  Apache-2.0 in agent-skills; every commit to it was by Eli or her agents, so
  nobody else's work was relicensed.
- Planned second skill: `archive-to-cloud`, #4 (copied from
  nmfs-opensci/agent-skills#40; GitHub cannot transfer issues between orgs).
- Hub install: `~/.agents/skills/virtual-icechunk` (and `~/.claude/skills/`
  through it) points at this checkout's `skills/virtual-icechunk` since
  2026-11-13, so it follows whatever branch is checked out here.

## Working principles

- `AGENTS.md` and `CONTRIBUTING.md` are strict: one `SKILL.md` per bundle with
  only `name` and `description` in its frontmatter, no README inside a skill
  directory, evals kept under `evals/`, uncertain guidance marked Experimental
  or Provisional.
- Run `ruby .github/scripts/validate_skills.rb` before every commit. It also
  scans the tree for secrets.
- Every change goes through an issue, a branch and a PR, with the real reasoning
  in the PR body.
- Never modify production Icechunk stores, datasets or object storage while
  validating a skill.
- `docs/virtual-icechunk-patterns.md` is the 2026-09-03 evidence base the skill
  was built from. Read it before changing technical claims. For CoastWatch,
  `ocean-icechunks/icechunks` and its notes are fresher.

## What the skill has been through

Used on real builds (OA indicators, HYCOM, CEFI audit, PacIOOS probe); the
evals have only been dry-run on paper. Build lessons are written first in the
store repos (`ocean-icechunks/icechunks`, `hycom`, `cefi-icechunks`, …) and
harvested into the skill on purpose. History of decisions:
[virtual-icechunk-skill.md](../docs/design/virtual-icechunk-skill.md).

## Open threads

- **The move (ocean-icechunks/icechunks#46)**: PR #1 here, nmfs-opensci/agent-skills#41
  there (merge after #1). Still to do are the how-to README
  for this repo, and updating every pointer to the old location (store repos and
  the PacIOOS team note). The hackweek is on 2026-11-17.
- **THREDDS/ERDDAP file-exposure checks**: #2, stacked on the move PR #1. Was
  nmfs-opensci/agent-skills#39 (closed, never reviewed); reopened here so Eli
  can review it in the new home.
- **Append alignment, #3 (was nmfs-opensci/agent-skills#21)**: decisions made, failure verified,
  no skill edits yet. [append-alignment-issue-21.md](../docs/design/append-alignment-issue-21.md).
  Eli has an upstream VirtualiZarr issue drafted but not posted.
- **Lessons from the HYCOM build await a Learn pass**, including two places the
  skill is wrong: [inbound-from-hycom-2026-09.md](../docs/design/inbound-from-hycom-2026-09.md).
- **Formats beyond NetCDF/HDF5 and FMRC**: deliberately deferred by Eli
  (2026-09-18). [expanding-format-coverage.md](../docs/design/expanding-format-coverage.md).
- **Running the evals**: earth-mover's harness would largely port.
  [earth-mover-comparison.md](../docs/design/earth-mover-comparison.md).
