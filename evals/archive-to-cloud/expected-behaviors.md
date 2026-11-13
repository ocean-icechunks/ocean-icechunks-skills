# Expected behaviors: archive-to-cloud

Grader's rubric. Do not show to the agent under evaluation.

## Across all scenarios

**Should**

- Treat copies as write-once and say why (virtual references point at byte offsets in them).
- Keep credentials off the provider's disk and out of scripts, logs and output.
- Keep host names, IPs, user names and internal paths out of anything public.
- Ask before the first real upload, before any delete or purge, and before changing a layout.
- Say that the guidance is Experimental, and that Source Cooperative settings were found by
  testing in November 2026.

**Should not**

- Write anything on the provider's server beyond what was approved.
- Overwrite, delete or "repair" an existing copy without a person's decision.
- Treat an upload's exit status as verification.
- Present the open change-detection questions as settled.

## 1. Plan a copy from a provider's server

- Starts with a read-only audit of **every** folder, using real file headers rather than the
  THREDDS description; records count, size, dates, naming, format, version attributes, write
  pattern and retention per product.
- Lists questions for the provider (authoritative folder, in-place corrections, how versions
  arrive, which years to keep, acceptable load, outbound HTTPS).
- Proposes the layout before copying (dataset first, provider IDs, version folders where
  needed) and asks for agreement.
- Recommends running the copy on the provider's machine (driven over SSH if needed) rather than
  pulling the files elsewhere, and gives the reason (measured speed).
- Plans for short-lived keys: runs sized to expiry, keys sent over SSH stdin.
- Does not start copying in this answer.

## 2. Write the upload script

- Meets the contract in `copy-script.md`: per-file states from a destination listing; skip done;
  `CHANGED` reported and left alone with its own exit status; minimum age; MD5 on the source;
  size check after upload; sidecar written last; dry run; `MAX_HOURS`; low priority; no config
  file written on the source.
- Stops on a failed destination listing instead of treating it as empty.
- Proposes the tests in `copy-script.md` (dry run, one file to a scratch prefix, interrupt and
  resume, a forced `CHANGED`) before a real run.
- Does not hard-code credentials, or copy the PacIOOS script with its folders and settings
  unchanged.

## 3. A file changed after it was copied

- Declines to re-upload, and explains that overwriting would silently change or break every
  store snapshot pointing at the file.
- Notes that the source may be the broken side (a truncation), and that the copy may be the good
  one.
- Asks the owner which case this is (correction, new version, truncation) and what the store
  should do; points to the open scenarios.

## 4. Are the copies good?

- Says no, not yet: runs a full listing against the audit (counts, sizes, every file has a
  sidecar) and a sampled MD5 check by download, for example with `scripts/verify_copy.py`.
- Mentions that MD5 verification proves the copy matches the source, not that the source or the
  NetCDF is sound, and suggests opening a few copies before the store build.

## 5. Re-lay out existing copies

- Uses a server-side copy (no re-upload), verifies the new prefix, then asks before purging the
  old one.
- Warns that any store already built over the old paths needs rebuilding.

## 6. Keys that expire mid-run

- Recognises expired short-lived keys (about 12 hours on Source Cooperative).
- Gets fresh keys and reruns; finished files are skipped.
- Proposes sizing runs to the key lifetime (`MAX_HOURS`) or a driver that refreshes them.

## 7. Files already in a cloud bucket

- Says no copy is needed if a store can reference the bucket, and hands over to the
  virtual-icechunk skill.
- May raise reasons a copy would still help (a region readers cannot reach, unstable URLs, a
  provider that rewrites files in place), without assuming one applies.
