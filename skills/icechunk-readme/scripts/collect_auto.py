#!/usr/bin/env python3
"""Read the values a README needs from each Icechunk store and write <product id>.json files.

Writes the --auto directory that render_readme.py takes. Every read is anonymous: the
store's main branch through Icechunk (s3:// virtual chunk containers with anonymous S3
credentials), the files the store references, the source-file prefix through an S3
ListObjectsV2 listing over HTTPS, the first bytes of a sample of files for their format and,
when a product asks for it, the header of its newest source file through range requests.
Nothing is written anywhere but --out.

    collect_auto.py collection.md --out auto/            every product the collection lists
    collect_auto.py roms_hiig.md  --out auto/            one product
    collect_auto.py noaa-ohc.md   --out auto/            a standalone product: one file per store

Needs Python 3.10+, PyYAML, icechunk, xarray and zarr; h5py too when a product sets
metadata.source_attributes and its newest file is NetCDF-4/HDF5 (NetCDF-3 headers are parsed
here). Source files are counted from the store's references (up to --max-refs chunks) and, when
the product's source_url answers an S3 listing, from that listing, which adds sizes.

Exit status: 0 written, 1 a product could not be read (others are still written), 2 usage error.
"""
import argparse
import datetime as dt
import io
import json
import math
import os
import pathlib
import re
import struct
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

import yaml

FORMATS = {".nc": "netcdf", ".nc4": "netcdf", ".cdf": "netcdf", ".h5": "hdf5", ".hdf5": "hdf5", ".he5": "hdf5"}
UNITS = {"degrees_north": "°N", "degree_north": "°N", "degrees_east": "°E", "degree_east": "°E"}
# Attributes the netCDF library adds to a NetCDF-4 file; xarray hides them, and so do we.
NC_INTERNAL = {"_NCProperties", "_nc3_strict", "_IsNetcdf4", "_SuperblockVersion"}
TIMEOUT = 60
MAX_SAMPLE = 40  # most file headers read to find the source formats
MIN_SAMPLE = 10
MAX_COORD_VALUES = 10_000_000  # largest non-dimension coordinate read for its range
# Most chunk references listed to count the files a store uses. roms_hiig's 804,025 took 5 s and
# ~400 MB; HYCOM GOFS (~23 million) would not fit a small hub. Above this, the listing alone counts.
MAX_REFS = 3_000_000


class CollectError(Exception):
    pass


def front_matter(path):
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n") or "\n---\n" not in text[3:]:
        raise CollectError(f"{path}: must start with YAML front matter between '---' lines")
    return yaml.safe_load(text[4:text.index("\n---\n", 3)]) or {}


def http(url, headers=None, method="GET"):
    req = urllib.request.Request(url, headers=headers or {}, method=method)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read(), resp.headers


# --- the store ---------------------------------------------------------------------------

def open_main(store_url):
    import icechunk
    repo = icechunk.Repository.open(icechunk.http_storage(store_url))
    # Coordinates such as time may be virtual; reading them needs the containers authorized.
    # An s3:// container (noaa-oisst) needs S3 anonymous credentials; HttpAccess is refused.
    containers = sorted(repo.config.virtual_chunk_containers or [])
    for p in containers:
        if not p.startswith(("s3://", "http://", "https://")):
            raise CollectError(f"virtual chunk container {p}: only s3:// and http(s):// are supported")
    auth = icechunk.containers_credentials({
        p: icechunk.s3_anonymous_credentials() if p.startswith("s3://") else icechunk.credentials.HttpAccess
        for p in containers})
    config = dict(repo.config.virtual_chunk_containers or {})
    repo = repo.reopen(authorize_virtual_chunk_access=auth)
    snap = next(iter(repo.ancestry(branch="main")))
    return repo.readonly_session("main"), snap, containers, config


def https_url(url, config):
    """HTTPS form of a reference, so its first bytes can be read with a range request.

    An s3:// container on Source Cooperative (necofs-waves) names its endpoint and is path-style;
    one on AWS (noaa-gomofs) has no endpoint and is reached as <bucket>.s3.<region>.amazonaws.com.
    """
    if not url.startswith("s3://"):
        return url
    prefix = max((p for p in config if url.startswith(p)), key=len, default=None)
    opts = config[prefix].store[0] if prefix else None
    bucket, _, key = url[5:].partition("/")
    endpoint = getattr(opts, "endpoint_url", None)
    if endpoint:
        return f"{endpoint.rstrip('/')}/{bucket}/{key}"
    region = getattr(opts, "region", None)
    return f"https://{bucket}.s3.{region}.amazonaws.com/{key}" if region else f"https://{bucket}.s3.amazonaws.com/{key}"


