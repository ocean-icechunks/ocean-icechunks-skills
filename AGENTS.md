# Instructions for coding agents

These instructions apply to any coding agent working in this repository. Edit
`AGENTS.md`, not `CLAUDE.md`: `CLAUDE.md` holds only `@AGENTS.md`, which makes
Claude Code read this file, and other agents read `AGENTS.md` directly.

This repository holds the Ocean Icechunks skills: reusable agent instructions
for building, checking and documenting Icechunk stores of ocean data and for the
file work around them. Task-specific workflows belong in the individual skills,
not in this file.

- Read the relevant issue and the existing skill before editing.
- Session state is in `agent/handoff.md`; design decisions and their evidence
  are in `docs/design/`. Read the handoff first.
- Keep to the open Agent Skills convention, and keep the repository usable by
  any agent, not one product.
- Keep every skill portable, self-contained, and independently installable.
- Use progressive disclosure: metadata first, a concise `SKILL.md`, and detailed
  references only as needed.
- Clearly distinguish stable guidance from experimental or provisional
  findings.
- Cite evidence for changes based on external documentation or example
  repositories. Report unresolved uncertainty rather than inventing a standard.
- Validate every modified skill (`ruby .github/scripts/validate_skills.rb`), test
  every modified script, and update the evaluations when behavior changes.
- Avoid unrelated changes.
- Never expose credentials, private endpoints, controlled data, sensitive NOAA
  information, or other secrets.
- Do not modify production services, repositories, datasets, or object stores
  while validating a skill.

Contribution conventions are in this file and `CONTRIBUTING.md`; reusable task
instructions belong under `skills/`.
