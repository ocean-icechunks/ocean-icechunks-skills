#!/usr/bin/env python3
"""Render README.md and docs/ files for a collection or a product from its source file.

Needs Python 3.10+ and PyYAML; reads no store and makes no network request. Values the store
knows (variables, coordinates, groups, snapshot, last update, global attributes, time range,
source-file counts) come from one JSON file per product in --auto DIR, named <product id>.json.

    render_readme.py collection.md --auto auto/ --out out/pacioos/
    render_readme.py roms_hiig.md  --auto auto/ --out out/pacioos/roms_hiig/

A collection source writes OUT/README.md and OUT/docs/documentation.md; it reads each listed
product's source file (<id>.md beside the collection source, or in --products DIR) for that
product's row. A product source also writes OUT/docs/metadata.md. Field rules are in
../assets/schema.yaml. The output is deterministic: the same inputs give identical files.

Exit status: 0 rendered, 1 a source file failed validation, 2 usage error.
"""
import argparse
import html
import json
import pathlib
import re
import sys

import yaml

SCHEMA = pathlib.Path(__file__).resolve().parent.parent / "assets" / "schema.yaml"
LICENSES = {"Apache-2.0": "Apache License 2.0", "MIT": "MIT License",
            "BSD-3-Clause": "BSD 3-Clause License", "CC0-1.0": "CC0 1.0 Universal",
            "CC-BY-4.0": "Creative Commons Attribution 4.0"}
LANGUAGES = {"python": "Python", "r": "R", "matlab": "MATLAB", "julia": "Julia"}
FORMATS = {"netcdf": "NetCDF", "hdf5": "HDF5", "grib": "GRIB", "zarr": "Zarr"}
# Shown above the first call to the loader unless code.python.chunks_advice replaces it.
CHUNKS_ADVICE = ("Large Icechunk stores hold many chunk references. Open with chunks=None (the default),\n"
                 "subset, then call .chunk() on the subset if the work uses dask.")
INHERITED = ("provider", "repository", "code_license", "source_coop")


class SourceError(Exception):
    """A source file is incomplete or malformed; args are the messages."""


# ---------------------------------------------------------------- reading

def split_fenced(text, marker):
    """Split text at lines starting with `marker` (e.g. '# '), ignoring fenced code."""
    parts, current, heading, fence = [], [], None, False
    for line in text.splitlines():
        if line.startswith("```"):
            fence = not fence
        if not fence and line.startswith(marker) and not line.startswith(marker + "#"):
            parts.append((heading, "\n".join(current).strip()))
            heading, current = line[len(marker):].strip(), []
        else:
            current.append(line)
    parts.append((heading, "\n".join(current).strip()))
    return parts


def read_source(path):
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n") or "\n---\n" not in text[3:]:
        raise SourceError(f"{path}: must start with YAML front matter between '---' lines")
    end = text.index("\n---\n", 3)
    try:
        front = yaml.safe_load(text[4:end]) or {}
    except yaml.YAMLError as exc:
        raise SourceError(f"{path}: front matter is not valid YAML: {exc}") from None
    body = re.sub(r"<!--.*?-->", "", text[end + 5:], flags=re.S)
    parts = dict(split_fenced(body, "# "))
    readme = {h: t for h, t in split_fenced(parts.get("README", ""), "## ") if h and t}
    return front, readme, parts.get("Documentation", "")


def blank(value):
    return value is None or value == "" or value == [] or value == {} or value == [None]


def need(d, dotted, where, errors):
    value = d
    for key in dotted.split("."):
        value = value.get(key) if isinstance(value, dict) else None
    if blank(value):
        errors.append(f"{where}: missing required field '{dotted}'")
    return value