def chunk_count(store, groups):
    """Chunks the store could reference, from array shapes, to decide whether listing them is safe."""
    import zarr
    root = zarr.open_group(store, mode="r")
    total = 0
    for g in groups:
        group = root if g == "/" else root[g.lstrip("/")]
        for _, a in group.arrays():
            total += math.prod(math.ceil(n / c) for n, c in zip(a.shape, a.chunks)) if a.shape else 1
    return total


def referenced_files(session, config):
    """Every file the store references, as HTTPS URLs, sorted."""
    return sorted({https_url(u, config) for u in session.all_virtual_chunk_locations()})


def array_groups(store):
    """Paths ('/', '/sub', ...) of every group that holds arrays, root first."""
    import zarr
    out = []

    def walk(group, path):
        if any(True for _ in group.array_keys()):
            out.append(path)
        for name, sub in sorted(group.groups()):
            walk(sub, f"{path.rstrip('/')}/{name}")
    walk(zarr.open_group(store, mode="r"), "/")
    return out


def number(x):
    text = f"{round(float(x), 2):,.2f}".rstrip("0").rstrip(".").replace(",", "")
    return text.replace("-", "−")  # the fixtures and READMEs use a real minus sign


def time_text(value):
    import numpy as np
    t = np.datetime64(value, "s").astype(dt.datetime)
    return t.strftime("%Y-%m-%dT%H:%MZ" if t.minute or t.second else "%Y-%m-%dT%HZ")


