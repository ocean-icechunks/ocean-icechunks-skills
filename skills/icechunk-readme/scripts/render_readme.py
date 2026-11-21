#!/usr/bin/env python3
"""Render README.md and docs/ files for a collection or a product from its source file.

Needs Python 3.10+ and PyYAML; reads no store and makes no network request. Values the store
knows (variables, coordinates, groups, snapshot, last update, global attributes, dates, NetCDF
file counts) come from one JSON file per product in --auto DIR, named <product id>.json.

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
        data = []
        if auto.get("netcdf"):
            nc = auto["netcdf"]
            data.append(f"**NetCDF:** `{nc['path']}`, {nc['files']:,} files, {nc['size']}")
        data.append(f"**Icechunk:** `{p['store_url']}`" + (f", {r['store_note']}" if r.get("store_note") else ""))
        rows.append([f"**{r['name']}** (`{pid}`), {r['detail']}", f"[README]({readme_url})",
                     auto.get("dates", ""), "<br>".join(data)])
        code = ", ".join(f"[{LANGUAGES.get(lang, lang)}]({readme_url}#user-content-{lang})" for lang in p["code"])
        cells = [r["short_name"]]
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
        table([f"Dataset ({provider['name']} id)", "About", "Dates", "Data"], rows),
        "## Data access",
        table(["Dataset"] + (["Viewer"] if viewer else []) + ["Code"], access),
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

def python_section(p, examples):
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
    code += ["", f'def {fn}(ref="main", chunks=None):',
             f'    """{py["docstring"]}"""',
             f'    url = "{store}"',
             "    repo = icechunk.Repository.open(icechunk.http_storage(url))",
             "    auth = {p: icechunk.credentials.HttpAccess for p in repo.config.virtual_chunk_containers or []}",
             "    repo = repo.reopen(authorize_virtual_chunk_access=auth)",
             "    tags = set(repo.list_tags())",
             "    session = repo.readonly_session(tag=ref) if ref in tags else repo.readonly_session(ref)",
             "    return xr.open_zarr(session.store, consolidated=False, chunks=chunks)",
             "", ""]
    if py.get("chunks_advice"):
        code += [f"# {line}" for line in py["chunks_advice"].strip().splitlines()]
    code += [f"ds = {fn}()", "print(ds)"]
    opening = p.get("performance", {}).get("open_time")
    return "\n\n".join(x for x in [
        "### Python", intro, extra, f"```bash\n{py['pip']}\n```",
        "**Open the dataset in xarray**", "```python\n" + "\n".join(code) + "\n```",
        f"Opening takes {opening} and reads only metadata." if opening else "",
        "**Example analyses**", examples] if x)


def variables_section(p, auto, readme):
    groups = auto.get("groups") or ["/"]
    notes, cnotes = p.get("variable_notes") or {}, p.get("coordinate_notes") or {}
    blocks = ["## Variables and coordinates"]
    if len(groups) > 1:
        blocks.append(p["groups_note"])
    for group in groups:
        if len(groups) > 1:
            blocks.append(f"### Group `{group}`")
        blocks.append(table(["Variable", "Dimensions", "Units", "Standard name"], [
            [f"`{v['name']}`", ", ".join(v["dims"]), v.get("units", ""),
             v.get("standard_name") or notes.get(v["name"], "")] for v in auto["variables"][group]]))
        coords = []
        for c in auto["coordinates"][group]:
            size = f"on `{c['on']}`" if c.get("on") else f"{c['size']:,}" + (f" ({c['as_of']})" if c.get("as_of") else "")
            coords.append([f"`{c['name']}`", size, cnotes.get(c["name"]) or c.get("values", "")])
        blocks.append(table(["Coordinate", "Size", "Values"], coords))
    blocks.append(readme.get("Variable notes", ""))
    return "\n\n".join(b for b in blocks if b)


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
    for field in ("snapshot", "last_update", "variables", "coordinates", "store_attributes"):
        if auto and blank(auto.get(field)):
            errors.append(f"{where}: store values for '{front.get('id')}' lack '{field}'")
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
        readme.get("Notes", ""),
        variables_section(p, auto, readme),
        "## Data access (code)\n\n" + python_section(p, readme["Example analyses"]),
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
        documentation.replace("{{viewer_fields_table}}", viewer_table)])

    nc = (auto.get("netcdf_attributes") or {}) if (p.get("metadata") or {}).get("netcdf_attributes") else {}
    note = ("_Generated from the store and the latest NetCDF copy on each update. " if nc
            else "_Generated from the store on each update. ")
    meta = [f"# {short_title(p['title'])}: global metadata attributes",
            note + "Do not edit by hand; `ds.attrs` shows the current set._",
            "## Published Icechunk dataset",
            f"Store: [{p['store_url']}]({p['store_url']}); snapshot <code>{cell(auto['snapshot'])}</code>.",
            attribute_table(auto["store_attributes"])]
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