def check_schema(level, front, readme, documentation, where, context):
    """Required top-level fields and body sections, from schema.yaml."""
    schema = yaml.safe_load(SCHEMA.read_text(encoding="utf-8"))[level]
    errors = []
    if front.get("level") != level:
        errors.append(f"{where}: 'level' must be '{level}'")
    for name, rule in schema["front_matter"].items():
        required = rule.get("required", False)
        if isinstance(required, str):
            condition = CONDITIONS.get(required)
            if condition is None:
                raise SystemExit(f"schema.yaml: unknown condition {required!r}")
            required = condition(context)
        if required is True and blank(front.get(name)):
            errors.append(f"{where}: missing required field '{name}' ({rule.get('description', '')})".replace(" ()", ""))
    for heading, rule in schema["body"]["# README"].items():
        if rule.get("required") and heading[3:] not in readme:
            errors.append(f"{where}: missing required section '{heading}' under '# README'")
    if schema["body"]["# Documentation"].get("required") and not documentation:
        errors.append(f"{where}: missing '# Documentation' sections")
    return errors


CONDITIONS = {
    "if the collection has a viewer": lambda c: bool(c.get("collection_viewer")),
    "if the store has more than one group": lambda c: len(c.get("groups") or ["/"]) > 1,
}


def read_auto(auto_dir, pid, where):
    path = auto_dir / f"{pid}.json"
    if not path.is_file():
        raise SourceError(f"{where}: no store values for '{pid}': {path} not found")
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------- helpers

def urls(collection):
    sc = collection["source_coop"]
    path = f"{sc['account']}/{sc['product']}"
    return f"https://source.coop/{path}", f"https://data.source.coop/{path}"


def repo_name(url):
    return re.sub(r"^https?://github\.com/", "", url).rstrip("/")


def join_and(items):
    items = list(items)
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " and " + items[-1]


def row(cells):
    return "|" + "|".join(f" {c} " if str(c) != "" else " " for c in cells) + "|"


def table(header, rows):
    return "\n".join([row(header), "|" + "---|" * len(header)] + [row(r) for r in rows])


def viewer_link(base, store_url, variable, view):
    return f"{base}#icechunk+{store_url}::varname={variable}::{view}"


def browse_url(url):
    """Source Coop browse page for a data.source.coop URL; a browser gets 404 from the data URL."""
    return re.sub(r"^https://data\.source\.coop/", "https://source.coop/", url)


def time_coverage(auto):
    tr = auto.get("time_range") or []
    return f"{tr[0]} to {tr[1]}" if len(tr) == 2 else ""


def short_title(title):
    return title.split(":")[0].strip()


def license_name(spdx):
    return LICENSES.get(spdx, spdx)


def code_paragraph(lic, repository, plural):
    text = (f"**The code** that copied the files and built the {'stores' if plural else 'store'} "
            f"was written by {lic['author']} and is released under the {license_name(lic['spdx'])} "
            f"at [{repo_name(repository)}]({repository}).")
    if lic.get("attribution_required"):
        return text + f" Please credit {lic['author']} when reusing it."
    return text + " It can be used without attribution."


def data_citation(provider, what):
    url = provider.get("citation_url") or provider["data_services_url"]
    name = provider["name"]
    return f"**The data are {name}'s.** Any use of {what} should cite {name}, as described at <{url}>."


def cell(value):
    """Global-attribute cell: escaped so Markdown and HTML in values show literally."""
    if not isinstance(value, str):
        value = json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)
    value = html.escape(value)
    for character in "|\\`*_[]~":
        value = value.replace(character, f"&#{ord(character)};")
    return value.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "<br>")


def attribute_table(attributes):
    if not attributes:
        return "No global attributes."
    return table(["Attribute", "Value"],
                 [[f"<code>{cell(k)}</code>", f"<code>{cell(attributes[k])}</code>"] for k in sorted(attributes)])


def bullet(label, text):
    lines = text.strip().splitlines()
    return "\n".join([f"- {label} {lines[0]}"] + [f"  {line.strip()}" for line in lines[1:]])


def write(out, rel, sections):
    path = out / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n\n".join(s for s in sections if s) + "\n", encoding="utf-8")
    return path


def insert_extras(sections, extras, where, errors):
    """extra_sections: {after, heading, text}; inserted after the section headed `after`."""
    for extra in extras or []:
        block = f"## {extra.get('heading', '')}\n\n{extra.get('text', '').strip()}"
        anchors = [i for i, s in enumerate(sections) if s.startswith(f"## {extra.get('after')}\n")]
        if not anchors:
            errors.append(f"{where}: extra_sections 'after: {extra.get('after')}' matches no section")
            continue
        sections.insert(anchors[0] + 1, block)