def values_text(var):
    import numpy as np
    if var.size == 0:
        return ""
    if np.issubdtype(var.dtype, np.datetime64):
        vals = var.values[~np.isnat(var.values)]  # a best series's run time is NaT where no run covers
        if not vals.size:
            return ""
        lo, hi = vals.min(), vals.max()
        return time_text(lo) if lo == hi else f"{time_text(lo)} to {time_text(hi)}"
    if np.issubdtype(var.dtype, np.timedelta64):  # forecast leads (step, lead): "0 to 143 h", not ns
        vals = var.values[~np.isnat(var.values)]
        if not vals.size:
            return ""
        for unit, name in (("h", "h"), ("m", "min"), ("s", "s")):
            if not (vals % np.timedelta64(1, unit)).any():
                lo, hi = (vals.min() // np.timedelta64(1, unit)), (vals.max() // np.timedelta64(1, unit))
                return f"{lo} {name}" if lo == hi else f"{lo} to {hi} {name}"
        return f"{vals.min()} to {vals.max()}"
    if var.dtype == bool:  # noaa-oisst `preliminary`: NOAA replaces the newest days within weeks
        vals = var.values.ravel()
        n = int(vals.sum())
        if var.ndim == 1 and 0 < n < vals.size and vals[-n:].all():
            return f"true for the last {n:,}, false before"
        return f"true for {n:,} of {vals.size:,}"
    if not np.issubdtype(var.dtype, np.number):
        return ""
    vals = var.values
    lo, hi = np.nanmin(vals), np.nanmax(vals)
    units = var.attrs.get("units", "")
    units = UNITS.get(units, units)
    text = number(lo) if lo == hi else f"{number(lo)} to {number(hi)}"
    return f"{text} {units}".strip()


def group_values(store, group, last_update):
    import numpy as np
    import xarray as xr
    ds = xr.open_zarr(store, group=None if group == "/" else group.lstrip("/"),
                      consolidated=False, chunks=None)
    # Store listing order is not stable, so order by rank, then name.
    names = sorted(ds.data_vars, key=lambda n: (-ds[n].ndim, n))
    variables = []
    for n in names:
        a = ds[n].attrs
        v = {"name": n, "dims": list(ds[n].dims), "units": str(a.get("units", ""))}
        for key in ("standard_name", "long_name"):
            if a.get(key):
                v[key] = str(a[key])
        variables.append(v)
    # Dimensions in the order the largest variables use them; other coordinates after the
    # first dimension they lie on, scalar coordinates last.
    dims = []
    for n in names + sorted(ds.coords):
        for d in ds[n].dims:
            if d not in dims:
                dims.append(d)
    coords = []
    for d in dims:
        c = {"name": d, "size": int(ds.sizes[d])}
        if d in ds.coords:
            if np.issubdtype(ds[d].dtype, np.datetime64):
                c["as_of"] = last_update
            c["values"] = values_text(ds[d])
        else:
            # A dimension with no coordinate variable (node, nele, eta_rho): keep its size.
            c["no_coordinate"] = True
        coords.append(c)
        for n in sorted(ds.coords):
            if n not in ds.dims and ds[n].dims and ds[n].dims[0] == d:
                # 2-D lat/lon, unstructured node lat/lon, run times on time: their range too,
                # unless reading them would be large.
                small = ds[n].size <= MAX_COORD_VALUES
                coords.append({"name": n, "on": ", ".join(ds[n].dims),
                               "values": values_text(ds[n]) if small else ""})
    for n in sorted(ds.coords):
        if not ds[n].dims:
            coords.append({"name": n, "size": 1, "values": values_text(ds[n])})
    return ds, variables, coords


def time_steps(ds):
    """Steps along the group's time dimension, or None when they say little about files.

    Estimates the file count of a store too large to list its references, on the assumption of
    one file per step. Checked against exact counts (2026-11-23): gomofs, PACE CHL, OHC and
    ECCOFS best within 0.2%, HYCOM 1.5% high, PACE KD 2x high (two groups read each file).
    None for an FMRC (time x step: ECCOFS writes a file per step, casco one per run, 576 steps
    in 3 files) and for a best time series of forecast runs, marked by a run time or lead along
    time (roms_hiig 8 steps a file, txla 32).
    """
    import numpy as np
    timelike = lambda v: np.issubdtype(v.dtype, np.datetime64) or np.issubdtype(v.dtype, np.timedelta64)  # noqa: E731
    dims = [d for d in ds.dims if d in ds.coords and timelike(ds[d])]
    if len(dims) != 1:
        return None
    for n in ds.coords:
        if n not in ds.dims and timelike(ds[n]) and dims[0] in ds[n].dims:
            return None
    return int(ds.sizes[dims[0]])


def jsonable(value):
    import numpy as np
    if isinstance(value, bytes):
        return value.decode("utf-8", "replace")
    if isinstance(value, np.ndarray):
        return [jsonable(x) for x in value.tolist()]
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, float) and not math.isfinite(value):
        return str(value)
    if isinstance(value, (list, tuple)):
        return [jsonable(x) for x in value]
    if isinstance(value, dict):
        return {k: jsonable(v) for k, v in value.items()}
    return value


def time_range(ds):
    import numpy as np
    times = [ds[n] for n in ds.dims if n in ds.coords and np.issubdtype(ds[n].dtype, np.datetime64)]
    if not times:
        return []
    t = times[0].values
    return [str(np.datetime64(t.min(), "D")), str(np.datetime64(t.max(), "D"))]


# --- the source files --------------------------------------------------------------------

class NotListable(CollectError):
    pass


def split_s3_url(url):
    """Listing endpoint, bucket and key prefix of an S3-style URL.

    s3://<bucket>/<prefix> and https://<bucket>.s3[.<region>].amazonaws.com/<prefix> are
    virtual-hosted; anything else (data.source.coop, OSN) is taken as path-style,
    https://<host>/<bucket>/<prefix>.
    """
    u = urllib.parse.urlsplit(url)
    if u.scheme == "s3":
        return f"https://{u.netloc}.s3.amazonaws.com", u.netloc, u.path.lstrip("/")
    m = re.match(r"^(?P<bucket>[^.]+)\.s3[.-]([a-z0-9-]+\.)?amazonaws\.com$", u.netloc)
    if m:
        return f"{u.scheme}://{u.netloc}", m["bucket"], u.path.lstrip("/")
    bucket, _, prefix = u.path.lstrip("/").partition("/")
    return f"{u.scheme}://{u.netloc}/{bucket}", bucket, prefix


