# Step 3: write and run the copy

This skill does not ship an upload script. Sources and destinations differ too much, and the
one script it is drawn from has been used once. Write one for the job, to the contract below.
The worked example is `upload/` in
[ocean-icechunks/pacioos](https://github.com/ocean-icechunks/pacioos/tree/main/upload):
`upload_to_source_coop.sh` (the copy), `upload_over_ssh.sh` (driving it over SSH) and
`README.md`. Read them; do not copy them blindly. They hard-code PacIOOS folders and Source
Cooperative settings.

## Decide where the copy runs

| Where | When | Measured (PacIOOS, 2026-11) |
|---|---|---|
| **On the machine that holds the files**, run by the provider's staff | The end goal, and the only sensible route for a daily top-up | 10–20 MB/s per file through a nearby Cloudflare edge |
| **On that machine, driven over SSH** by someone with a read-only login | A first bulk copy, done for the provider | Same speed; nothing left on the server but one approved binary |
| **Pulled to another machine** over SSH, or through THREDDS or HTTP | Only when nothing else is allowed | Under 1 MB/s over SSH to a mainland machine, about 1 MB/s through THREDDS; months for a few TB |

Distance to the destination's edge dominated everything else. Run the copy where the files are.

## The contract every copy script meets

**Per file, decide one state, from a listing of the destination taken at the start:**

| State | Test | Action |
|---|---|---|
| Done | Its sidecar exists and the copy's size equals the source's | Skip, silently counted |
| **Changed** | Its sidecar exists, but the size differs (or the mtime, if you record it) | Report `CHANGED`, **touch nothing**, set a distinct exit status |
| Too new | Modified within `MIN_AGE` (PacIOOS used 120 min) | Skip; it may still be being written |
| To do | Anything else, including a copy with no sidecar (an interrupted upload) | Upload it |

**Uploading one file:**

1. Compute the MD5 on the source, at low priority (`nice -n 19 ionice -c3`).
2. Upload the bytes unchanged, at low priority. Reading the file for the checksum first means the
   upload mostly reads it from the page cache, so the disk is read once.
3. Read back the uploaded object's size and compare it with the source.
4. **Only then** upload the sidecar, `<file>.md5`, in `md5sum` format (`<md5>  <name>`), so
   anyone can check a download with `md5sum -c`. A sidecar means "this upload finished".

**Whole run:**

- **Never overwrite.** No code path writes to a key that has a sidecar. Where the tool offers a
  second guard, use it as well (rclone's `--immutable`; S3 conditional writes,
  `If-None-Match: *`). Neither has been tested on Source Cooperative.
- **A failed destination listing stops the run.** It must not look like an empty destination,
  because then every file is "to do". (The PacIOOS script swallows listing errors with
  `|| true`. Avoid that.)
- **Resumable by construction:** stopping at any moment and rerunning carries on, because
  state comes only from the destination listing and the sidecars.
- **One line per file:** `OK`, `SKIP`, `FAIL` or `CHANGED`, with size, MD5 and speed for `OK`.
  Progress is then `grep -c '^OK'`.
- **Distinct exit statuses.** PacIOOS used 0 (done), 2 (some failed: rerun), 4 (some changed: a
  person decides). A driver must not loop on 4.
- **`--dry-run`:** list what would be uploaded, and the counts in each state, with no writes.
- **`MAX_HOURS`:** stop *starting* files after this long, so a run ends cleanly before its keys
  expire.
- **`PARALLEL`:** files at once. Two used about 20% of one core, 170 MB of memory and 30–50 MB/s
  of outgoing traffic on the PacIOOS server.
- **A product table** (name → source folder, version label) at the top, plus a
  `name=/folder` command-line override for one-off products.
- **Write nothing on the source machine.** With rclone, configure the remote entirely through
  environment variables and set `RCLONE_CONFIG=/dev/null`, so no config file is written.

## Tools

- **rclone** is one static binary: no installation, no root. Download the Linux zip from
  rclone.org, check it against the published `SHA256SUMS`, and put it where the provider
  approved (PacIOOS: one binary in `/tmp`). Destination settings are in `destinations.md`.
- Other S3 clients (`aws s3 cp`, `s5cmd`) would work for an ordinary S3 bucket but have not been
  used for this. Source Cooperative needs the rclone settings in `destinations.md`; whether other
  clients can be configured equivalently is untested.

## Driving it over SSH, without leaving anything behind

From `upload_over_ssh.sh`:

- **Make short-lived keys on your own machine** for each run, and send them, the settings and
  the upload script down the SSH connection's stdin (`ssh host bash -s`). Nothing is saved on
  the server.
- **Wrap the sent script in `{ … }` and start it with `exec </dev/null`.** Bash then reads the
  whole script before running any of it, and nothing the script runs can swallow the rest of
  the stream.
- `ssh -o BatchMode=yes -o ServerAliveInterval=60`: fail rather than prompt, and notice a dead
  connection.
- **Size each run to the keys.** Ask the credential tool when the current keys expire (print
  only the expiry, never the keys), set `MAX_HOURS` to that minus half an hour, and start the
  next run with fresh keys. With under an hour left, wait for them to expire and get new ones.
- **Stop on `CHANGED`** (exit 4) and on a failed login (PacIOOS: exit 3, "log in again"), and
  give up after `MAX_RUNS`. Retry after anything else; resumability makes a dropped connection
  cheap.
- **Keep the logs on the driving machine, outside any repository.** They name the server.

## Running for days

- Start the driver detached: `setsid nohup ./driver.sh … > console.txt 2>&1 &`, with the
  console file gitignored. A hub restart or a laptop going to sleep then does not matter.
- Check progress by counting `OK` lines in the log, not by watching the terminal.
- Order the work by what the provider says matters most, and copy the core products first.
  Leave decisions about trimming years or adding big products until the core is up.
- **A growing product needs a daily top-up.** The same script, run once a day after the model
  runs finish, uploads just the new files. Where the source keeps only recent days, a missed
  day is lost from the source for good, so the top-up needs monitoring.

## Test before the real run

1. Read the script against the contract above.
2. Run `--dry-run` against the real source and destination, and compare its counts with the
   audit.
3. Upload one file to a **scratch prefix**, then check it with `scripts/verify_copy.py`.
4. Interrupt a run partway and rerun it: the finished files are skipped and an interrupted
   upload (no sidecar) is redone.
5. In the scratch prefix, make a copy whose size differs from its source and check that the
   script reports `CHANGED`, leaves it alone and exits with the "changed" status.
6. Ask before pointing it at the real destination.
