# Destinations

Only Source Cooperative has been used as a copy destination so far. Everything in its section
was found by testing in November 2026 and may change as the service changes. For any other
destination, check its current documentation and test against a scratch prefix first.

## Source Cooperative

**Endpoints.** Writes go to the S3 API at `https://data.source.coop` with path-style addressing,
region `us-east-1`, bucket = account (for example `ocean-icechunks`), key = product path. Public
reads go to the same host over HTTPS: `https://data.source.coop/<account>/<key>`, and listings to
`https://data.source.coop/<account>?list-type=2&prefix=<prefix>`.

**rclone settings.** Each was found by a failure. Set them as environment variables
(`RCLONE_CONFIG_<REMOTE>_<OPTION>`), so no config file is written:

| Setting | Without it |
|---|---|
| `type = s3`, `provider = Other`, `env_auth = true`, `force_path_style = true` | (the basics) |
| `sign_accept_encoding = false` | every request fails with `SignatureDoesNotMatch` |
| `list_version = 2` | listings say "directory not found" |
| `no_check_bucket = true` | uploads fail with `Missing object key` |
| `upload_cutoff = 0`, and `RCLONE_STREAMING_UPLOAD_CUTOFF=0` | single-part uploads fail: "headers present in the request which were not signed" |
| `chunk_size = 64M` | requests over about 100 MB are refused with `413` |

The full working block is in `upload_to_source_coop.sh` in ocean-icechunks/pacioos.

**Behaviour to expect:**

- **No stored checksum.** Source Cooperative drops the checksum rclone normally stores with an
  object, and multipart ETags are not MD5s. Hence the `.md5` sidecars. Upload with
  `--s3-disable-checksum`.
- **Occasional `520` errors on a multipart part.** rclone's own retries handled every one
  (5 in 4,380 files). No alarm needed, but keep `--retries`.
- **`GetBucketVersioning NoSuchBucket`** when purging a prefix is harmless.
- **Content types are never inferred.** They are served as uploaded. NetCDF needs none in
  particular, but a README or HTML page uploaded without one is served as
  `binary/octet-stream`. Set `Content-Type` on each upload.
- **No directory index.** A browser cannot list a folder; link files directly.
- **Python's default User-Agent is refused (403)** at the edge. Send your own, generic one.
- **Server-side copy works.** A 1.9 GB file copied in 40 s with an identical MD5, and
  re-laying out 1.7 TB took under an hour with no re-upload (`rclone copy sc:old sc:new` within
  one remote). Verify the new prefix (`verify.md`), then purge the old one, and ask before
  purging.

**Credentials.** Write keys are short-lived STS keys from the
[`source-coop` CLI](https://github.com/source-cooperative/source-coop-cli), lasting about 12 hours:

- `eval "$(source-coop creds --format env)"` puts them in the environment.
- An AWS profile with `credential_process = source-coop creds` fetches fresh ones by itself,
  which is better for long runs on the machine where the CLI is logged in.
- `source-coop creds` reports an `Expiration`; a driver uses it to size each run
  (`copy-script.md`).
- After the first browser login, the CLI refreshes keys without a browser (refresh token) until
  the login itself expires (`source-coop login --duration 1d`).

**Logging in from a JupyterHub.** The login opens a browser at a `localhost` redirect, which
cannot reach a hub. Run `source-coop login --duration 1d --port 8400`, and when the browser
lands on `http://localhost:8400/...`, replace `http://localhost:8400` with the hub's
`https://<hub>/user/<name>/proxy/8400`. Explain this plainly in any instructions: it is where
people get stuck.

**Account setup.** The uploader needs write rights on the product (an organisation admin adds
them). A server that runs a daily top-up without a person needs a non-interactive credential;
ask Source Cooperative about one, since the browser login cannot run there.

## Other S3-compatible destinations (untested here)

AWS S3, NODD buckets and other S3-compatible stores should need far fewer settings: standard
rclone `provider` values, virtual-host addressing where supported, and stored checksums that
work. The contract in `copy-script.md` and the sidecars still apply: a sidecar is portable,
whatever the store does with checksums. `scripts/verify_copy.py` works on any public bucket that
answers an anonymous path-style `ListObjectsV2`; a private bucket needs a signed client instead
(for example `rclone check --download`).
