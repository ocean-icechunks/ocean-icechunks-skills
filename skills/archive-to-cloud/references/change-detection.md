# When source files change after they were copied

**Provisional.** This is open work, tracked in
[ocean-icechunks/pacioos#2](https://github.com/ocean-icechunks/pacioos/issues/2). What is
settled is the rule; the procedures for most scenarios are not. Do not present any of the open
items below as decided. Raise them with the owner instead.

## Why it matters

A virtual Icechunk store holds byte offsets into the copies, not the data. Its snapshots and
tags version the *addresses*, not the *bytes*. If a copy is overwritten:

- if the store recorded each file's modification time or ETag, reads of that file fail;
- if not, reads silently return the new bytes at the old offsets.

So copies are write-once, and a changed source file is a decision for a person, never an
automatic re-upload.

## Settled

- The copy script never overwrites a finished copy. A difference is reported as `CHANGED`, with
  its own exit status, and left alone (`copy-script.md`).
- A new version of a product goes to a new version folder (`layout.md`). The old version's
  copies are not touched.
- A truncated or corrupted source never replaces a good copy. This is the same rule.

## Open

**The change signal.** A size check misses a same-size rewrite, and uncompressed model output on
a fixed grid is usually exactly the same size after reprocessing. The candidates:

| Signal | Cost | Catches |
|---|---|---|
| Size | Free (in the listing) | Truncation, format changes, most compressed rewrites |
| Source mtime, recorded at upload (in the sidecar, or a small file beside it) | Free afterwards | Any rewrite that updates mtime; misses a copy that preserves mtime |
| Checksum of the source | Reads every file again (1.2 TB for the PacIOOS reanalysis) | Everything |
| A notice from the provider | None, if they will do it | What they remember to announce |

None is chosen yet. Recording the source mtime at upload time costs nothing and is the likely
first step.

**The scenarios** (from pacioos#2; work through each with the provider):

1. New daily files: upload them and append to the store. The store-update half is the open
   part.
2. A new version in a new folder, the old one kept: upload to the new version folder, a new
   snapshot, a new tag; `main` moves.
3. A new version written over the old files, same names: the script must notice (see the change
   signal), refuse, and someone routes the files to a new version folder.
4. A new version that changes the period: some names new, some reused, some gone.
5. A new version that changes variables, levels or the grid. Working rule so far: a changed
   model is a new product.
6. Single files corrected in place: not a new version. Options: a new path for the corrected
   file and a store commit that repoints those chunks, or keep the original and document the
   correction.
7. Retiring an old version: delete its tag, expire its snapshots, garbage-collect the store,
   and only then delete its files. Garbage collection does not touch the copies. Who decides,
   and how users are told, is open.
8. A file shrinks or is truncated at the source: the copy is good and the source is bad. Report
   it to the provider; leave the copy.

## What to do now

When a run reports `CHANGED`: stop, list the files with their old and new sizes (and mtimes if
recorded), and ask the owner which scenario this is. Do not re-upload, delete or move anything
until they answer. Record the answer in the project's issue for it, and if it settles one of the
open items above, propose updating this file through the skill's Learn path: an issue on the
skills repository with the evidence.
