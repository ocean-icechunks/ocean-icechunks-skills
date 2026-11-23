#!/usr/bin/env python3
"""Find the Icechunk stores and documentation in a Source Cooperative product and name its layout.

Reads anonymously and writes nothing: an S3 ListObjectsV2 listing over HTTPS of
https://data.source.coop/<account>/<product>/, and, with --groups, each store's group tree
through icechunk and zarr. Says which layout in references/layouts.md the product looks like,
how sure that is, what differs from the standard layout, and the moves that would fix it.

    scan_layout.py ocean-icechunks/pacioos
    scan_layout.py ocean-icechunks/noaa-ohc --groups
    scan_layout.py fish-pace/gobai-o2 --json

Needs Python 3.10+; --groups also needs icechunk and zarr. Exit status: 0 scanned,
1 the product could not be listed or holds no store, 2 usage error.
"""
import argparse
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

HOST = "https://data.source.coop"
NS = {"s3": "http://s3.amazonaws.com/doc/2006-03-01/"}
TIMEOUT = 60
# Folders that never hold a store: Icechunk's own, viewers, docs, copied source files.
SKIP = {"chunks", "manifests", "transactions", "snapshots", "refs", "overwritten", "viewer", "docs",
        "netcdf", "nc", "data", "assets", "static"}


class ScanError(Exception):
    pass


def listing(account, prefix):
    """(sub-folders, file names) directly under prefix, following continuation tokens."""
    folders, files, token = [], [], None
    while True:
        q = {"list-type": "2", "delimiter": "/", "prefix": prefix}
        if token:
            q["continuation-token"] = token
        url = f"{HOST}/{account}?{urllib.parse.urlencode(q)}"
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "scan_layout"}),
                                        timeout=TIMEOUT) as r:
                root = ET.fromstring(r.read())
        except (urllib.error.URLError, ET.ParseError) as exc:
            raise ScanError(f"{account}/{prefix}: cannot be listed ({exc})") from None
        folders += [p.findtext("s3:Prefix", namespaces=NS)[len(prefix):].rstrip("/")
                    for p in root.findall("s3:CommonPrefixes", NS)]
        files += [c.findtext("s3:Key", namespaces=NS)[len(prefix):] for c in root.findall("s3:Contents", NS)]
        token = root.findtext("s3:NextContinuationToken", namespaces=NS)
        if root.findtext("s3:IsTruncated", namespaces=NS) != "true" or not token:
            return folders, [f for f in files if f]


def is_store(folders, files):
    """An Icechunk repository: snapshots/ beside refs/ or manifests/, or its `repo` object (2.x)."""
    return "snapshots" in folders and ({"refs", "manifests"} & set(folders) or "repo" in files)


def walk(account, root, depth):
    """Every folder down to `depth` below root: {relative path: {folders, files, store}}."""
    found = {}

    def visit(rel, level):
        folders, files = listing(account, root + (rel + "/" if rel else ""))
        store = bool(is_store(folders, files))
        found[rel] = {"folders": folders, "files": files, "store": store}
        if store or level == depth:
            return
        for f in folders:
            sub = f"{rel}/{f}" if rel else f
            if f == "docs":  # its sub-folders say whether docs are kept per dataset (old hycom)
                found[sub] = dict(zip(("folders", "files"), listing(account, root + sub + "/")), store=False)
            elif f not in SKIP:
                visit(sub, level + 1)

    visit("", 0)
    return found


def groups_of(url):
    """Group paths that hold arrays, '/' first; needs icechunk and zarr."""
    import icechunk
    import zarr
    repo = icechunk.Repository.open(icechunk.http_storage(url))
    root = zarr.open_group(repo.readonly_session("main").store, mode="r")
    out = []

    def visit(g, path):
        if any(True for _ in g.array_keys()):
            out.append(path or "/")
        for name, sub in g.groups():
            visit(sub, f"{path}/{name}")

    visit(root, "")
    return out


def product_shape(stores, groups):
    """One of the four product shapes in references/layouts.md."""
    grouped = [s for s in stores if len(groups.get(s) or ["/"]) > 1]
    unknown = any(s not in groups for s in stores)
    if len(stores) == 1:
        if unknown:
            return "one store (groups not checked; --groups tells one-store from one-store-groups)"
        return "one-store-groups" if grouped else "one-store"
    if unknown:
        return "several-stores (groups not checked)"
    return "several-stores-groups" if grouped else "several-stores"


