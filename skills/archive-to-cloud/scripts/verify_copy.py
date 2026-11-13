#!/usr/bin/env python3
"""Check copied files in a public bucket against the .md5 sidecars uploaded beside them.

Standard library only (Python 3.8+; tested with 3.12); needs no credentials. It lists the prefix with an anonymous
path-style S3 ListObjectsV2 request, then downloads each file over HTTPS, computes its MD5 as
the bytes arrive (nothing is written to disk), and compares it with the sidecar that the copy
script computed on the source before uploading.

    verify_copy.py https://data.source.coop/ACCOUNT/PREFIX/ --list-only
    verify_copy.py https://data.source.coop/ACCOUNT/PREFIX/ --list-only --manifest source.tsv
    verify_copy.py https://data.source.coop/ACCOUNT/PREFIX/ --sample 20 --seed 1
    verify_copy.py https://s3.us-west-2.amazonaws.com/BUCKET/PREFIX/

The URL is ENDPOINT/BUCKET/PREFIX (on Source Cooperative the bucket is the account).

One line per problem or checked file:
    OK       downloaded bytes match the sidecar
    BAD      they do not, or the download failed; copy that file again
    NO-MD5   no sidecar: the upload never finished
  with --manifest (one "relative/path<TAB>size" per line, relative to PREFIX):
    MISSING  on the source, not in the bucket
    EXTRA    in the bucket, not on the source
    SIZE     sizes differ
Exit status: 0 no problems, 1 problems found, 2 usage or listing error.
"""
import argparse
import fnmatch
import hashlib
import random
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor

# Source Cooperative's edge refuses Python's default User-Agent.
HEADERS = {"User-Agent": "archive-copy-check/1.0"}


def get(url, timeout=60):
    return urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=timeout)


def split_url(url):
    """https://host/bucket/prefix -> ("https://host", "bucket", "prefix")."""
    u = urllib.parse.urlsplit(url)
    if u.scheme not in ("http", "https") or not u.netloc:
        raise ValueError("expected https://ENDPOINT/BUCKET/PREFIX, got %r" % url)
    bucket, _, prefix = u.path.lstrip("/").partition("/")
    if not bucket:
        raise ValueError("no bucket in %r" % url)
    return "%s://%s" % (u.scheme, u.netloc), bucket, prefix


def list_objects(endpoint, bucket, prefix):
    """Yield (key, size) for every object under prefix (anonymous ListObjectsV2, paginated)."""
    token = None
    while True:
        query = {"list-type": "2", "prefix": prefix}
        if token:
            query["continuation-token"] = token
        url = "%s/%s?%s" % (endpoint, bucket, urllib.parse.urlencode(query))
        root = ET.fromstring(get(url).read())
        # {*} matches any namespace, or none: not every S3-compatible service sets one.
        for c in root.findall("{*}Contents"):
            yield c.findtext("{*}Key"), int(c.findtext("{*}Size"))
        if root.findtext("{*}IsTruncated") != "true":
            return
        token = root.findtext("{*}NextContinuationToken")
        if not token:
            raise RuntimeError("listing truncated but no continuation token")


def object_url(endpoint, bucket, key):
    return "%s/%s/%s" % (endpoint, bucket, urllib.parse.quote(key))


def md5_of_url(url, retries=3):
    for attempt in range(1, retries + 1):
        try:
            h, n = hashlib.md5(), 0
            with get(url, timeout=120) as r:
                for block in iter(lambda: r.read(8 << 20), b""):
                    h.update(block)
                    n += len(block)
            return h.hexdigest(), n
        except Exception:
            if attempt == retries:
                raise
            time.sleep(5 * attempt)


