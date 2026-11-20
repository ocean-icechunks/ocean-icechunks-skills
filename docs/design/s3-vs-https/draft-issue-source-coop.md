<!-- DRAFT for source-cooperative/data.source.coop. Not posted. Review before filing.
     Framed as an FYI and question: the slow path looks client-side (Rust hyper/h2), not the proxy. -->

# FYI: S3-API clients built on the Rust AWS SDK read ~2× slower through data.source.coop because it offers HTTP/2

## What we see

Concurrent range reads from `https://data.source.coop` are about half as fast over HTTP/2 as over HTTP/1.1
when the client is Rust `object_store` (obstore) or the Rust AWS SDK (hyper/h2 under both). The proxy
serves both protocols, and the S3 API itself adds no cost: over HTTP/1.1, S3 GetObject and plain GET read at
the same speed.

This matters because `data.source.coop` is, as far as we have tested, the only S3-compatible endpoint
that offers HTTP/2. AWS S3 and CloudFerro offer only HTTP/1.1. Tools whose S3 client offers `h2` first,
such as the Rust AWS SDK's default client used by Icechunk's `s3_store`, therefore take the slower path only
on Source Cooperative. For Icechunk virtual stores, `s3://ocean-icechunks/...` references read about 2× slower than
`https://data.source.coop/ocean-icechunks/...` references to the same bytes (reported to Icechunk separately).

## Reprex

No credentials, `pip install obstore`:

```
python source_coop_reprex.py --rounds 5
```

<!-- link to the script on the branch, or paste it inline when filing -->
Script: `docs/design/s3-vs-https/source_coop_reprex.py` in ocean-icechunks/ocean-icechunks-skills
(branch `s3-vs-https-investigation`). It reads the same 320 × 1.66 MB ranges of public
`ocean-icechunks/pacioos/...` objects four ways, with 64 in flight, and prints the Cloudflare colo
and connect time from `/cdn-cgi/trace` (not the client IP).

Result, 2026-11-20, from AWS us-west-2 (Cloudflare colo PDX, TCP connect ≈ 30 ms), obstore 0.12.1, 530 MB per read:

| client | median s | best s | MB/s |
|---|---|---|---|
| S3 API (S3Store, unsigned, path-style), HTTP/1.1 | 1.12 | 0.92 | 474 |
| S3 API, HTTP/2 | 1.95 | 1.55 | 272 |
| plain GET (HTTPStore), HTTP/1.1 | 0.94 | 0.87 | 562 |
| plain GET, HTTP/2 | 1.87 | 1.64 | 283 |

With curl 8.23 (nghttp2), the same 320 ranges took 1.23–1.29 s over HTTP/2 (one multiplexed connection) and
1.16–1.24 s over HTTP/1.1 (64 connections). So HTTP/2 through the proxy can be fast. The gap is specific to
the Rust hyper/h2 client, which has a known HTTP/2 throughput problem
([apache/arrow-rs-object-store#104](https://github.com/apache/arrow-rs-object-store/issues/104)).

From Google Colab the gap for the Icechunk case was larger (3–5×), so it may grow with distance to the edge.

## Questions

1. Is offering HTTP/2 to S3-API clients on `data.source.coop` intentional, and does it help other clients?
2. Is there any per-connection or per-stream limit in the Worker or Cloudflare front end that would cap HTTP/2
   throughput (for example, concurrent streams per connection, or how response bodies are streamed back through
   the Worker)?
3. Would you consider documenting that Rust/AWS-SDK-based clients may read faster over HTTP/1.1, or offering an
   HTTP/1.1-only hostname for S3-API access?

We are not asking for a change in the proxy if the cause is entirely client-side. This is mainly so that you know, and
in case there is something on the edge side we are missing.

Related: ocean-icechunks/ocean-icechunks-skills#27 (investigation), ocean-icechunks/pacioos#40.
