# s3:// vs https:// virtual references

Investigation for [#27](https://github.com/ocean-icechunks/ocean-icechunks-skills/issues/27), 2026-11-19 to
2026-11-20. Filed upstream as
[earth-mover/icechunk#2571](https://github.com/earth-mover/icechunk/issues/2571). Not yet folded into the
`virtual-icechunk` skill.

## What we found

- **Access.** `s3://` references read anonymously wherever we tried: Source Cooperative (endpoint
  `data.source.coop`), NODD on AWS S3, CloudFerro and OSN (endpoint saved in the container), and GCS's S3
  interface. The reader authorizes with `icechunk.containers_credentials({prefix:
  s3_anonymous_credentials()})`; a bare anonymous credential is rejected by `reopen`. The container's endpoint,
  path-style and anonymous settings are saved in the repo config, so readers need not know them.
- **Speed: HTTP/2 is the cause, not the S3 API.** Icechunk's `s3_store` uses the Rust AWS SDK's default client,
  which offers ALPN `h2` first. `http_store` (and `gcs_store`) use `object_store`, which is HTTP/1.1 by default
  *because* hyper's HTTP/2 is slow (arrow-rs-object-store#104). On endpoints that offer HTTP/2, `s3_store` reads
  the same bytes 2–7× slower. Turning HTTP/2 on for `http_store` reproduces the slowdown exactly.

  | 530 MB, 64 chunks, from the hub (us-west-2) | Source Coop | GCS | OSN `udel1` |
  |---|---|---|---|
  | `http_store()` (HTTP/1.1) | 1.1 s | 1.6 s | 1.7 s |
  | `http_store`, HTTP/2 allowed | 2.4 s | 3.0 s | 11.3 s |
  | `s3_store` | 2.3 s | 3.3 s | 11.7 s |
  | `gcs_store()` | — | 1.7 s | — |

  AWS S3, Tigris, Wasabi and CloudFerro offer only HTTP/1.1, so `s3://` and `https://` are equal there (NODD and
  CloudFerro measured). From Colab the Source Coop gap was 3–5×.
- **Other tools are largely unaffected.** fsspec/s3fs (aiohttp), boto3 and the AWS CLI (urllib3) speak only HTTP/1.1.
  GDAL and curl use HTTP/2 via libcurl/nghttp2 and are as fast as HTTP/1.1 on Source Coop (2.3× slower on OSN,
  against 7× for the Rust clients).
- **Why Earthmover says use `s3://`.** Arraylake forbids `http://`/`https://` virtual chunk container prefixes
  "for security reasons" ([docs](https://docs.earthmover.io/guide/virtual-datasets)). That is the likely meaning
  of the "security reasons" in ocean-icechunks/pacioos#40. It means a store meant for Arraylake must use `s3://`
  and, on HTTP/2 endpoints, pay the slowdown until icechunk#2571 is fixed.
- **GlobColour's S3 → CloudFerro HTTPS rewrite** was not about speed (equal from the hub); probably simplicity.
- **Side finds.** The `s3://pacioos/...` path suggested in pacioos#40 has the wrong bucket; it is
  `s3://ocean-icechunks/pacioos/...` at endpoint `data.source.coop`. Speeds to Source Coop swing over the day
  (one run reversed the result); repeat runs before trusting a single number.

## Decisions (Eli)

- It is an **Icechunk issue**. No issue to Source Cooperative: `draft-issue-source-coop.md` is kept as a record
  and **not filed** (turning off HTTP/2 would cost browser viewers and change nothing for GDAL).
- **Keep the test stores** in `ocean-icechunks/test-repo/s3-vs-https/` (`roms_reanalysis_8day`,
  `oisst_nodd_64day`, `globcolour_chl_16day`, each `H`/`S`) so people can be pointed at them.
- The skill's "prefer HTTPS" lines (`references/source-patterns.md`, `learn-and-evolve.md`) are **not changed
  yet**. Measured, HTTPS is the faster choice on HTTP/2 endpoints; the counterweight is Arraylake requiring
  `s3://`. Revisit once icechunk#2571 has an answer.

## Files

Test stores and timing:
- `build_pair.py` (ROMS on Source Coop), `build_oisst.py` (NODD), `build_globcolour.py` (CloudFerro): built the
  H/S pairs, once, with Source Coop write keys via `icechunk_utils` from a local `ocean-icechunks/pacioos`
  checkout. Records, not reusable tools. S was made from H with `vds.vz.rename_paths`.
- `bench.py` (`--dataset roms|oisst|globcolour`) and `s3_vs_https_read_test.ipynb` (Colab/laptop): anonymous
  timed reads of a pair. JSON results: `hub-us-west-2*.json`, `colab.json`, `colab-both.json`.

Finding the cause:
- `logging_proxy.py` + `trace_requests.py`: both clients send the same range requests (each 8.3 MB chunk as
  5 × 1.66 MB); through an HTTP/1.1 proxy they are equally fast.
- `count_connections.py`: peak connections per client per endpoint (6 for HTTP/2 vs 37–69 for HTTP/1.1).
- `icechunk_http_h1_vs_h2.py`: the same `https://` store with HTTP/2 off and on.
- `obstore_h1_vs_h2.py`, `source_coop_reprex.py`: no Icechunk; obstore S3 API and plain GET over HTTP/1.1 and HTTP/2.
- `gdal_h1_vs_h2.py`: GDAL `/vsicurl/` and `/vsis3/` over HTTP/1.1 and HTTP/2.
- `icechunk_endpoint_test.py --target gcs|osn`: four containers over the same bytes on GCS and OSN.
- `icechunk_reprex.py`: the reprex in icechunk#2571.
- `draft-issue-icechunk.md`: the filed text (icechunk#2571). `draft-issue-source-coop.md`: not filed.

Chunk layouts: ROMS one uncompressed time step per chunk (36 × 195 × 295 float32, ~8.3 MB); OISST one gzip chunk
per day per variable (~1 MB); GlobColour 256 × 256 gzip (578 per global day), read over a 1024 × 2048 box.
