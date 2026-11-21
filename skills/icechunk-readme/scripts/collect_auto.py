#!/usr/bin/env python3
"""Read the values a README needs from each Icechunk store and write <product id>.json files.

Writes the --auto directory that render_readme.py takes. Every read is anonymous HTTPS: the
store's main branch through Icechunk, the source-file prefix through an S3 ListObjectsV2
listing, and, when a product asks for it, the header of its newest NetCDF file through range
requests. Nothing is written anywhere but --out.

    collect_auto.py collection.md --out auto/            every product the collection lists
    collect_auto.py roms_hiig.md  --out auto/            one product

Needs Python 3.10+, PyYAML, icechunk, xarray and zarr; h5py too when a product sets
metadata.netcdf_attributes and its newest file is NetCDF-4/HDF5 (NetCDF-3 headers are parsed
here). The source-file prefix is the product's netcdf_url; without it, source_files is left out.

Exit status: 0 written, 1 a product could not be read (others are still written), 2 usage error.
"""
import argparse
import datetime as dt
import io
import json
import math
import pathlib
import re
import struct
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

import yaml

FORMATS = {".nc": "netcdf", ".nc4": "netcdf", ".cdf": "netcdf", ".h5": "hdf5", ".hdf5": "hdf5", ".he5": "hdf5"}
UNITS = {"degrees_north": "°N", "degree_north": "°N", "degrees_east": "°E", "degree_east": "°E"}
# Attributes the netCDF library adds to a NetCDF-4 file; xarray hides them, and so do we.
NC_INTERNAL = {"_NCProperties", "_nc3_strict", "_IsNetcdf4", "_SuperblockVersion"}
TIMEOUT = 60


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
    auth = {p: icechunk.credentials.HttpAccess for p in repo.config.virtual_chunk_containers or []}
    repo = repo.reopen(authorize_virtual_chunk_access=auth)
    snap = next(iter(repo.ancestry(branch="main")))
    return repo.readonly_session("main"), snap


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
        lo, hi = var.values.min(), var.values.max()
        return time_text(lo) if lo == hi else f"{time_text(lo)} to {time_text(hi)}"
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
        if d in ds.coords:
            c = {"name": d, "size": int(ds.sizes[d])}
            if np.issubdtype(ds[d].dtype, np.datetime64):
                c["as_of"] = last_update
            c["values"] = values_text(ds[d])
            coords.append(c)
        for n in sorted(ds.coords):
            if n not in ds.dims and ds[n].dims and ds[n].dims[0] == d:
                coords.append({"name": n, "on": ", ".join(ds[n].dims), "values": ""})
    for n in sorted(ds.coords):
        if not ds[n].dims:
            coords.append({"name": n, "size": 1, "values": values_text(ds[n])})
    return ds, variables, coords


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

def split_s3_url(url):
    """https://data.source.coop/<bucket>/<key prefix> -> (listing endpoint, bucket, prefix)."""
    u = urllib.parse.urlsplit(url)
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
        body, _ = http(f"{endpoint}?{urllib.parse.urlencode(q)}")
        root = ET.fromstring(body)
        for c in root.findall("s3:Contents", ns):
            objects.append((c.findtext("s3:Key", namespaces=ns), int(c.findtext("s3:Size", namespaces=ns)),
                            c.findtext("s3:LastModified", namespaces=ns)))
        token = root.findtext("s3:NextContinuationToken", namespaces=ns)
        if root.findtext("s3:IsTruncated", namespaces=ns) != "true" or not token:
            return endpoint, objects


def size_text(n):
    for unit, scale in (("TB", 1e12), ("GB", 1e9), ("MB", 1e6)):
        if n >= scale / 100 or unit == "MB":
            return f"{n / scale:.2f} {unit}"


def source_files(netcdf_url, data_base):
    if not netcdf_url.startswith(data_base + "/"):
        raise CollectError(f"netcdf_url {netcdf_url} is not under the collection {data_base}/")
    endpoint, objects = list_prefix(netcdf_url)
    data = [o for o in objects if pathlib.PurePosixPath(o[0]).suffix.lower() in FORMATS]
    if not data:
        raise CollectError(f"no data files (.nc, .h5, ...) under {netcdf_url}")
    kinds = {FORMATS[pathlib.PurePosixPath(k).suffix.lower()] for k, _, _ in data}
    summary = {"format": kinds.pop() if len(kinds) == 1 else "files",
               "path": netcdf_url[len(data_base) + 1:],
               "files": len(data),
               "size": size_text(sum(s for _, s, _ in data))}
    formats, summary["formats_sampled"] = file_formats(endpoint, data)
    rel = lambda key: f"{endpoint}/{key}"[len(data_base) + 1:]  # noqa: E731  same base as "path"
    summary["formats"] = [{**f, "first": rel(f["first"]), "last": rel(f["last"])} for f in formats]
    return summary, endpoint, data


