# Ocean Icechunks skills

Agent skills for building, checking and documenting
[Icechunk](https://icechunk.io) stores of ocean data, and for the file work
around them. They work with any coding agent that supports the open
[Agent Skills](https://agentskills.io/specification) format, including Claude
Code, GitHub Copilot, OpenAI Codex and Google Antigravity.

The skills focus on **[VirtualiZarr](https://virtualizarr.readthedocs.io) +
Icechunk**: virtual stores that hold only Zarr metadata and references to
NetCDF/HDF5 files left where they are. They do not cover materialized stores
that copy and rechunk the data. `archive-to-cloud` is the step before a virtual
store, when the files first need to be copied somewhere a store can reference.

## Skills

| Skill | What it covers | Status | Maintainer |
| --- | --- | --- | --- |
| [virtual-icechunk](skills/virtual-icechunk/) | Research, build, validate, document, and audit virtual Icechunk stores that reference remote NetCDF/HDF5 files in place. | Experimental | [@eeholmes](https://github.com/eeholmes) |
| [archive-to-cloud](skills/archive-to-cloud/) | Audit a provider's NetCDF/HDF5 archive, copy it unchanged to object storage, and verify the copies. Comes before a virtual store when the files are not already in a bucket it can reference. | Experimental | [@eeholmes](https://github.com/eeholmes) |

Status levels: **Experimental** (exploratory, may change substantially),
**Provisional** (useful in practice, still gathering evidence), **Stable**
(validated and maintained), **Deprecated** (kept for transition).

## What a skill is

A skill is a folder of instructions, a `SKILL.md` plus reference files, that
your coding agent reads when the task calls for it. You do not run it or call
it like a function. At the start of a session the agent reads each installed
skill's one-paragraph description. When what you ask matches one, the agent
loads that skill and follows it for the rest of the task, opening the reference
files only as it needs them.

So you use a skill by **describing the task in plain language**, for example
"build a virtual Icechunk store for these files". You do not need to name the
skill. If it doesn't kick in, you can ask for it by name (see
[Check that it worked](#check-that-it-worked)).

## Install

Pick one:

- **Personal**: the skill is available in every project on your machine, and
  a `git pull` keeps it up to date. Best for most people.
- **Per project**: the skill is committed into one repository, so everyone who
  clones that repository gets it. Best for a shared store repository.

### Personal (all your projects)

Clone this repository once, then link the skills into the folder each agent
reads:

```bash
git clone https://github.com/ocean-icechunks/ocean-icechunks-skills ~/ocean-icechunks-skills

for dir in ~/.claude/skills ~/.agents/skills ~/.gemini/config/skills; do
  mkdir -p "$dir"
  for skill in virtual-icechunk archive-to-cloud; do
    ln -sfn ~/ocean-icechunks-skills/skills/$skill "$dir/$skill"
  done
done
```

The three folders cover the four agents:

| Agent | Personal skills folder |
| --- | --- |
| Claude Code | `~/.claude/skills/` |
| OpenAI Codex | `~/.agents/skills/` |
| GitHub Copilot (CLI, VS Code agent mode, and other IDEs) | `~/.agents/skills/` (or `~/.copilot/skills/`) |
| Google Antigravity | `~/.gemini/config/skills/` |

Linking a folder you don't need does no harm, so the loop above simply links
all three. The `mkdir -p` matters, because `ln` fails confusingly if the
folder doesn't exist yet. If you previously *copied* the skill into one of these
folders, delete that copy first, or `ln` will put the link inside it.

If you installed it from `nmfs-opensci/agent-skills` before November 2026, run
the loop above: `ln -sfn` replaces the old links.

### Per project (one repository)

Copy the skill into the repository and commit it. Collaborators then get it when
they clone, with nothing to install:

```bash
cd /path/to/your-repo
mkdir -p .agents/skills .claude/skills
rsync -a --delete ~/ocean-icechunks-skills/skills/virtual-icechunk/ .agents/skills/virtual-icechunk/
rsync -a --delete ~/ocean-icechunks-skills/skills/virtual-icechunk/ .claude/skills/virtual-icechunk/
git add .agents/skills .claude/skills
git commit -m "Add the virtual-icechunk skill from ocean-icechunks-skills"
```

Repeat the two `rsync` lines with `archive-to-cloud` in place of
`virtual-icechunk` if the project also copies source files to object storage.

`.agents/skills/` is read by Codex, Copilot and Antigravity, and `.claude/skills/`
by Claude Code (and also by Copilot). If everyone on the project uses the same
agent, you only need its folder. Use copies, not symlinks, in a repository:
a symlink breaks for anyone who doesn't have `~/ocean-icechunks-skills`, and on
Windows.

Use either the personal install or the per-project one, not both, so the agent
doesn't see two copies of the same skill.

**Coming: `gh skill install`.** GitHub CLI 2.90 and later can install a skill
straight from a repository (`gh skill install ocean-icechunks/ocean-icechunks-skills
virtual-icechunk`), and update it with `gh skill update`. It has not been tested
with these skills yet. The hub image will get a newer `gh` in a later update, and
this section will be filled in then.

### Check that it worked

Start a new session in your agent and ask for something the skill covers. To
check directly:

| Agent | See installed skills | Ask for the skill by name | Pick up a newly installed skill |
| --- | --- | --- | --- |
| Claude Code | `/skills` | `/virtual-icechunk` | Usually automatic; otherwise `/reload-skills` or a new session |
| Copilot CLI | `/skills list`, or `copilot skill list` in a terminal | `/virtual-icechunk` | `/skills reload` |
| Codex | `/skills` | `$virtual-icechunk` | Usually automatic; otherwise restart Codex |
| Antigravity | type `/` in the CLI (each skill is a slash command); the Customizations menu in the IDE | `/virtual-icechunk` | `/skills reload` in the CLI, or a new conversation |

If it still doesn't appear, check that `SKILL.md` sits directly inside the
`virtual-icechunk` folder, not one level deeper:

```bash
ls ~/.agents/skills/virtual-icechunk/SKILL.md
```

## Keep it up to date

- **Personal install:** `git -C ~/ocean-icechunks-skills pull`. The links point
  at the clone, so every agent picks up the new version, and the next session
  uses it.
- **Per project:** rerun the two `rsync` lines above, review the diff, and
  commit. A project copy stays at the version you copied until you do this,
  which is useful when you need a build to stay reproducible.

Changes are listed in the
[commit history](https://github.com/ocean-icechunks/ocean-icechunks-skills/commits/main).
To hear about them, watch the repository on GitHub (Watch → All activity).

## Example prompts

Describe the job; the agent picks the skill and the right part of it.

**Look before you build**

```text
I want a virtual Icechunk store for the PacIOOS ROMS reanalysis. Research the
source files and write a plan before any code.

Does this THREDDS server expose the real NetCDF files, or only OPeNDAP?
```

**Build**

```text
Write a smoke-test notebook that builds a small virtual store from three of
these files and reads real data back.

The smoke test passed. Turn it into a production build script.

Write the README and a loading example for this store.
```

**Check or fix an existing store**

```text
Review this older Icechunk repository and tell me what to modernize.

Why is this store so slow to open?

The viewer shows coordinates but no data. Is this a CORS problem?
```

**Capture what you learned**

```text
We just finished this build. What did it teach that the virtual-icechunk skill
should know?
```

The skill builds in a set order (plan → smoke test → production → docs) and
stops for your review between steps. Expect it to ask questions and show you a
plan before it writes build code.

## Report a lesson back

The skill improves through real builds, and it only knows what someone has
written into it. When a build teaches you something, such as a provider quirk, a
check that would have caught a bug, or a place where the skill was wrong:

1. **Ask the agent to sum it up.** At the end of a build, ask what the work
   taught (the last example prompt above). The skill's *Learn* step sorts each
   lesson: a core workflow change, something true of one source or
   destination, a known issue, or a one-off. It does not edit the skill unless
   you ask it to.
2. **Write it down in your store repository first**, in its notes or README,
   with the evidence: which dataset, which package versions, what you observed.
3. **Bring it here.** Open an
   [Update skill](https://github.com/ocean-icechunks/ocean-icechunks-skills/issues/new?template=update-skill.yml)
   issue with that evidence, or a pull request that edits the skill. An agent
   can draft either; the issue form asks for the evidence and a realistic test
   scenario.

One success is an anecdote. A lesson becomes core guidance only once it has
held on more than one dataset, provider or destination. Until then it goes in
the section for that source, or is noted as provisional. "This failed" is
worth reporting even when you are not sure it always fails; say which it is.

To propose a new skill, use the
[New skill](https://github.com/ocean-icechunks/ocean-icechunks-skills/issues/new?template=new-skill.yml)
form. [CONTRIBUTING.md](CONTRIBUTING.md) has the conventions.

## What's in this repository

```text
skills/<skill-name>/   the installable skill: SKILL.md plus references/
evals/<skill-name>/    test scenarios, kept outside the installed bundle
docs/                  the evidence the skills were built from, and a comparison with other guides
docs/design/           design notes: decisions and why
agent/handoff.md       rolling state for agents working on this repository
```

`virtual-icechunk` was developed in
[nmfs-opensci/agent-skills](https://github.com/nmfs-opensci/agent-skills) from
September to November 2026 and moved here with its git history
([ocean-icechunks/icechunks#46](https://github.com/ocean-icechunks/icechunks/issues/46)).
Issue and PR numbers in the older commit messages refer to that repository.

## Reuse and citation

This work is released under [CC0 1.0 Universal](LICENSE) and is free of known
copyright restrictions. You are free to use, copy, modify, and redistribute it
for any purpose, including commercially. Attribution is appreciated but not
required — you do not need to cite me or ask permission. (The files that came
from nmfs-opensci/agent-skills were under Apache-2.0 there; they are released
here under CC0.)

## More resources

These skills come from lessons learned building a variety of VirtualiZarr +
Icechunk stores of ocean data. Others have written guides and tools for related
work, including materialized stores and pipelines at larger scale.
[Four Icechunk playbooks](docs/other-icechunk-playbooks.md) summarizes how they
differ from these skills and what they share. Bringing their lessons into these
skills is an open issue,
[#10](https://github.com/ocean-icechunks/ocean-icechunks-skills/issues/10).

- [dynamical.org dataset development guide](https://github.com/dynamical-org/reformatters/blob/main/docs/dataset_development_guide.md):
  how dynamical.org's agents take a weather dataset from source exploration to a
  published Icechunk store, virtual and materialized.
- [Earthmover `icechunk-datacube-ingestion` skill](https://github.com/earth-mover/agent-skills/tree/main/icechunk-datacube-ingestion):
  an agent skill for ingesting datacubes into Icechunk or Arraylake, organized by
  file format (HDF5, NetCDF3, GRIB, TIFF, Kerchunk, Zarr).
- [Development Seed `virtualizarr-data-pipelines`](https://github.com/developmentseed/virtualizarr-data-pipelines):
  a template repository for VirtualiZarr + Icechunk pipelines on AWS, with a
  parallel backfill and processing of new files as they arrive.
- [dynamical.org binary rounding](https://github.com/dynamical-org/reformatters/blob/main/src/reformatters/common/binary_rounding.py):
  rounds float32 values to fewer mantissa bits so materialized chunks compress
  better. It does not apply to virtual stores, which reference the provider's
  bytes unchanged.
