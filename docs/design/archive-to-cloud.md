# archive-to-cloud skill — design decisions

The skill audits a provider's NetCDF/HDF5 archive, copies it unchanged to object storage, and verifies the
copies. Added in #8 (merged 2026-11-13; #4 closed). The full reasoning is in the #8 PR body. Evidence came from
ocean-icechunks/pacioos (`upload/`, `docs/design/`, pacioos#2), noaa-nwfsc/cefi-icechunks (`audit/`, notes),
and ocean-icechunks/icechunks (AGENTS.md, notes).

## Decisions Eli made (2026-11-13), not to be silently revisited

- **Only the verify script is bundled.** No upload scripts: `copy-script.md` is a contract for writing one per
  job, with PacIOOS `upload/` as the worked example. Don't "complete" the skill by importing the PacIOOS scripts.
- **The audit is split by job.** Inventory and integrity checks live here; whether files can be virtualized
  stays in `virtual-icechunk`. Don't duplicate chunking guidance.
- **`change-detection.md` is Provisional** until ocean-icechunks/pacioos#2 settles; harvest the answers from there.

## Testing status

- `verify_copy.py` was tested on Python 3.12 only. Listing and sampled MD5s were run on the PacIOOS copies, and
  listing on the CEFI NODD bucket. The evals are written, not run.
- Found on the way: ocean-icechunks/pacioos#9 (the upload script hid a failed listing and could overwrite
  copies). PacIOOS's copy, their fix (PR pacioos#24). What it taught the skill is #15, still open.
