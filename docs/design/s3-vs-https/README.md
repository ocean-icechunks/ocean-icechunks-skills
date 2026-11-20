# s3:// vs https:// virtual references: test material

Evidence for [#27](https://github.com/ocean-icechunks/ocean-icechunks-skills/issues/27).
Provisional: these are the inputs to a design note that is not written yet.

- `build_pair.py`: builds two virtual Icechunk stores over the same 8 PacIOOS ROMS reanalysis
  files (2009-01-01..08) in `ocean-icechunks/test-repo/s3-vs-https/roms_reanalysis_8day/`:
  **H** references `https://data.source.coop/ocean-icechunks/pacioos/...` (HTTP store);
  **S** references `s3://ocean-icechunks/pacioos/...` (S3 store, endpoint `data.source.coop`,
  anonymous, path-style), made from H with `vds.vz.rename_paths`. Run once on the JupyterHub
  with Source Cooperative write keys; it imports `icechunk_utils` from a local
  `ocean-icechunks/pacioos` checkout and is kept as a record, not as a reusable tool.
- `build_oisst.py`: the same pair over 64 days of NOAA OISST v2.1 on NODD (AWS us-east-1,
  `noaa-cdr-sea-surface-temp-optimum-interpolation-pds`), stores in
  `test-repo/s3-vs-https/oisst_nodd_64day/`. S uses `s3_store(region="us-east-1", anonymous=True)`.
- `bench.py`: reads both stores of a pair (`--dataset roms|oisst`) anonymously and times the same reads. No credentials needed.
- `s3_vs_https_read_test.ipynb`: the same test as a self-contained notebook for Colab or a laptop.
- `hub-us-west-2.json`: raw timings from the JupyterHub (AWS us-west-2), 2026-11-20.
- `colab.json`: raw timings from Google Colab, 2026-11-20 (ROMS pair only; older notebook).
- `hub-us-west-2-oisst.json`: OISST pair from the JupyterHub, 2026-11-20.

ROMS: each chunk is one whole time step of one variable (36 x 195 x 295 float32, uncompressed, ~8.3 MB),
so the point series, surface and full-variable reads each fetch all 64 chunks (~530 MB).

OISST: one gzip chunk per day per variable (1 x 1 x 720 x 1440 int16, ~1 MB), 64 chunks per bulk read.
