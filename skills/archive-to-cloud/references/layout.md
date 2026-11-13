# Step 2: decide the layout before the first byte

Copies get referenced by stores, linked from READMEs and downloaded by scripts, so their paths
should not change. Moving them later is possible (a server-side copy, see `destinations.md`),
but it is a second job, and every store built in between has to be rebuilt.

## The pattern used so far

Dataset first, using the **provider's public dataset IDs** (the ERDDAP or THREDDS ID, a DOI
suffix, a catalogue name). Readers recognise them, and the provider can map them back.

```text
<org>/<dataset>/netcdf/[<version>/]<original subpath>     the files, unchanged
<org>/<dataset>/icechunk/                                 a store built over them
```

For example, from PacIOOS:

```text
pacioos/roms_hiig/netcdf/2026/hiig_forec_20261109.nc        (+ .md5 sidecar)
pacioos/roms_hiig_reanalysis/netcdf/v2.0/2009/hiig_his_zlevel_20090101.nc
pacioos/roms_hiig_reanalysis/icechunk/
```

- **Keep the provider's folder structure under `netcdf/`** (year folders and the like), so a
  path maps back to the source by simple prefix substitution, and the copy script needs no
  renaming logic.
- **Keep the original file names.** Renaming breaks the mapping back to the source and to the
  provider's own documentation.
- **One store per dataset**, beside its files, not a separate tree. The store's virtual
  references point at `<dataset>/netcdf/`.

This is one project's convention, not a standard. If the destination already has a
convention (a NODD bucket's layout, an organisation's), follow it and say so.

## Versions

A product released in versions gets **one folder per version**, and a version folder is never
written into again once it is complete:

```text
<dataset>/netcdf/v2.0/...
<dataset>/netcdf/v3.0/...
<dataset>/icechunk/          one store; snapshots tagged v2.0, v3.0, ...
```

- Name the folder with the provider's own version label. If the files carry none (the PacIOOS
  reanalysis did not), take it from the catalogue or DOI, and record in the README where it
  came from.
- A product that grows daily and is never reissued needs no version folder.
- If you cannot tell whether a product is versioned, ask the provider (see
  `source-audit.md`) before copying. Adding a version folder after the fact means moving every
  file.

What to do when a new version arrives, or files change under an existing one, is open:
`change-detection.md`.

## Decide, then write it down

Before the copy starts, the plan should list, for every product: the source folder, the
destination prefix, the version label (or "none, and why"), and which files are excluded and
why. Put that table in the project README; the copy script reads the same table.