# ---------------------------------------------------------------- collection

def render_collection(source, auto_dir, products_dir, out):
    where = source.name
    front, readme, documentation = read_source(source)
    errors = check_schema("collection", front, readme, documentation, where, {})
    if errors:
        raise SourceError(*errors)
    web, _ = urls(front)
    viewer = front.get("viewer") or {}
    provider = front["provider"]

    rows, access = [], []
    for pid in front["products"]:
        psrc = products_dir / f"{pid}.md"
        if not psrc.is_file():
            errors.append(f"{where}: product '{pid}' has no source file {psrc}")
            continue
        p, _, _ = read_source(psrc)
        pwhere = psrc.name
        for field in ("id", "title", "row.name", "row.detail", "row.short_name", "store_url", "code"):
            need(p, field, pwhere, errors)
        if viewer:
            need(p, "viewer.variable", pwhere, errors)
            need(p, "viewer.view", pwhere, errors)
        auto = read_auto(auto_dir, pid, pwhere)
        if errors:
            continue
        r, readme_url = p["row"], f"{web}/{pid}/README.md"
        data, files_link = [], ""
        sf = auto.get("source_files")
        if sf:
            fmt = sf.get("format", "files")
            # Counted from the store's references there is no size; a listing that finds more files
            # than the store uses says how many it uses.
            text = f"**{FORMATS.get(fmt, fmt)}:** `{sf['path']}`, {sf['files']:,} files"
            if sf.get("size"):
                text += f", {sf['size']}"
            if sf.get("referenced") not in (None, sf["files"]):
                text += f" ({sf['referenced']:,} used by the store)"
            data.append(text)
            if "://" in sf["path"]:  # files outside the collection, e.g. AWS (s3:// or https://)
                files_link = f"[{fmt}]({sf.get('url') or sf['path']})"
            else:
                files_link = f"[{fmt}]({web}/{sf['path'].rstrip('/')})"  # Source Coop redirects a trailing slash
        data.append(f"**Icechunk:** `{p['store_url']}`" + (f", {r['store_note']}" if r.get("store_note") else ""))
        if auto.get("last_update"):
            data.append(f"Updated {auto['last_update']}")
        rows.append([f"**{r['name']}** (`{pid}`), {r['detail']}", f"[README]({readme_url})",
                     r.get("time_coverage") or time_coverage(auto), "<br>".join(data)])
        code = ", ".join(f"[{LANGUAGES.get(lang, lang)}]({readme_url}#user-content-{lang})" for lang in p["code"])
        cells = [r["short_name"], f"[icechunk]({browse_url(p['store_url'])})", files_link]
        if viewer:
            v = p["viewer"]
            cells.append(f"[{viewer['name']}]({viewer_link(viewer['url'], p['store_url'], v['variable'], v['view'])})")
        access.append(cells + [code])
    if errors:
        raise SourceError(*errors)

    header = ([f"**[View data in browser](#data-access)**"] if viewer else []) + [
        "**[Data access (code)](#data-access)**",
        f"**[{provider['data_services_label']}]({provider['data_services_url']})**",
        f"**[Documentation]({web}/docs/documentation.md)**"]
    sections = [
        f"# {front['title']}",
        " · ".join(header),
        readme["Summary"],
        readme.get("Caveats", ""),
        table([f"Dataset ({provider['name']} id)", "About", "Time coverage", "Data"], rows),
        "## Data access",
        table(["Dataset", "Store", "Data files"] + (["Viewer"] if viewer else []) + ["Code"], access),
        "## Citation and reuse",
        readme.get("Citation") or data_citation(provider, "the NetCDF copies or the Icechunk stores"),
        code_paragraph(front["code_license"], front["repository"], plural=True),
        "## Credits",
        "\n".join(bullet(f"**{c['label']}:**", c["text"]) for c in front["credits"]),
    ]
    write(out, "README.md", sections)
    write(out, "docs/documentation.md", [
        f"# {short_title(front['title'])}: documentation",
        f"Technical detail for the [`{front['source_coop']['product']}` collection]({web}). "
        "The README has what most readers need; this page has the rest.",
        documentation])


# ---------------------------------------------------------------- product

