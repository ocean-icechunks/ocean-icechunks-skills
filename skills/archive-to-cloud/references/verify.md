# Step 4: verify the copies

Verify by downloading, not by trusting the upload. The upload script's `OK` means its own
size check passed; it does not prove the bytes a reader will get are the bytes on the source.

## Three checks

1. **Listing against the audit: every file, no downloads.** Counts and sizes per product match
   the source inventory, and every data file has a sidecar. A data file without a sidecar is an
   upload that never finished.
2. **A sampled byte check, by download.** Download a random sample over the public read path,
   compute each MD5 as the bytes arrive, and compare it with the sidecar (which was computed on
   the source before upload). From a JupyterHub this ran at about 50 MB/s; from AWS
   `us-west-2`, about 40 MB/s per file. Sample size is a judgement: tens of files per product is
   cheap; check everything when the product is small or the stakes are high.
3. **Again after any move.** A server-side copy to a new layout is a new copy: run checks 1 and
   2 on the new prefix before purging the old one.

Run downloads from a machine other than the provider's server, so they use your bandwidth, not
theirs.

## `scripts/verify_copy.py`

Standard library only (Python 3.8 or newer; tested with 3.12, not 3.8). Works against any
public bucket that answers an anonymous path-style S3 `ListObjectsV2`. Tested 2026-11-13 on
the PacIOOS copies on Source Cooperative (listings and a sampled download) and, for listing
only, on a public NODD bucket (`https://s3.us-east-1.amazonaws.com/<bucket>/<prefix>/`).

```bash
# 1. listing only: sidecars present, and counts and sizes against the source inventory
python3 scripts/verify_copy.py https://data.source.coop/<account>/<prefix>/ --list-only \
    --manifest source-inventory.tsv

# 2. a random 20 files, downloaded and checked against their .md5 sidecars
python3 scripts/verify_copy.py https://data.source.coop/<account>/<prefix>/ --sample 20

# every file
python3 scripts/verify_copy.py https://data.source.coop/<account>/<prefix>/
```

- The manifest is the audit's listing of the source, one `relative/path<TAB>size` per line,
  paths relative to the same folder as the prefix. On the source machine:
  `find . -type f -name '*.nc' -printf '%P\t%s\n' | sort > source-inventory.tsv`.
- `--glob` picks the data files (default `*.nc`; repeat it for `*.h5` and others). Anything else
  under the prefix, such as a store in `icechunk/`, is ignored.
- One line per file: `OK`, `BAD` (bytes differ; upload again), `NO-MD5` (no sidecar), and with a
  manifest `MISSING` (on the source, not copied), `EXTRA` (copied, not on the source) and `SIZE`
  (sizes differ). Exit status 1 if there is any problem.
- `--seed` makes a sample repeatable, so a second person can re-check the same files.
- Keys are listed anonymously; nothing needs or sees credentials.

## What a passing check does not prove

- **That the source was right.** The MD5 sidecar is taken from the source as it was at upload
  time. A file that was already truncated on the source will verify perfectly. The audit's
  size outliers and open failures are the check for that.
- **That the files read as NetCDF.** Open a few copies with xarray (or `ncdump -h` over a
  download) before building a store over them. In PacIOOS the first store build was to do
  that; until then the bytes were verified by MD5 only.
- **That they are still unchanged later.** Nothing here watches for a later overwrite. The
  copy script's never-overwrite rule is the protection; `change-detection.md` covers the rest.
