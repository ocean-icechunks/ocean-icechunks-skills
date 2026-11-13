# Handoff

Rolling session state. Keep it lean: repo state, working principles, recent
work, and pointers into `docs/design/`. Not a task list. Ask Eli before acting
on anything under "Open threads".

## Repo state

- Repo: `ocean-icechunks/ocean-icechunks-skills`, at
  `/home/jovyan/ocean-icechunks-skills`. Issue ocean-icechunks/icechunks#46 calls
  it `ocean-icechunks/skills`; Eli chose to keep the current name (2026-11-13).
- Two skills, both Experimental:
  - `virtual-icechunk`. Moved here from `nmfs-opensci/agent-skills` on 2026-11-13,
    history kept with `git-filter-repo`. Old commit messages name
    `nmfs-opensci/agent-skills#N` for that repo's issues; the design notes were
    rewritten the same way.
  - `archive-to-cloud` (#8, merged 2026-11-13; #4 closed): audit a provider's archive,
    copy it unchanged to object storage, verify the copies. See "archive-to-cloud" below.
- **License: CC0-1.0** (Eli, 2026-11-13: "not really code"). `virtual-icechunk` was
  Apache-2.0 in agent-skills; every commit to it was by Eli or her agents, so
  nobody else's work was relicensed.
- Hub install: `~/.agents/skills/<skill>` points at this checkout's `skills/<skill>`,
  and `~/.claude/skills/<skill>` points through it (`~/.gemini/config/skills` *is*
  `~/.agents/skills`). Both skills since 2026-11-13. They follow whatever branch is
  checked out here.

## Working principles

- `AGENTS.md` and `CONTRIBUTING.md` are strict: one `SKILL.md` per bundle with
  only `name` and `description` in its frontmatter, no README inside a skill
  directory, evals kept under `evals/`, uncertain guidance marked Experimental
  or Provisional.
- Run `ruby .github/scripts/validate_skills.rb` before every commit. It also
  scans the tree for secrets, including untracked files, and binary ones as
  bytes (fixed in #8; it used to crash on a `.pyc`).
- Script tests live in `evals/<skill>/` (e.g. `test_verify_copy.py`), outside
  the bundle, and must not write `__pycache__` into a skill directory.
- Every change goes through an issue, a branch and a PR, with the real reasoning
  in the PR body.
- Never modify production Icechunk stores, datasets or object storage while
  validating a skill.
- `docs/virtual-icechunk-patterns.md` is the 2026-09-03 evidence base the skill
  was built from. Read it before changing technical claims. For CoastWatch,
  `ocean-icechunks/icechunks` and its notes are fresher.

## What virtual-icechunk has been through

Used on real builds (OA indicators, HYCOM, CEFI audit, PacIOOS probe); the
evals have only been dry-run on paper. Build lessons are written first in the
store repos (`ocean-icechunks/icechunks`, `hycom`, `cefi-icechunks`, …) and
harvested into the skill on purpose. History of decisions:
[virtual-icechunk-skill.md](../docs/design/virtual-icechunk-skill.md).

## archive-to-cloud: decisions (Eli, 2026-11-13)

Reasoning in full in the #8 PR body. Evidence came from ocean-icechunks/pacioos
(`upload/`, `docs/design/`, #2), noaa-nwfsc/cefi-icechunks (`audit/`, notes), and
ocean-icechunks/icechunks (AGENTS.md, notes).

- **Only the verify script is bundled.** No upload scripts: `copy-script.md` is a
  contract for writing one per job, with PacIOOS `upload/` as the worked example.
  Don't "complete" the skill by importing the PacIOOS scripts.
- **The audit is split by job.** Inventory and integrity checks are here; whether files
  can be virtualized stays in `virtual-icechunk`. Don't duplicate chunking guidance.
- **`change-detection.md` is Provisional** until ocean-icechunks/pacioos#2 settles;
  harvest the answers from there.
- `verify_copy.py` was tested on Python 3.12 only. Listing and sampled MD5s were run on
  the PacIOOS copies, and listing on the CEFI NODD bucket. The evals are written, not run.
- Found on the way: ocean-icechunks/pacioos#9 (the upload script hides a failed listing
  and could overwrite copies). PacIOOS's copy, their fix.

## Other playbooks: positioning (Eli, 2026-11-13)

From the ESIP dynamical.org links (Earthmover skill, dynamical.org guides, Development
Seed `virtualizarr-data-pipelines`, dynamical bit rounding). Shipped in #11.

- **Our skills are stage 1**: a knowledge layer for ocean sources, for experimental and
  research-level virtual stores, for someone starting from NetCDF/HDF5 files on a server
  or object storage (or moving them there). **Development Seed's template is stage 2**,
  production pipelines; what stage 1 works out becomes its processor. Earthmover is a
  skill too but is built around file formats, tailored to Arraylake, and assumes files are
  already in an Arraylake bucket (no HTTPS/THREDDS; checked in its SKILL.md step 2).
  dynamical.org is lessons, not reusable code. None of them is a base to rebuild ours on.
- **The comparison lives in two places, keep them in step**: the public artifact "Four
  Icechunk playbooks" (https://claude.ai/artifact/Q9ZqcXiqYZVBc2tXygyHVd, linked from the
  README) and `docs/other-icechunk-playbooks.md`. The artifact's source HTML was in a session
  scratchpad and is gone; to edit it, read it by URL first and republish to the same URL.

## Open threads

- **Lessons from the other playbooks, #10**: candidate additions (manifest-split cost
  model, "what validated means", append vs region writes, parallel builds, license check,
  Kerchunk is in *maintenance mode* not "deprecated", NetCDF3 sub-chunk refs for #3).
  Nothing tested. Bit rounding was ruled out (materialized only). Whether keeping stores
  current is in scope is Eli's open question; it decides how much of #10 matters.
- **The move is finished** (ocean-icechunks/icechunks#46, closed 2026-11-13): here
  #1 (a merge commit, to keep history), #2 and #6 (README). Elsewhere:
  nmfs-opensci/agent-skills#41, icechunks#48, cefi-icechunks#9, pacioos#8, hycom#14,
  and the PacIOOS team note. One follow-up: test `gh skill install` once `gh` in the
  py-rocket image is 2.90 or later, then fill in the README's "Coming" note.
- **Append alignment, #3 (was nmfs-opensci/agent-skills#21)**: decisions made, failure verified,
  no skill edits yet. [append-alignment-issue-21.md](../docs/design/append-alignment-issue-21.md).
  Eli has an upstream VirtualiZarr issue drafted but not posted.
- **Lessons from the HYCOM build await a Learn pass**, including two places the
  skill is wrong: [inbound-from-hycom-2026-09.md](../docs/design/inbound-from-hycom-2026-09.md).
- **Formats beyond NetCDF/HDF5 and FMRC**: deliberately deferred by Eli
  (2026-09-18). [expanding-format-coverage.md](../docs/design/expanding-format-coverage.md).
- **Running the evals**: earth-mover's harness would largely port.
  [earth-mover-comparison.md](../docs/design/earth-mover-comparison.md).

## README install instructions: what was verified (2026-11-13)

- Both README recipes (personal links, per-project `rsync`) were run under a throwaway
  `HOME`: on a fresh machine, and on an old agent-skills-style install where
  `~/.gemini/config/skills` is itself a symlink to `~/.agents/skills`.
- On this hub, with the symlinked install, the skill is listed by Claude Code, by
  `copilot skill list`, and by `agy -p` (Antigravity CLI). Codex is not installed here,
  so its rows come from its docs only.
- Skill paths and commands were checked against each vendor's docs on 2026-11-13.
  Symlinks are documented only by Claude Code and Codex; for Copilot and Antigravity,
  symlinks work on this hub but the docs don't say.
- `gh skill install` (gh 2.90 and later) is only mentioned as coming, untested: the hub
  has gh 2.86. Eli will update `gh` in the py-rocket image later; then test it and fill in
  the README section.
