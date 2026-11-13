# Ocean Icechunks skills

Agent skills for building, checking and documenting
[Icechunk](https://icechunk.io) stores of ocean data, and for the file work
around them. A skill is a folder of instructions that a coding agent (Claude
Code, Codex, GitHub Copilot, Antigravity and others) loads on its own when what
you ask matches it.

## Skills

| Skill | Description | Status | Maintainer |
| --- | --- | --- | --- |
| [virtual-icechunk](skills/virtual-icechunk/) | Research, build, validate, document, and audit virtual Icechunk stores that reference remote NetCDF/HDF5 files in place. | Experimental | [@eeholmes](https://github.com/eeholmes) |

A skill is added to this table only when its directory and valid `SKILL.md`
exist. Maturity levels: **Experimental** (exploratory, may change
substantially), **Provisional** (useful in practice, still gathering evidence),
**Stable** (validated and maintained), **Deprecated** (kept for transition).

## Quick install

Clone this repository once, then link the skill into the folder your agent
reads, so that a `git pull` updates it:

```bash
git clone https://github.com/ocean-icechunks/ocean-icechunks-skills ~/ocean-icechunks-skills

# Claude Code, every project on this machine
mkdir -p ~/.claude/skills
ln -s ~/ocean-icechunks-skills/skills/virtual-icechunk ~/.claude/skills/virtual-icechunk

# Codex, Antigravity and other agents that read ~/.agents/skills
mkdir -p ~/.agents/skills
ln -s ~/ocean-icechunks-skills/skills/virtual-icechunk ~/.agents/skills/virtual-icechunk
```

Restart the agent afterwards: skills are discovered when a session starts.

## Layout

```text
skills/<skill-name>/   the installable skill: SKILL.md plus references/
evals/<skill-name>/    evaluation scenarios, kept outside the installed bundle
docs/                  the evidence the skills were built from
docs/design/           design notes: decisions and why
agent/handoff.md       rolling state for agents working on this repository
```

## History

`virtual-icechunk` was developed in
[nmfs-opensci/agent-skills](https://github.com/nmfs-opensci/agent-skills) from
September to November 2026 and moved here with its git history
([ocean-icechunks/icechunks#46](https://github.com/ocean-icechunks/icechunks/issues/46)).
Issue and PR numbers in the older commit messages refer to that repository.

To propose a skill or a change, read [CONTRIBUTING.md](CONTRIBUTING.md) and use
the issue forms.

## Reuse and citation

This work is released under [CC0 1.0 Universal](LICENSE) and is free of known
copyright restrictions. You are free to use, copy, modify, and redistribute it
for any purpose, including commercially. Attribution is appreciated but not
required — you do not need to cite me or ask permission. (The files that came
from nmfs-opensci/agent-skills were under Apache-2.0 there; they are released
here under CC0.)