def classify(tree, groups=None):
    """The layout guess for a walked product: top level, products, moves to the standard layout."""
    groups = groups or {}
    stores = sorted(p for p, v in tree.items() if v["store"])
    if not stores:
        raise ScanError("no Icechunk store found")
    out = {"stores": stores, "deviations": [], "moves": [], "alternatives": []}
    std_standalone = all(re.fullmatch(r"icechunk(/[^/]+)?", s) for s in stores)
    std_collection = all(re.fullmatch(r"[^/]+/icechunk(/[^/]+)?", s) for s in stores)
    readme = lambda p: "README.md" in tree.get(p, {}).get("files", [])  # noqa: E731
    docs = lambda p: "docs" in tree.get(p, {}).get("folders", [])  # noqa: E731

    if std_standalone or std_collection:
        out["standard"] = True
        out["top"] = "standalone" if std_standalone else "collection"
        products = {"": stores} if std_standalone else {}
        if std_collection:
            for s in stores:
                products.setdefault(s.split("/")[0], []).append(s)
    else:
        out["standard"] = False
        top_level = [s for s in stores if "/" not in s]
        if stores == [""]:
            out["top"] = "standalone"
            products = {"": stores}
            out["deviations"].append("the product folder is itself the store: README.md and docs/ cannot sit beside it")
        elif len(stores) == len(top_level):
            # Stores directly under the product root (noaa-ohc, noaa-gomofs, gobai-o2, old hycom).
            per_store_docs = [s for s in stores if s in tree.get("docs", {}).get("folders", [])]
            if per_store_docs:  # hycom: docs/<dataset>/ for each store, so each store is a dataset
                out["top"] = "collection"
                products = {s: [s] for s in stores}
                out["alternatives"].append("standalone product with " + ("several stores" if len(stores) > 1 else "one store"))
                out["moves"] += [[f"docs/{s}", f"{s}/docs"] for s in per_store_docs]
            else:
                out["top"] = "standalone"
                products = {"": stores}
                if len(stores) > 1:
                    out["alternatives"].append("collection whose products are " + ", ".join(stores))
            out["deviations"].append("stores sit directly under the product root, not under icechunk/")
        else:
            # Deeper or mixed (pace-oci/inregion/<store>, <product>/<name>.icechunk): group by first folder.
            out["top"] = "collection" if len({s.split("/")[0] for s in stores}) > 1 else "standalone"
            products = {}
            for s in stores:
                head = s.split("/")[0] if out["top"] == "collection" else ""
                products.setdefault(head, []).append(s)
            heads = {s.split("/")[0] for s in stores}
            if out["top"] == "standalone" and heads != {"icechunk"}:  # pace-oci/inregion/<store>
                out["alternatives"].append(f"collection with product {heads.pop()}")
            out["deviations"].append("stores are not at <product>/icechunk[/<id>]")
    out["products"] = {}
    for p, ss in sorted(products.items()):
        if out["top"] == "collection" and not readme(p) and p:
            out["deviations"].append(f"{p}/ has no README.md")
        if out["top"] == "collection" and not docs(p) and p:
            out["deviations"].append(f"{p}/ has no docs/")
        out["products"][p or "."] = {"stores": ss, "shape": product_shape(ss, groups)}
        for s in ss:
            want = standard_place(p, s, len(ss))
            if s != want:
                out["moves"].append([s or ".", want])
    out["moves"].sort(key=lambda m: m[0].startswith("docs/"))  # a store moves before docs move into its folder
    if not readme(""):
        out["deviations"].append("no README.md at the product root")
    if not docs(""):
        out["deviations"].append("no docs/ at the product root")
    keep = {"README.md", "LICENSE", "LICENSE.md", "CITATION.cff"}
    loose = [f for f in tree[""]["files"] if f not in keep and not f.startswith(".")]
    if loose:
        out["deviations"].append("files at the root that belong in docs/: " + ", ".join(sorted(loose)))
    return out


def standard_place(product, store, n):
    """icechunk/ for a product's only store, icechunk/<id>/ for each of several."""
    base = f"{product}/icechunk" if product else "icechunk"
    if n == 1:
        return base
    name = store.rstrip("/").split("/")[-1]
    name = re.sub(r"\.icechunk$", "", name)
    return base if name == "icechunk" else f"{base}/{name}"


def report(path, out):
    lines = [path, f"  stores ({len(out['stores'])}): " + ", ".join(s or "(the root itself)" for s in out["stores"])]
    top = "collection of products" if out["top"] == "collection" else "standalone product"
    lines.append(f"  looks like: {top}" + ("" if out["standard"] else " (not in the standard places)"))
    for p, v in out["products"].items():
        label = "" if p == "." else f"{p}: "
        lines.append(f"    {label}{v['shape']}")
    for a in out["alternatives"]:
        lines.append(f"  could also be: {a} (ask)")
    for d in out["deviations"]:
        lines.append(f"  differs: {d}")
    for a, b in out["moves"]:
        lines.append(f"  move: {a}/ -> {b}/")
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("product", help="<account>/<product> on Source Cooperative, e.g. ocean-icechunks/pacioos")
    parser.add_argument("--depth", type=int, default=4, help="folders to descend looking for stores (default 4)")
    parser.add_argument("--groups", action="store_true", help="open each store to list its groups (needs icechunk, zarr)")
    parser.add_argument("--json", action="store_true", help="print JSON instead of text")
    args = parser.parse_args(argv)
    m = re.fullmatch(r"(?:https://(?:data\.)?source\.coop/)?([^/]+)/([^/]+)/?", args.product)
    if not m:
        parser.error("product must be <account>/<product>")
    account, product = m.groups()
    try:
        tree = walk(account, product + "/", args.depth)
        groups = {}
        if args.groups:
            for s in (p for p, v in tree.items() if v["store"]):
                groups[s] = groups_of(f"{HOST}/{account}/{product}" + (f"/{s}" if s else ""))
        out = classify(tree, groups)
    except ScanError as exc:
        print(f"scan_layout: {account}/{product}: {exc}", file=sys.stderr)
        return 1
    if args.groups:
        out["groups"] = groups
    print(json.dumps(out, indent=1) if args.json else report(f"{account}/{product}", out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