def list_prefix(url):
    endpoint, _, prefix = split_s3_url(url)
    ns = {"s3": "http://s3.amazonaws.com/doc/2006-03-01/"}
    token, objects = None, []
    while True:
        q = {"list-type": "2", "prefix": prefix}
        if token:
            q["continuation-token"] = token
        try:
            body, _ = http(f"{endpoint}?{urllib.parse.urlencode(q)}")
            root = ET.fromstring(body)
        except (urllib.error.HTTPError, ET.ParseError) as exc:
            # An HTTPS server that is not S3 (CoastWatch, NCEI) answers with a web page or a 404.
            raise NotListable(f"{url} cannot be listed as S3 ({type(exc).__name__})") from None
        if not root.tag.endswith("ListBucketResult"):
            raise NotListable(f"{url} cannot be listed as S3 (answer is <{root.tag}>)")
        for c in root.findall("s3:Contents", ns):
            objects.append((c.findtext("s3:Key", namespaces=ns), int(c.findtext("s3:Size", namespaces=ns)),
                            c.findtext("s3:LastModified", namespaces=ns)))
        token = root.findtext("s3:NextContinuationToken", namespaces=ns)
        if root.findtext("s3:IsTruncated", namespaces=ns) != "true" or not token:
            return endpoint, objects


def size_text(n):
    for unit, scale in (("TB", 1e12), ("GB", 1e9), ("MB", 1e6)):
        if n >= scale / 10 or unit == "MB":  # 0.46 TB as the PacIOOS README has it, but 33 GB, not 0.03 TB
            return f"{n / scale:.2f} {unit}"


def relative(url, data_base):
    """Path under the collection when the files are there (PacIOOS); else the full URL (AWS)."""
    return url[len(data_base) + 1:] if url.startswith(data_base + "/") else url


def source_files(source_url, data_base):
    endpoint, objects = list_prefix(source_url)
    data = [o for o in objects if pathlib.PurePosixPath(o[0]).suffix.lower() in FORMATS]
    if not data:
        raise CollectError(f"no data files (.nc, .h5, ...) under {source_url}")
    kinds = {FORMATS[pathlib.PurePosixPath(k).suffix.lower()] for k, _, _ in data}
    summary = {"format": kinds.pop() if len(kinds) == 1 else "files",
               "path": relative(source_url, data_base),
               # a browser cannot open s3://; the listing endpoint's URL is the same place over HTTPS
               "url": f"{endpoint}/{split_s3_url(source_url)[2]}",
               "files": len(data),
               "size": size_text(sum(s for _, s, _ in data))}
    urls = [(f"{endpoint}/{k}", s, m) for k, s, m in data]
    add_formats(summary, [u for u, _, _ in urls], data_base)
    return summary, urls


def add_formats(summary, urls, data_base):
    formats, summary["formats_sampled"] = file_formats(urls)
    summary["formats"] = [{**f, "first": relative(f["first"], data_base), "last": relative(f["last"], data_base)}
                          for f in formats]


def summary_from_references(refs, data_base):
    """source_files from the files the store references, when no listing is possible."""
    prefix = os.path.commonprefix(refs).rpartition("/")[0] + "/"
    kinds = {FORMATS.get(pathlib.PurePosixPath(u).suffix.lower(), "files") for u in refs}
    summary = {"format": kinds.pop() if len(kinds) == 1 else "files",
               "path": relative(prefix, data_base), "url": prefix, "files": len(refs)}
    add_formats(summary, refs, data_base)
    return summary


MAGIC = {b"CDF\x01": "NetCDF-3 classic", b"CDF\x02": "NetCDF-3 64-bit offset",
         b"CDF\x05": "NetCDF-3 64-bit data (CDF-5)"}


def magic_format(head, key):
    if head[:4] in MAGIC:
        return MAGIC[head[:4]]
    if head[:8] == b"\x89HDF\r\n\x1a\n":
        return "NetCDF-4 (HDF5)" if FORMATS[pathlib.PurePosixPath(key).suffix.lower()] == "netcdf" else "HDF5"
    return f"unknown (first bytes {head[:8]!r})"


