#!/usr/bin/env python3
"""Offline tests of skills/icechunk-readme/scripts/render_readme.py.

Renders the PacIOOS collection and its roms_hiig product from pacioos/source/ with the frozen
store values in pacioos/auto/, and compares the result with the hand-made files in
pacioos/expected/. Line wrapping inside paragraphs is ignored (it does not change the rendered
page); everything else must match. Needs PyYAML; no network.

    python3 -I evals/icechunk-readme/test_render.py
"""
import contextlib
import importlib.util
import io
import json
import pathlib
import shutil
import sys
import tempfile
import unittest

import yaml

sys.dont_write_bytecode = True  # keep __pycache__ out of the skill bundle
ROOT = pathlib.Path(__file__).resolve().parents[2]
SKILL = ROOT / "skills/icechunk-readme"
HERE = pathlib.Path(__file__).resolve().parent / "pacioos"
spec = importlib.util.spec_from_file_location("render_readme", SKILL / "scripts/render_readme.py")
render = importlib.util.module_from_spec(spec)
spec.loader.exec_module(render)

FILES = {
    "collection": ["README.md", "docs/documentation.md"],
    "product": ["README.md", "docs/documentation.md", "docs/metadata.md"],
}


def unwrap(text):
    """Join soft-wrapped lines; keep code blocks, tables, headings and list items as lines."""
    out, fence = [], False
    for raw in text.splitlines():
        line = raw.rstrip()
        if line.startswith("```"):
            fence = not fence
            out.append(line)
            continue
        if fence:
            out.append(line)
            continue
        prev = out[-1] if out else ""
        if line and prev and not prev.startswith(("|", "#", "```")) and not line.startswith(("|", "#", "- ", "```")):
            out[-1] = prev + " " + line.strip()
        else:
            out.append(line.strip())
    return "\n".join(out).strip() + "\n"


def run(*argv):
    err = io.StringIO()
    with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
        status = render.main([str(a) for a in argv])
    return status, err.getvalue()