def check(endpoint, bucket, key, size, suffix):
    try:
        expected = get(object_url(endpoint, bucket, key + suffix)).read().decode().split()[0]
    except Exception as e:
        return "BAD", "%s  (could not read sidecar: %s)" % (key, e)
    t = time.time()
    try:
        got, n = md5_of_url(object_url(endpoint, bucket, key))
    except Exception as e:
        return "BAD", "%s  (download failed: %s)" % (key, e)
    dt = max(time.time() - t, 0.001)
    detail = "%s  size=%d  md5=%s  (%.0f MB/s)" % (key, n, got, n / dt / 1e6)
    if got == expected.lower() and n == size:
        return "OK", detail
    return "BAD", "%s  expected md5=%s size=%d" % (detail, expected, size)


def read_manifest(path):
    sizes = {}
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.rstrip("\n")
            if not line.strip():
                continue
            rel, sep, size = line.rpartition("\t")
            if not sep or not size.strip().isdigit():
                raise ValueError("%s line %d: expected 'path<TAB>size'" % (path, i))
            sizes[rel] = int(size)
    return sizes


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("url", help="https://ENDPOINT/BUCKET/PREFIX/ to check")
    p.add_argument("--glob", action="append", default=None,
                   help="data files to check, matched on the file name (default *.nc; repeatable)")
    p.add_argument("--sidecar-suffix", default=".md5", help="checksum sidecar suffix (default .md5)")
    p.add_argument("--manifest", help="source inventory, 'relative/path<TAB>size' per line")
    p.add_argument("--sample", type=int, default=0, help="download only this many, at random")
    p.add_argument("--seed", type=int, help="random seed, to repeat a sample")
    p.add_argument("--parallel", type=int, default=4, help="downloads at once (default 4)")
    p.add_argument("--list-only", action="store_true", help="listing checks only, no downloads")
    a = p.parse_args(argv)
    globs = a.glob or ["*.nc"]

    try:
        endpoint, bucket, prefix = split_url(a.url)
        objects = dict(list_objects(endpoint, bucket, prefix))
        manifest = read_manifest(a.manifest) if a.manifest else None
    except Exception as e:
        print("ERROR  %s" % e, file=sys.stderr)
        return 2

    def is_data(key):
        name = key.rsplit("/", 1)[-1]
        return any(fnmatch.fnmatchcase(name, g) for g in globs)

    data = sorted(k for k in objects if is_data(k))
    with_md5 = [k for k in data if k + a.sidecar_suffix in objects]
    total = sum(objects[k] for k in data)
    print("%d data files (%.1f GB) under %s/%s/%s; %d with a %s sidecar"
          % (len(data), total / 1e9, endpoint, bucket, prefix, len(with_md5), a.sidecar_suffix))

    problems = 0
    for k in data:
        if k + a.sidecar_suffix not in objects:
            print("NO-MD5   %s  size=%d" % (k, objects[k]))
            problems += 1

    if manifest is not None:
        copied = {k[len(prefix):]: objects[k] for k in data}
        for rel in sorted(set(manifest) - set(copied)):
            print("MISSING  %s  size=%d" % (rel, manifest[rel]))
            problems += 1
        for rel in sorted(set(copied) - set(manifest)):
            print("EXTRA    %s  size=%d" % (rel, copied[rel]))
            problems += 1
        for rel in sorted(set(copied) & set(manifest)):
            if copied[rel] != manifest[rel]:
                print("SIZE     %s  copy=%d source=%d" % (rel, copied[rel], manifest[rel]))
                problems += 1
        print("manifest: %d files on the source, %d copied" % (len(manifest), len(copied)))

    if not a.list_only:
        todo = with_md5
        if a.sample and a.sample < len(todo):
            todo = sorted(random.Random(a.seed).sample(todo, a.sample))
        with ThreadPoolExecutor(max(1, a.parallel)) as pool:
            jobs = [pool.submit(check, endpoint, bucket, k, objects[k], a.sidecar_suffix)
                    for k in todo]
            for j in jobs:
                status, detail = j.result()
                print("%-8s %s" % (status, detail), flush=True)
                problems += status != "OK"
        print("%d downloaded and checked" % len(todo))

    print("%d problems" % problems)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
