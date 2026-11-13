# Step 1: audit the source

Read-only. The audit decides what gets copied and how it is laid out, and it is
the baseline the copies are checked against afterwards. It is also where most of
the surprises are found: in both archives this skill is drawn from, the files on
disk disagreed with the provider's public description.

## Survey everything, not just what was asked about

List every folder you can read, not only the products named in the request.

What turned up in practice:

- **PacIOOS (2026-11):**
  - a hindcast 3× larger than the public catalogue implied (3.37 TB, not about 1.1 TB);
  - an unexplained set of about 3,200 "replacement" files, most with the same names as
    originals but in a different format (compressed HDF5 instead of NetCDF-3);
  - other regions' archives (Samoa, western Pacific, seven forecast regions);
  - folders that keep only the last 7 days.
- **CEFI (2026-09):** 46 release directories, many of them superseded releases with far
  fewer files sitting beside the current one, plus stray files (`all.json`, `ocean_stati.json`)
  in data folders.

Report what you found that nobody asked about. The user decides what is in scope.

## Per product, record

| Fact | How to get it | Why it matters |
|---|---|---|
| File count, total bytes, date range | `find -printf '%P\t%s\t%T@\n'`, or an object listing | Sizes the transfer; the baseline for verification |
| Naming pattern, and files that break it | Parse every name with one pattern and list the failures | Misnamed or stray files are findings |
| Format, **from the file's own header** | The magic number (`CDF\x01`/`CDF\x02` NetCDF-3, `\x89HDF` HDF5), then `ncdump -hs` or h5py | THREDDS, ERDDAP and published docs get this wrong |
| Compression and native chunks | `ncdump -hs` (`_Storage`, `_ChunkSizes`, `_DeflateLevel`) | Facts the virtual-icechunk skill needs, gathered once |
| Global attributes, especially a **version** | `ncdump -h` | Decides whether version folders are needed (`layout.md`) |
| When the files were written | The mtime histogram | All at once means a reprocessed version; daily means a growing product |
| How much history is kept | Earliest file per folder, compared over two days | A trimmed folder means a missed day is lost for good |
| Empty, zero-length or truncated files | Sizes far below the product's normal size; files that fail to open | Copy them as they are, but list them |
| Sidecar files (Kerchunk JSON, `.md5`, indexes) | Match each sidecar to its data file **by the path it contains**, not by its name | CEFI had 568 JSONs with the first character of the name dropped |

Two facts from PacIOOS show why headers beat catalogues:

- The forecast and hindcast were **NetCDF-3**, though the public servers implied HDF5.
- The reanalysis files carry **no version**: their only global attributes are `author`,
  `history` and `title`. "v2.0" exists only in the THREDDS description.

## Ask the provider

Ask these before laying out the copy, and write the answers down:

- Which folder is authoritative, when two look alike?
- Are files ever corrected or rewritten in place? Do the replacements keep the same name and
  size?
- How will a new version arrive: a new folder, or over the old files?
- Can older years be dropped, and is anything due to be deleted from the server?
- What load is acceptable: a speed cap, quiet hours, how many files at once?
- May the machine connect out to the destination (HTTPS, port 443)?

## Method: scanning a large archive without hurting anything

From the CEFI audit (13,307 NetCDFs, 37 TB, on a hub with a 3.9 GB memory cap):

- **Read metadata only.** Read the headers and small coordinate values; never read whole data
  variables. Write one JSON line per file, so the scan can be resumed and re-analysed without
  being repeated.
- **Make every scanner resumable.** Skip files already in the output. S3 reads occasionally
  stalled for minutes, so set connect and read timeouts and retry.
- **Count your workers against the memory cap.** More than about 6 worker processes hit the OOM
  killer on that hub. A killed `multiprocessing.Pool` worker hangs the pool for ever, because
  its task is lost. If a scan stalls with idle workers, check `oom_kill` in
  `/sys/fs/cgroup/memory.events`.
- **Never use h5py's `visititems` to walk a file.** It walks every chunk index: 300 s per
  43 GB file instead of 1.6 s. Walk the groups yourself.
- **Do not `pkill -f` a pattern that also appears in your own command line.** It kills the
  shell running it. Kill by PID.
- **Keep the scan output out of git** if it is large (the CEFI header scan was 500 MB); commit
  the scripts and a summary table instead.

On the provider's own server, scan with `nice -n 19 ionice -c3`, one file at a time, and only
what you need: a header read touches a few kilobytes, a checksum reads the whole file (do that
during the copy, once, not in the audit).

## Contradictions go back into the notes

When the files contradict an earlier note, a catalogue entry or the provider's documentation,
correct the note where it is, with the date and the evidence. PacIOOS's probe note gained a
correction box at the top rather than a second, conflicting note.

## Hand-off to the virtual-icechunk skill

If a virtual store will be built over the copies, the audit has already gathered most of what
that skill's research step needs: format, chunks, codecs, the time axis, and which variables
sit in which files. Record them in the audit output. The *judgement* about whether they can be
virtualized (chunk grids that do not tile, append misalignment, Kerchunk byte-range agreement)
belongs to that skill, not this one.