def file_formats(urls):
    """Format of the first and last file in each folder, from their first 8 bytes.

    Reading every file's header would cost one request per file (thousands); a provider that
    changes format usually does so between folders (years, versions), so ends of folders catch it.
    """
    folders = {}
    for key in urls:
        folders.setdefault(key.rpartition("/")[0], []).append(key)
    sample = {k for keys in folders.values() for k in (min(keys), max(keys))}
    if len(sample) < MIN_SAMPLE:  # one flat folder (pace-oci) would give only 2
        everything = sorted(urls)
        step = max(1, len(everything) // MIN_SAMPLE)
        sample |= set(everything[::step][:MIN_SAMPLE])
    sample = sorted(sample)
    if len(sample) > MAX_SAMPLE:  # noaa-oisst has 543 monthly folders; keep the requests bounded
        step = (len(sample) - 1) / (MAX_SAMPLE - 1)
        sample = [sample[round(i * step)] for i in range(MAX_SAMPLE)]
    formats = {}
    for key in sample:
        try:
            head, _ = http(key, {"Range": "bytes=0-7"})
            fmt = magic_format(head, key)
        except urllib.error.HTTPError as exc:
            # pace-oci: the store opens anonymously but NASA's bucket answers 403, so data reads
            # need credentials. Record it: the README must not say "No credentials".
            fmt = f"not readable anonymously (HTTP {exc.code})"
        entry = formats.setdefault(fmt, {"format": fmt, "files": 0, "first": key, "last": key})
        entry["files"] += 1
        entry["last"] = key
    spread = "" if len(sample) < MAX_SAMPLE else f", {MAX_SAMPLE} of them spread evenly"
    where = "the only folder" if len(folders) == 1 else f"each of {len(folders)} folders"
    if len(sample) > 2 * len(folders) or len(folders) == 1:
        where += " and others spread through it" if len(folders) == 1 else ", and others"
    return list(formats.values()), (f"first and last file in {where}{spread}, "
                                    f"{len(sample)} of {len(urls):,} files")


def newest(data):
    """The newest file: by the latest date in its name, else by LastModified.

    A date is YYYYMMDD, optionally with HH or HHMM (HYCOM: hycom_GLBv0.08_539_2015123012_t021.nc);
    ties go to the later name (the longer lead, t021 after t000).
    """
    def name_date(key):
        found = re.findall(r"(?<!\d)((?:19|20)\d{6}(?:\d{2}){0,2})(?!\d)", pathlib.PurePosixPath(key).name)
        return found[-1].ljust(12, "0") if found else None
    dated = [(name_date(k), k) for k, _, _ in data if name_date(k)]
    if len(dated) == len(data):
        return max(dated)[1], "filename date"
    if all(m for _, _, m in data):
        return max(data, key=lambda o: o[2])[0], "last modified"
    return max(k for k, _, _ in data), "last name"  # store references carry no dates


# --- NetCDF global attributes ------------------------------------------------------------

class RangeReader(io.RawIOBase):
    """Read-only file over HTTP range requests, so only the header bytes are fetched."""

    def __init__(self, url):
        self.url, self.pos = url, 0
        _, headers = http(url, method="HEAD")
        self.size = int(headers["Content-Length"])

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, offset, whence=0):
        self.pos = offset if whence == 0 else self.pos + offset if whence == 1 else self.size + offset
        return self.pos

    def readinto(self, buf):
        if self.pos >= self.size:
            return 0
        end = min(self.pos + len(buf), self.size) - 1
        data, _ = http(self.url, {"Range": f"bytes={self.pos}-{end}"})
        buf[:len(data)] = data
        self.pos += len(data)
        return len(data)


NC3_TYPES = {1: "b", 2: "c", 3: "h", 4: "i", 5: "f", 6: "d", 7: "B", 8: "H", 9: "I", 10: "q", 11: "Q"}