class RenderPacIOOS(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)

    def render_both(self, out):
        self.assertEqual(run(HERE / "source/collection.md", "--auto", HERE / "auto", "--out", out)[0], 0)
        self.assertEqual(run(HERE / "source/roms_hiig.md", "--auto", HERE / "auto", "--out", out / "roms_hiig")[0], 0)

    def test_matches_expected(self):
        out = self.tmp / "pacioos"
        self.render_both(out)
        for prefix, level in (("", "collection"), ("roms_hiig/", "product")):
            for name in FILES[level]:
                with self.subTest(file=prefix + name):
                    expected = (HERE / "expected" / (prefix + name)).read_text(encoding="utf-8")
                    got = (out / (prefix + name)).read_text(encoding="utf-8")
                    self.assertEqual(unwrap(got), unwrap(expected))

    def test_deterministic(self):
        self.render_both(self.tmp / "a")
        self.render_both(self.tmp / "b")
        for path in sorted((self.tmp / "a").rglob("*.md")):
            with self.subTest(file=str(path.relative_to(self.tmp / "a"))):
                self.assertEqual(path.read_bytes(), (self.tmp / "b" / path.relative_to(self.tmp / "a")).read_bytes())

    def edited(self, name, old, new):
        """Copy the source tree with one edit to one file; return the copied file's path."""
        src = self.tmp / "src"
        shutil.copytree(HERE / "source", src)
        path = src / name
        text = path.read_text(encoding="utf-8")
        self.assertIn(old, text)
        path.write_text(text.replace(old, new, 1), encoding="utf-8")
        return path

    def test_missing_required_field(self):
        path = self.edited("roms_hiig.md", "store_url: https://", "# store_url: https://")
        status, err = run(path, "--auto", HERE / "auto", "--out", self.tmp / "out")
        self.assertEqual(status, 1)
        self.assertIn("missing required field 'store_url'", err)
        self.assertFalse((self.tmp / "out/README.md").exists())

    def test_missing_nested_field(self):
        path = self.edited("roms_hiig.md", "    function: open_forecast\n", "")
        status, err = run(path, "--auto", HERE / "auto", "--out", self.tmp / "out")
        self.assertEqual(status, 1)
        self.assertIn("'code.python.function'", err)

    def test_missing_body_section(self):
        path = self.edited("roms_hiig.md", "## Example analyses", "## Examples")
        status, err = run(path, "--auto", HERE / "auto", "--out", self.tmp / "out")
        self.assertEqual(status, 1)
        self.assertIn("'## Example analyses'", err)

    def test_collection_names_product_without_source(self):
        path = self.edited("collection.md", "  - wrf_hi\n", "  - wrf_hi\n  - no_such_product\n")
        status, err = run(path, "--auto", HERE / "auto", "--out", self.tmp / "out")
        self.assertEqual(status, 1)
        self.assertIn("'no_such_product' has no source file", err)

    def test_partial_product_cannot_render_alone(self):
        status, err = run(HERE / "source/wrf_hi.md", "--auto", HERE / "auto", "--out", self.tmp / "out")
        self.assertEqual(status, 1)
        self.assertIn("missing required section '## Summary'", err)

    def auto_copy(self, edit):
        """Copy the auto/ fixtures, apply edit(dict) to roms_hiig.json; return the directory."""
        auto = self.tmp / "auto"
        shutil.copytree(HERE / "auto", auto)
        path = auto / "roms_hiig.json"
        values = json.loads(path.read_text(encoding="utf-8"))
        edit(values)
        path.write_text(json.dumps(values), encoding="utf-8")
        return auto

    def product_files(self, source, auto):
        out = self.tmp / "out"
        status, err = run(source, "--auto", auto, "--out", out)
        self.assertEqual(status, 0, err)
        return ((out / "README.md").read_text(encoding="utf-8"),
                (out / "docs/documentation.md").read_text(encoding="utf-8"))

    def test_order_overrides_store_order(self):
        def shuffle(values):
            values["variables"]["/"].reverse()
            values["coordinates"]["/"].reverse()
        auto = self.auto_copy(shuffle)
        readme, _ = self.product_files(HERE / "source/roms_hiig.md", auto)
        expected = (HERE / "expected/roms_hiig/README.md").read_text(encoding="utf-8")
        self.assertEqual(unwrap(readme), unwrap(expected))

    def test_order_names_unknown_variable(self):
        path = self.edited("roms_hiig.md", "variables: [temp,", "variables: [tmep,")
        status, err = run(path, "--auto", HERE / "auto", "--out", self.tmp / "out")
        self.assertEqual(status, 1)
        self.assertIn("order.variables names 'tmep'", err)

    def test_source_format_section(self):
        _, doc = self.product_files(HERE / "source/roms_hiig.md", HERE / "auto")
        self.assertEqual(doc.count("## Source file format"), 1)
        # A hand-written section of the same name replaces the generated one.
        path = self.edited("roms_hiig.md", "## What the store adds over the files",
                           "## Source file format\n\nHand-written.\n\n## What the store adds over the files")
        _, doc = self.product_files(path, HERE / "auto")
        self.assertEqual(doc.count("## Source file format"), 1)
        self.assertIn("Hand-written.", doc)
        self.assertNotIn("Files checked", doc)

    def test_source_format_mixed(self):
        def mixed(values):
            f = values["source_files"]["formats"]
            f.append({**f[0], "format": "NetCDF-4 (HDF5)"})
        _, doc = self.product_files(HERE / "source/roms_hiig.md", self.auto_copy(mixed))
        self.assertIn("not all in one format", doc)
        self.assertIn("NetCDF-4 files are HDF5", doc)

    def test_blank_templates_fail_cleanly(self):
        for name in ("collection-template.md", "product-template.md"):
            with self.subTest(template=name):
                src = self.tmp / name
                shutil.copy(SKILL / "assets" / name, src)
                if name.startswith("product"):
                    shutil.copy(SKILL / "assets/collection-template.md", self.tmp / "collection.md")
                    src.write_text(src.read_text(encoding="utf-8").replace("../collection.md", "collection.md"), encoding="utf-8")
                status, err = run(src, "--auto", HERE / "auto", "--out", self.tmp / "out")
                self.assertEqual(status, 1)
                self.assertIn("missing required field 'title'", err)


class Schema(unittest.TestCase):
    def test_templates_and_sources_use_only_schema_fields(self):
        schema = yaml.safe_load((SKILL / "assets/schema.yaml").read_text(encoding="utf-8"))
        files = [SKILL / "assets/collection-template.md", SKILL / "assets/product-template.md",
                 *sorted((HERE / "source").glob("*.md"))]
        for path in files:
            with self.subTest(file=path.name):
                front, _, _ = render.read_source(path)
                unknown = set(front) - set(schema[front["level"]]["front_matter"])
                self.assertEqual(unknown, set())

    def test_templates_list_every_writable_field(self):
        schema = yaml.safe_load((SKILL / "assets/schema.yaml").read_text(encoding="utf-8"))
        for level in ("collection", "product"):
            with self.subTest(level=level):
                front, _, _ = render.read_source(SKILL / f"assets/{level}-template.md")
                writable = {k for k, v in schema[level]["front_matter"].items() if v.get("source") != "inherit"}
                self.assertEqual(set(front), writable)


if __name__ == "__main__":
    unittest.main(verbosity=2)