def auth_lines(containers):
    """Loader lines that authorize the store's virtual chunk containers.

    Store values without the list (older JSON) get the HTTPS form; a materialized store (no
    containers) needs none; an s3:// container needs anonymous S3 credentials, which
    authorize_virtual_chunk_access accepts only through containers_credentials.
    """
    if containers is None:
        return ["    auth = {p: icechunk.credentials.HttpAccess for p in repo.config.virtual_chunk_containers or []}",
                "    repo = repo.reopen(authorize_virtual_chunk_access=auth)"]
    if not containers:
        return []
    if not any(c.startswith("s3://") for c in containers):
        return auth_lines(None)
    return ["    auth = icechunk.containers_credentials({",
            "        p: icechunk.s3_anonymous_credentials() if p.startswith(\"s3://\") else icechunk.credentials.HttpAccess",
            "        for p in repo.config.virtual_chunk_containers})",
            "    repo = repo.reopen(authorize_virtual_chunk_access=auth)"]


def python_section(p, examples, auto):
    py = p["code"]["python"]
    store = p["store_url"]
    needs = join_and([f"**Python {py['python_version']} or newer**"] + [f"`{x}`" for x in py["packages"]])
    access = p.get("access") or {}
    intro = f"Needs {needs}."
    if not access.get("auth"):
        intro += " No credentials and no account."
    extra = " ".join(x for x in (access.get("auth"), access.get("region")) if x)
    code = ["import icechunk"]
    if "np." in examples:
        code.append("import numpy as np")
    code += ["import xarray as xr", "import zarr", ""]
    if py.get("concurrency"):
        code += ["# Zarr's default of 10 concurrent reads is too low.",
                 f'zarr.config.set({{"async.concurrency": {py["concurrency"]}}})', ""]
    fn = py["function"]
    # A store whose arrays are in groups (noaa-ohc, noaa-oisst) opens as an empty root without one.
    # The first group in order.groups is the default; "/" (arrays at the root too) means None.
    groups = ordered_groups(p, auto) if len(auto.get("groups") or ["/"]) > 1 else []
    group_arg = ("group=None, " if groups[0] == "/" else f'group="{groups[0].lstrip("/")}", ') if groups else ""
    code += ["", f'def {fn}({group_arg}ref="main", chunks=None):',
             f'    """{py["docstring"]}"""',
             f'    url = "{store}"',
             "    repo = icechunk.Repository.open(icechunk.http_storage(url))"]
    code += auth_lines(auto.get("virtual_chunk_containers"))
    code += [
             "    tags = set(repo.list_tags())",
             "    session = repo.readonly_session(tag=ref) if ref in tags else repo.readonly_session(ref)",
             "    return xr.open_zarr(session.store, consolidated=False, chunks=chunks"
             + (", group=group)" if groups else ")"),
             "", ""]
    code += [f"# {line}" for line in (py.get("chunks_advice") or CHUNKS_ADVICE).strip().splitlines()]
    code += [f"ds = {fn}()", "print(ds)"]
    subset = ("**Subset, then chunk.** A large store holds many chunk references, and `chunks={}` "
              "makes one dask task for each, which is slow. Open with `chunks=None`, select what you "
              "need, then call `.chunk()` on the selection if the work uses dask.")
    if py.get("dask_example"):
        subset += f" {py['dask_example'].strip()}"
    return "\n\n".join(x for x in [
        "### Python", intro, extra, f"```bash\n{py['pip']}\n```",
        "**Open the dataset in xarray**", "```python\n" + "\n".join(code) + "\n```",
        subset, "**Example analyses**", examples] if x)


def ordered(items, names, key=lambda x: x["name"]):
    """Items named in `names` first, in that order; the rest after, in the store values' order."""
    rank = {n: i for i, n in enumerate(names or [])}
    return sorted(items, key=lambda x: rank.get(key(x), len(rank)))


def ordered_groups(p, auto):
    return ordered(auto.get("groups") or ["/"], (p.get("order") or {}).get("groups"), key=lambda g: g)