def nc3_attributes(f):
    """Global attributes from a NetCDF-3 header (classic, 64-bit offset or CDF-5)."""
    magic = f.read(4)
    big = magic == b"CDF\x05"  # CDF-5 widens counts to 64 bits
    count_fmt = ">q" if big else ">i"

    def read(fmt):
        size = struct.calcsize(fmt)
        return struct.unpack(fmt, f.read(size))

    def count():
        return read(count_fmt)[0]

    def name():
        n = count()
        text = f.read(n).decode("utf-8", "replace")
        f.read(-n % 4)
        return text

    count()  # numrecs
    tag, n = read(">i")[0], count()
    for _ in range(n if tag == 0x0A else 0):
        name()
        count()
    tag, n = read(">i")[0], count()
    attrs = {}
    for _ in range(n if tag == 0x0C else 0):
        key = name()
        code, n_values = read(">i")[0], count()
        fmt = NC3_TYPES[code]
        size = struct.calcsize(fmt) * n_values
        raw = f.read(size)
        f.read(-size % 4)
        if fmt == "c":
            attrs[key] = raw.rstrip(b"\0").decode("utf-8", "replace")
        else:
            vals = list(struct.unpack(f">{n_values}{fmt}", raw))
            attrs[key] = vals[0] if n_values == 1 else vals
    return attrs


def source_attributes(url):
    f = io.BufferedReader(RangeReader(url), buffer_size=1 << 20)
    magic = f.peek(8)[:8]
    if magic[:3] == b"CDF":
        attrs = nc3_attributes(f)
    elif magic == b"\x89HDF\r\n\x1a\n":
        try:
            import h5py
        except ImportError:
            raise CollectError(f"{url} is NetCDF-4/HDF5; reading its attributes needs h5py") from None
        with h5py.File(f, "r") as h:
            attrs = {k: jsonable(v) for k, v in h.attrs.items() if k not in NC_INTERNAL}
    else:
        raise CollectError(f"{url}: not a NetCDF file")
    return url, jsonable(attrs)


# --- one product -------------------------------------------------------------------------

def collect(product, data_base, max_refs=MAX_REFS):
    import zarr
    session, snap, containers, config = open_main(product["store_url"])
    last_update = snap.written_at.astimezone(dt.timezone.utc).date().isoformat()
    groups = array_groups(session.store)
    if not groups:
        raise CollectError(f"{product['store_url']}: main has no arrays")
    auto = {"_comment": f"Read from the store and its source files by collect_auto.py on "
                        f"{dt.date.today().isoformat()}; do not edit by hand."}
    variables, coordinates, ranges, group_attributes, steps = {}, {}, [], {}, []
    root = zarr.open_group(session.store, mode="r")
    for g in groups:
        ds, variables[g], coordinates[g] = group_values(session.store, g, last_update)
        ranges += time_range(ds)
        steps.append(time_steps(ds))
        if g != "/":
            # zarr, not ds.attrs: xarray moves a global 'coordinates' attribute into encoding.
            attrs = dict(root[g.lstrip("/")].attrs)
            if attrs:
                group_attributes[g] = jsonable(attrs)
    # Over every group: noaa-ohc's groups are eras (daily 2020-2024, 14day 2025-).
    auto["time_range"] = [min(ranges), max(ranges)] if ranges else []
    # Files the store actually uses, from its references: works on any host (CoastWatch, NCEI),
    # and counts what the store reads, not whatever else sits under the prefix.
    refs, notes = None, []
    if containers:
        n = chunk_count(session.store, groups)
        if n <= max_refs:
            refs = referenced_files(session, config)
        else:
            notes.append(f"references not counted: about {n:,} chunks, over --max-refs {max_refs:,}")
    data = None
    if product.get("source_url"):
        url = product["source_url"]
        url = url if url.endswith("/") else url + "/"
        try:
            auto["source_files"], data = source_files(url, data_base)
            auto["source_files"]["counted_from"] = "listing"
            if refs is not None:
                auto["source_files"]["referenced"] = len(refs)
        except NotListable as exc:
            notes.append(str(exc))
    if "source_files" not in auto and refs:
        auto["source_files"] = summary_from_references(refs, data_base)
        auto["source_files"]["counted_from"] = "store references"
        data = [(u, 0, "") for u in refs]
    if "source_files" not in auto and refs is None and containers and steps and None not in steps:
        # Too many references to list and no listing: estimate from the time axis (see time_steps).
        prefix = containers[0]
        auto["source_files"] = {"path": relative(prefix, data_base), "url": https_url(prefix, config),
                                "files": sum(steps),
                                "estimated": True, "counted_from": "time steps (one file per step)"}
        notes.append(f"source files estimated from {sum(steps):,} time steps, one file per step")
    refused = [f for f in (auto.get("source_files") or {}).get("formats", []) if f["format"].startswith("not readable")]
    if refused:
        notes.append(f"{sum(f['files'] for f in refused)} sampled source files refused an anonymous read; "
                     "data reads need credentials, so set access.auth in the source file")
    if notes:
        auto["_source_files"] = "; ".join(notes)
    auto.update(groups=groups, snapshot=snap.id, last_update=last_update,
                virtual_chunk_containers=containers,
                variables=variables, coordinates=coordinates,
                store_attributes=jsonable(dict(root.attrs)))
    if group_attributes:
        auto["group_attributes"] = group_attributes
    if (product.get("metadata") or {}).get("source_attributes"):
        if not data:
            raise CollectError("metadata.source_attributes is set but no source files were found")
        key, selected_by = newest(data)
        url, attrs = source_attributes(key)
        auto["source_attributes"] = {"file": pathlib.PurePosixPath(key).name, "url": url,
                                     "attributes": attrs, "selected_by": selected_by}
    return auto


