<!-- DRAFT for earth-mover/icechunk. Not posted. Review before filing. -->

# `s3_store` virtual chunk reads are ~2× slower than `http_store` against an endpoint that offers HTTP/2

## Summary

`s3_store` virtual chunk reads go through the AWS SDK's default HTTPS client. That client offers ALPN
`["h2", "http/1.1"]`, so against an S3-compatible endpoint that accepts HTTP/2, all requests share a
few HTTP/2 connections. `http_store` reads go through `object_store`, which uses HTTP/1.1 only by
default because "HTTP/2 is known to be significantly slower than HTTP/1"
([apache/arrow-rs-object-store#104](https://github.com/apache/arrow-rs-object-store/issues/104)).

Against Source Cooperative (`https://data.source.coop`, which offers HTTP/2), the same virtual
references read about 1.5–2× slower from the hub (AWS us-west-2) through `s3_store`, and 3–5× slower
from Google Colab. Allowing HTTP/2 on `http_store` makes it just as slow, so the cause is HTTP/2 in
the Rust client stack, not the S3 API. Against AWS S3 and CloudFerro, which offer only HTTP/1.1,
`s3_store` and `http_store` read at the same speed.

There is no way in the Python API to make `s3_store` use HTTP/1.1.

## Reprex

`icechunk`, `zarr` and `numpy` only; no credentials. An in-memory repo holds one uint8 array whose
64 chunks are virtual references to 8.3 MB byte ranges of public files on Source Cooperative (no
codecs, so a chunk read is exactly a range read). The same references are read through three containers:

```
pip install icechunk zarr numpy
python icechunk_reprex.py --rounds 5
```

<!-- link to the script on the branch, or paste it inline when filing -->
Script: `docs/design/s3-vs-https/icechunk_reprex.py` in ocean-icechunks/ocean-icechunks-skills
(branch `s3-vs-https-investigation`).

Result, icechunk 2.3.1, zarr 3.4.2, Linux on AWS us-west-2, zarr `async.concurrency` 64, 530 MB per read:

| container | median s | best s | MB/s (median) |
|---|---|---|---|
| `http_store()` (object_store default, HTTP/1.1) | 1.62 | 1.25 | 328 |
| `http_store(opts={"http1_only": "false"})` (HTTP/2) | 2.19 | 1.87 | 242 |
| `s3_store(endpoint_url="https://data.source.coop", anonymous=True, force_path_style=True)` | 2.52 | 2.01 | 210 |

The same bytes are returned by all three.

## Supporting measurements

**Connections.** Peak established TCP connections to the source host during a 64-chunk read, from `psutil`:

| source | `http_store` | `s3_store` | speed |
|---|---|---|---|
| `data.source.coop` (offers h2) | 37–69 | **6** | `s3_store` slower |
| `*.s3.amazonaws.com`, NODD bucket (HTTP/1.1 only) | 64 | 64 | equal |
| `s3.waw3-1.cloudferro.com` (HTTP/1.1 only) | 64 | 64 | equal |

**The same store with only the HTTP client changed** (full 64-chunk variable of a virtual ROMS dataset,
built with VirtualiZarr):

| | median s | peak connections |
|---|---|---|
| `http_store()` default | 1.10 | 69 |
| `http_store(opts={"http1_only": "false"})` | 2.41 | 6 |
| `http_store(opts={"http2_only": "true"})` | 2.11 | 6 |
| `s3_store(...)` | 2.29 | 6 |

**Without Icechunk.** obstore against `data.source.coop`, 320 × 1.66 MB ranges, 64 in flight: S3 API 474 MB/s over HTTP/1.1
against 272 MB/s over HTTP/2; plain GET 562 against 283 MB/s. curl (nghttp2) gets the same throughput over a single
HTTP/2 connection as over 64 HTTP/1.1 connections, so the server's HTTP/2 support looks fine. The slow part is
the hyper/h2 client.

## Where it comes from (v2.3.1)

- `icechunk-s3/src/lib.rs`, `mk_client`: builds the S3 client from `aws_config::defaults(...)` and sets no
  `http_client`, so the SDK's default HTTPS client is used.
- `aws-smithy-http-client` 1.5.0, `src/client/tls/rustls_provider.rs:322`: `wrap_connector` offers
  `&[b"h2", b"http/1.1"]`.
- `object_store` 0.14.2, `src/client/mod.rs:403`: `http1_only: true` by default, with the comment
  quoted above.

## Ask

One of these, in order of preference:

1. Use HTTP/1.1 for `s3_store` / `s3_compatible` virtual chunk fetching by default, matching `http_store` and
   object_store's reasoning, or
2. add an option to `s3_store()` (and the repository storage config) to force HTTP/1.1, for example an
   ALPN choice or a custom SDK HTTP client built with HTTP/1.1 only, or
3. at least document that `s3_store` may be slower than `http_store` against endpoints that offer HTTP/2.

Where this came up: Earthmover suggested switching PacIOOS virtual references from `https://data.source.coop/...`
to `s3://...` (ocean-icechunks/pacioos#40). Measured, that would make reads about 2× slower until this is addressed.

Investigation notes: ocean-icechunks/ocean-icechunks-skills#27.