def order_errors(p, auto, where):
    """Names in the source's `order` that the store does not have (a typo would be silently ignored)."""
    errors = []
    for kind in ("variables", "coordinates", "groups"):
        if kind == "groups":
            have = set(auto.get("groups") or ["/"])
        else:
            have = {x["name"] for group in (auto.get(kind) or {}).values() for x in group}
        for name in ((p.get("order") or {}).get(kind) or []):
            if name not in have:
                errors.append(f"{where}: order.{kind} names '{name}', which the store does not have")
    return errors


def variables_section(p, auto, readme):
    groups = ordered_groups(p, auto)
    order = p.get("order") or {}
    notes, cnotes = p.get("variable_notes") or {}, p.get("coordinate_notes") or {}
    blocks = ["## Variables and coordinates"]
    if len(groups) > 1:
        blocks.append(p["groups_note"])
    for group in groups:
        if len(groups) > 1:
            blocks.append(f"### Group `{group}`")
        blocks.append(table(["Variable", "Dimensions", "Units", "Standard name"], [
            [f"`{v['name']}`", ", ".join(v["dims"]) or "scalar", v.get("units", ""),
             v.get("standard_name") or notes.get(v["name"]) or v.get("long_name", "")]
            for v in ordered(auto["variables"][group], order.get("variables"))]))
        coords = []
        for c in ordered(auto["coordinates"][group], order.get("coordinates")):
            size = f"on `{c['on']}`" if c.get("on") else f"{c['size']:,}" + (f" ({c['as_of']})" if c.get("as_of") else "")
            values = cnotes.get(c["name"]) or c.get("values", "")
            if not values and c.get("no_coordinate"):
                values = "index only (no coordinate variable)"
            coords.append([f"`{c['name']}`", size, values])
        blocks.append(table(["Coordinate", "Size", "Values"], coords))
    blocks.append(readme.get("Variable notes", ""))
    return "\n\n".join(b for b in blocks if b)


FORMAT_NOTES = {
    "NetCDF-3": "NetCDF-3 files are uncompressed and have no internal chunks: each variable is one "
                "contiguous block or, along the record (unlimited) dimension, one block per record "
                "interleaved with the other record variables.",
    "NetCDF-4": "NetCDF-4 files are HDF5 files. Their variables may be chunked and compressed; a "
                "compressed chunk can only be read whole, so the files' chunking sets the smallest read.",
}


def source_formats_section(auto):
    """Format of the source files, from collect_auto.py's sample of file headers."""
    sf = auto.get("source_files") or {}
    formats = sf.get("formats")
    if not formats:
        return ""
    rows = [[f["format"], f"{f['files']:,}", f"`{f['first']}`", f"`{f['last']}`"] for f in formats]
    notes = [text for prefix, text in FORMAT_NOTES.items() if any(f["format"].startswith(prefix) for f in formats)]
    if any(f["format"].startswith("not readable") for f in formats):
        notes.insert(0, "**Some source files refused an anonymous read.** Reading data from this store needs "
                        "credentials for the provider's files.")
    if len(formats) > 1:
        notes.insert(0, "**The files are not all in one format.** Code that opens them directly must handle each.")
    return "\n\n".join(["## Source file format",
                         table(["Format", "Files checked", "First", "Last"], rows),
                         f"Read from the first bytes of the {sf['formats_sampled']}."] + notes)


def with_source_formats(documentation, auto):
    """Put the source-format section in documentation.md unless the source already has one.

    {{source_formats}} places it; a '## Source file format' heading of the person's own keeps
    theirs; otherwise it goes after 'A virtual store', which every product has.
    """
    section = source_formats_section(auto)
    if "{{source_formats}}" in documentation:
        return documentation.replace("{{source_formats}}", section)
    if not section or re.search(r"^## Source file formats?\s*$", documentation, re.M):
        return documentation
    m = re.search(r"^## A virtual store\s*$", documentation, re.M)
    nxt = re.search(r"^## ", documentation[m.end():], re.M) if m else None
    if not nxt:
        return documentation.rstrip() + "\n\n" + section
    at = m.end() + nxt.start()
    return documentation[:at] + section + "\n\n" + documentation[at:]