def products_of(source):
    """(front matter that names the Source Coop product, product source files).

    A product with no `collection` stands alone (noaa-ohc, gobai-o2, noaa-oisst): it names its
    own Source Coop product and is the root of the README tree.
    """
    front = front_matter(source)
    if front.get("level") == "collection":
        return front, [(source.parent / f"{pid}.md") for pid in front.get("products") or []]
    if front.get("level") == "product":
        if not front.get("collection"):
            return front, [source]
        coll = (source.parent / front["collection"]).resolve()
        if not coll.is_file():
            raise CollectError(f"{source}: collection source {coll} not found")
        return front_matter(coll), [source]
    raise CollectError(f"{source}: level must be collection or product")


def stores_of(product):
    """[(json file stem, store fields)]: one store, or each of a standalone product's `stores`.

    A store in `stores` takes the product's fields, then its own (store_url, source_url, ...).
    """
    stores = [s for s in product.get("stores") or [] if isinstance(s, dict) and any(s.values())]
    if not stores:
        if not product.get("store_url"):
            raise CollectError("no store_url")
        return [(product["id"], product)]
    out = []
    for store in stores:
        if not store.get("id") or not store.get("store_url"):
            raise CollectError("every entry in stores needs id and store_url")
        out.append((f"{product['id']}.{store['id']}", {**product, **store}))
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("source", type=pathlib.Path, help="collection or product source file (.md)")
    parser.add_argument("--out", type=pathlib.Path, required=True, help="directory for <product id>.json (<product id>.<store id>.json for each of a product's stores)")
    parser.add_argument("--max-refs", type=int, default=MAX_REFS,
                        help=f"most chunk references to list when counting source files (default {MAX_REFS:,}, "
                             "about 1.2 GB of memory; each million needs about 0.4 GB)")
    args = parser.parse_args(argv)
    if not args.source.is_file():
        parser.error(f"{args.source}: not found")
    try:
        collection, sources = products_of(args.source)
        sc = collection["source_coop"]
        data_base = f"https://data.source.coop/{sc['account']}/{sc['product']}"
    except (CollectError, KeyError, TypeError) as exc:
        print(f"collect_auto: {exc}", file=sys.stderr)
        return 1
    args.out.mkdir(parents=True, exist_ok=True)
    status = 0
    for src in sources:
        try:
            product = front_matter(src)
            if not product.get("id"):
                raise CollectError("no id")
            stores = stores_of(product)
        except Exception as exc:
            print(f"collect_auto: {src}: {type(exc).__name__}: {exc}", file=sys.stderr)
            status = 1
            continue
        for stem, store in stores:
            try:
                auto = collect(store, data_base, args.max_refs)
            except Exception as exc:  # one unreadable store must not stop the others
                print(f"collect_auto: {src} ({stem}): {type(exc).__name__}: {exc}", file=sys.stderr)
                status = 1
                continue
            if auto.get("_source_files"):
                print(f"collect_auto: {stem}: {auto['_source_files']}", file=sys.stderr)
            if "source_files" not in auto:
                print(f"collect_auto: {stem}: no source_files", file=sys.stderr)
            path = args.out / f"{stem}.json"
            path.write_text(json.dumps(auto, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
            print(f"wrote {path}")
    return status


if __name__ == "__main__":
    sys.exit(main())
