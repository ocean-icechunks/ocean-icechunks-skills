---
name: archive-to-cloud
description: Audit a data provider's NetCDF or HDF5 archive, copy the files unchanged to object storage (Source Cooperative, S3, NODD or similar), and verify the copies byte for byte. Use when asked to survey or inventory a provider's file archive before copying it, plan or lay out a copy to a cloud bucket, write or adapt an upload script that runs on someone else's server, run a multi-day transfer with short-lived keys, check that copies match their originals, move copies to a new layout, or decide what to do when a source file changes after it was copied. Comes before a virtual Icechunk store whenever the source files are not already in a bucket the store can reference; building the store itself is the virtual-icechunk skill.
---

# Archive to cloud: audit, copy, verify

The job is to put a provider's original files, **byte for byte unchanged**, into
object storage where anyone (and any virtual Icechunk store) can read them. It
is a different job from building a store, with different risks: someone else's
server, write credentials, a transfer that runs for days, and copies that other
things will depend on.

**Status: Experimental.** This is drawn from one full copy (PacIOOS Hawaiʻi
models, about 3.8 TB, to Source Cooperative, November 2026) and one read-only
audit (CEFI regional MOM6, about 37 TB on NODD). Source Cooperative details were
found by failure and may change. Other destinations are untested here. Say which
parts you are relying on when you use them.

## Rules that do not bend

1. **Copies are write-once.** Icechunk versions a store, not the files its
   virtual references point at. Overwriting a copied NetCDF silently changes
   or breaks every snapshot that points into it. A copy script never
   overwrites a finished copy; it reports the difference and stops for a
   person. A truncated or corrupted source must never "fix" a good copy.
2. **You are a guest on the provider's server.** Write nothing there that has
   not been approved, read each file once at low priority, and keep host names,
   IP addresses, user names and internal paths out of public issues, commits
   and logs that get committed.
3. **Credentials never touch the provider's disk.** Pass them over SSH stdin or
   environment variables, keep them out of scripts, logs and cell output.
4. **A copy is trusted only after it has been verified by downloading it.** An
   upload's exit status is not verification.
5. **Do not write to a production bucket to test.** Test against a scratch
   prefix, and ask before the first real upload, before any delete or purge, and
   before any change to an existing layout.

## The order

Each step gates the next. Show the user the output of steps 1 and 2 before any
byte is copied.

| Step | Output | Read |
|---|---|---|
| 1. **Audit the source** (read-only) | An inventory per product, the contradictions found, and questions for the provider | `references/source-audit.md` |
| 2. **Decide the layout** | The destination path for every product and version, agreed before the first upload | `references/layout.md` |
| 3. **Write and run the copy** | A copy script built for this source and destination, a dry run, a one-file test, then the full run | `references/copy-script.md`, `references/destinations.md` |
| 4. **Verify the copies** | A full listing reconciled with the audit, and a sampled MD5 check by download | `references/verify.md`, `scripts/verify_copy.py` |
| 5. **Record** | A README beside the scripts, and an issue for what is still undecided | below |

When a file changes at the source after it was copied (a correction, a new
version, a truncation), read `references/change-detection.md`. It is
**Provisional**: the scenarios are listed, not settled.

## Step 5: record

Beside the copy scripts, in the project repository (not in this skill), write a
README that a provider's staff could follow without you:

- a products table: source folder, destination prefix, file count, size, and
  the date the counts were taken;
- the layout and the reason for any version folders;
- how to rerun the copy (including the daily top-up, if the product grows) and
  how to check the copies;
- why each destination-specific setting is there, so nobody "cleans it up".

Open an issue for every decision left to the provider or the owner: versioning,
which folder is authoritative, which years to keep. Keep the logs that name the
provider's server outside any repository.

## Where this skill stops

- **The files are already in a bucket a store can reference** (NODD, a public
  S3 bucket, a DAAC bucket): there is nothing to copy. Use the virtual-icechunk
  skill. Its research step still applies the audit ideas here.
- **Whether files can be virtualized** (chunk shapes, concatenation and append
  alignment, codecs, Kerchunk agreement) belongs to the virtual-icechunk skill.
  This skill's audit records the facts that skill needs, and points there.
- **Rechunking or reformatting** is not a copy. If the provider wants rewritten
  files, that is a separate, explicitly approved job; the unchanged originals
  should still be kept.