def provenance_section(p, auto, readme, data_base):
    prov = p["provenance"]
    files = []
    for f in prov.get("build_files") or []:
        files.append(f"{f['label']} `{f['file']}`" if isinstance(f, dict) else f"`{f}`")
    lines = [
        bullet("**Source files:**", readme["Source files"]),
        f"- **Built** {prov['built']} by `{prov['build_script']}` in "
        f"[{repo_name(p['repository'])}]({prov['build_url']}). "
        f"Last update {auto['last_update']}, snapshot `{auto['snapshot']}`.",
        f"- **Tested with** {prov['tested_with']}.",
    ]
    if files:
        lines.append(f"- **Build files** (in [`docs/`]({data_base}/{p['id']}/docs/)): {join_and(files)}.")
    if prov.get("how_made"):
        how = prov["how_made"]
        line = f"- **How it was made, and how to rebuild it:** [`{how['file']}`]({how['url']})."
        if prov.get("plan"):
            line += f" The plan and decisions are in [{prov['plan']['label']}]({prov['plan']['url']})."
        lines.append(line)
    return "## Provenance\n\n" + "\n".join(lines)


def render_product(source, auto_dir, out):
    where = source.name
    front, readme, documentation = read_source(source)
    if blank(front.get("collection")):
        raise SourceError(f"{where}: missing required field 'collection'")
    cpath = (source.parent / front["collection"]).resolve()
    if not cpath.is_file():
        raise SourceError(f"{where}: collection source {front['collection']} not found")
    collection, _, _ = read_source(cpath)
    p = {**{k: collection.get(k) for k in INHERITED}, **front}
    cviewer = collection.get("viewer") or {}
    auto, errors = {}, []
    if blank(front.get("id")):
        errors.append(f"{where}: missing required field 'id'")
    else:
        try:
            auto = read_auto(auto_dir, front["id"], where)
        except SourceError as exc:
            errors.extend(exc.args)
    errors = check_schema("product", front, readme, documentation, where,
                          {"collection_viewer": cviewer, "groups": auto.get("groups")}) + errors
    if not blank(front.get("code")):
        for lang in front["code"]:
            if lang != "python":
                errors.append(f"{where}: no built-in snippet for code language '{lang}'; use extra_sections")
        for field in ("python_version", "packages", "pip", "function", "docstring"):
            need(front, f"code.python.{field}", where, errors)
    for field in ("rows", "measured"):
        need(front, f"performance.{field}", where, errors)
    for field in ("built", "build_script", "build_url", "tested_with"):
        need(front, f"provenance.{field}", where, errors)
    for field in ("snapshot", "last_update", "variables", "coordinates"):
        if auto and blank(auto.get(field)):
            errors.append(f"{where}: store values for '{front.get('id')}' lack '{field}'")
    if auto and "store_attributes" not in auto:  # {} is real: noaa-ohc keeps its attributes per group
        errors.append(f"{where}: store values for '{front.get('id')}' lack 'store_attributes'")
    if auto:
        errors += order_errors(front, auto, where)
        formats = (auto.get("source_files") or {}).get("formats") or []
        if any(f["format"].startswith("not readable") for f in formats) and not (front.get("access") or {}).get("auth"):
            # pace-oci: the README would otherwise promise "No credentials and no account".
            errors.append(f"{where}: some source files refused an anonymous read; set access.auth "
                          "to say what credentials reading the data needs")
    if not str(front.get("store_url", "")).startswith("https://"):
        errors.append(f"{where}: store_url must be a public https:// URL for the built-in loader")
    if errors:
        raise SourceError(*errors)

    web, data_base = urls(collection)
    pid = p["id"]
    perf = p["performance"]
    header = []
    if cviewer:
        v = p["viewer"]
        header.append(f"**[View data in browser]({viewer_link(cviewer['url'], p['store_url'], v['variable'], v['view'])})**")
    header.append("**[Data access (code)](#data-access-code)**")
    if p.get("provider_page"):
        header.append(f"**[{p['provider_page']['label']}]({p['provider_page']['url']})**")
    header += ["**[How to cite](#citation-and-reuse)**",
               f"**[Documentation]({web}/{pid}/docs/documentation.md)**",
               f"**[Metadata]({web}/{pid}/docs/metadata.md)**"]
    citation = data_citation(p["provider"], "this store or the NetCDF copies")
    if p.get("citation_extra"):
        citation += " " + p["citation_extra"].strip()
    sections = [
        f"# {p['title']}",
        " · ".join(header),
        readme["Summary"],
        f"```\n{p['store_url']}\n```",
        f"Updated {auto['last_update']}.",
        readme.get("Notes", ""),
        variables_section(p, auto, readme),
        "## Data access (code)\n\n" + python_section(p, readme["Example analyses"], auto),
        "## Performance\n\n" + table(["Read", "Chunks", "Data moved", "Time (measured)"], [
            [r["read"], f"{r['chunks']:,}" if isinstance(r["chunks"], int) else r["chunks"],
             r["data_moved"], r["time"]] for r in perf["rows"]])
        + f"\n\nMeasured {perf['measured']}. Rates elsewhere will differ.",
        provenance_section(p, auto, readme, data_base),
        ("## Caveats\n\n" + readme["Caveats"]) if readme.get("Caveats") else "",
        "## Citation and reuse\n\n" + citation + "\n\n"
        + code_paragraph(p["code_license"], p["repository"], plural=False),
    ]
    insert_extras(sections, p.get("extra_sections"), where, errors)
    if errors:
        raise SourceError(*errors)
    write(out, "README.md", sections)

    fields = (p.get("viewer") or {}).get("fields") or []
    viewer_table = table(["Field", "Viewer"], [
        [f["label"], f"[Open `{f['variable']}`]({viewer_link(cviewer['url'], p['store_url'], f['variable'], f.get('view') or p['viewer']['view'])})"]
        for f in fields]) if (fields and cviewer) else ""
    write(out, "docs/documentation.md", [
        f"# {short_title(p['title'])}: documentation",
        f"Technical detail for the [`{pid}` Icechunk store]({web}/{pid}). "
        "The README has what most readers need; this page has the rest.",
        with_source_formats(documentation, auto).replace("{{viewer_fields_table}}", viewer_table)])

    nc = (auto.get("netcdf_attributes") or {}) if (p.get("metadata") or {}).get("netcdf_attributes") else {}
    note = ("_Generated from the store and the latest NetCDF copy on each update. " if nc
            else "_Generated from the store on each update. ")
    meta = [f"# {short_title(p['title'])}: global metadata attributes",
            note + "Do not edit by hand; `ds.attrs` shows the current set._",
            "## Published Icechunk dataset",
            f"Store: [{p['store_url']}]({p['store_url']}); snapshot <code>{cell(auto['snapshot'])}</code>.",
            attribute_table(auto["store_attributes"])]
    gattrs = auto.get("group_attributes") or {}
    if gattrs and not auto["store_attributes"]:
        meta[-1] = "The root group has no attributes; each group has its own."
    for group in ordered_groups(p, auto):
        if group in gattrs:
            meta += [f"### Group `{group}`", attribute_table(gattrs[group])]
    if nc:
        meta += ["## Latest completed NetCDF copy",
                 f"File: [{nc['file']}]({nc['url']}). Selected by {nc.get('selected_by', 'date')}. "
                 "These are file attributes; other files may have different values.",
                 attribute_table(nc["attributes"])]
    write(out, "docs/metadata.md", meta)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("source", type=pathlib.Path, help="collection or product source file (.md)")
    parser.add_argument("--auto", type=pathlib.Path, required=True, help="directory of <product id>.json store values")
    parser.add_argument("--out", type=pathlib.Path, required=True, help="output directory")
    parser.add_argument("--products", type=pathlib.Path, help="directory of product source files (default: beside the collection source)")
    args = parser.parse_args(argv)
    if not args.source.is_file():
        parser.error(f"{args.source}: not found")
    try:
        front, _, _ = read_source(args.source)
        if front.get("level") == "collection":
            render_collection(args.source, args.auto, args.products or args.source.parent, args.out)
        elif front.get("level") == "product":
            render_product(args.source, args.auto, args.out)
        else:
            raise SourceError(f"{args.source.name}: 'level' must be 'collection' or 'product'")
    except SourceError as exc:
        for message in exc.args:
            print(f"error: {message}", file=sys.stderr)
        return 1
    print(f"rendered {args.source.name} into {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