MAGIC = {b"CDF\x01": "NetCDF-3 classic", b"CDF\x02": "NetCDF-3 64-bit offset",
         b"CDF\x05": "NetCDF-3 64-bit data (CDF-5)"}


def magic_format(head, key):
    if head[:4] in MAGIC:
        return MAGIC[head[:4]]
    if head[:8] == b"\x89HDF\r\n\x1a\n":
        return "NetCDF-4 (HDF5)" if FORMATS[pathlib.PurePosixPath(key).suffix.lower()] == "netcdf" else "HDF5"
    return f"unknown (first bytes {head[:8]!r})"


def file_formats(endpoint, data):
    """Format of the first and last file in each folder, from their first 8 bytes.

    Reading every file's header would cost one request per file (thousands); a provider that
    changes format usually does so between folders (years, versions), so ends of folders catch it.
    """
    folders = {}
    for key, _, _ in data:
        folders.setdefault(key.rpartition("/")[0], []).append(key)
    sample = sorted({k for keys in folders.values() for k in (min(keys), max(keys))})
    formats = {}
    for key in sample:
        head, _ = http(f"{endpoint}/{key}", {"Range": "bytes=0-7"})
        fmt = magic_format(head, key)
        entry = formats.setdefault(fmt, {"format": fmt, "files": 0, "first": key, "last": key})
        entry["files"] += 1
        entry["last"] = key
    return list(formats.values()), (f"first and last file in each of {len(folders)} folders, "
                                    f"{len(sample)} of {len(data)} files")


def newest(data):
    """The newest file: by the latest YYYYMMDD date in its name, else by LastModified."""
    def name_date(key):
        found = re.findall(r"(?<!\d)((?:19|20)\d{6})(?!\d)", pathlib.PurePosixPath(key).name)
        return found[-1] if found else None
    dated = [(name_date(k), k) for k, _, _ in data if name_date(k)]
    if len(dated) == len(data):
        return max(dated)[1], "filename date"
    return max(data, key=lambda o: o[2])[0], "last modified"


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


def netcdf_attributes(endpoint, key):
    url = f"{endpoint}/{key}"
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

def collect(product, data_base):
    import zarr
    session, snap = open_main(product["store_url"])
    last_update = snap.written_at.astimezone(dt.timezone.utc).date().isoformat()
    groups = array_groups(session.store)
    if not groups:
        raise CollectError(f"{product['store_url']}: main has no arrays")
    auto = {"_comment": f"Read from the store and its source files by collect_auto.py on "
                        f"{dt.date.today().isoformat()}; do not edit by hand."}
    variables, coordinates, first = {}, {}, None
    for g in groups:
        ds, variables[g], coordinates[g] = group_values(session.store, g, last_update)
        first = first if first is not None else ds
    auto["time_range"] = time_range(first)
    data = None
    if product.get("netcdf_url"):
        auto["source_files"], endpoint, data = source_files(product["netcdf_url"].rstrip("/") + "/", data_base)
    auto.update(groups=groups, snapshot=snap.id, last_update=last_update,
                variables=variables, coordinates=coordinates,
                # zarr, not ds.attrs: xarray moves a global 'coordinates' attribute into encoding.
                store_attributes=jsonable(dict(zarr.open_group(session.store, mode="r").attrs)))
    if (product.get("metadata") or {}).get("netcdf_attributes"):
        if not data:
            raise CollectError("metadata.netcdf_attributes is set but there is no netcdf_url to read from")
        key, selected_by = newest(data)
        url, attrs = netcdf_attributes(endpoint, key)
        auto["netcdf_attributes"] = {"file": pathlib.PurePosixPath(key).name, "url": url,
                                     "attributes": attrs, "selected_by": selected_by}
    return auto


def products_of(source):
    front = front_matter(source)
    if front.get("level") == "collection":
        return front, [(source.parent / f"{pid}.md") for pid in front.get("products") or []]
    if front.get("level") == "product":
        coll = (source.parent / front.get("collection", "")).resolve()
        if not coll.is_file():
            raise CollectError(f"{source}: collection source {coll} not found")
        return front_matter(coll), [source]
    raise CollectError(f"{source}: level must be collection or product")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("source", type=pathlib.Path, help="collection or product source file (.md)")
    parser.add_argument("--out", type=pathlib.Path, required=True, help="directory for <product id>.json")
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
            for field in ("id", "store_url"):
                if not product.get(field):
                    raise CollectError(f"no {field}")
            auto = collect(product, data_base)
        except Exception as exc:  # one unreadable store must not stop the others
            print(f"collect_auto: {src}: {type(exc).__name__}: {exc}", file=sys.stderr)
            status = 1
            continue
        if "source_files" not in auto:
            print(f"collect_auto: {src}: no netcdf_url, so no source_files", file=sys.stderr)
        path = args.out / f"{product['id']}.json"
        path.write_text(json.dumps(auto, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"wrote {path}")
    return status


if __name__ == "__main__":
    sys.exit(main())
