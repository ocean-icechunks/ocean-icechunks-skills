#!/usr/bin/env python3
"""Tests of skills/icechunk-readme/scripts/collect_auto.py.

The offline tests check the NetCDF-3 header parser and the text helpers. The live tests read
the four public PacIOOS stores on Source Cooperative (anonymous HTTPS, read only), so they
need the network and check structure, not exact dates or counts: the stores update daily.
They also render the collection and roms_hiig from what was read, and compare the stable
values of roms_hiig with the frozen fixture in pacioos/auto/.

    python3 -I evals/icechunk-readme/test_collect.py

Needs the packages in requirements.txt. Set ICECHUNK_README_OFFLINE=1 to skip the live tests.
"""
import contextlib
import importlib.util
import io
import json
import os
import pathlib
import re
import struct
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True  # keep __pycache__ out of the skill bundle
ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "skills/icechunk-readme/scripts"
HERE = pathlib.Path(__file__).resolve().parent / "pacioos"
OFFLINE = os.environ.get("ICECHUNK_README_OFFLINE") == "1"


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


collect = load("collect_auto")
render = load("render_readme")


def quiet(fn, argv):
    err = io.StringIO()
    with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
        status = fn([str(a) for a in argv])
    return status, err.getvalue()


def nc3_header(magic=b"CDF\x01"):
    """A minimal NetCDF-3 header: one dimension, three global attributes, no variables."""
    wide = magic == b"CDF\x05"
    n = (lambda v: struct.pack(">q", v)) if wide else (lambda v: struct.pack(">i", v))

    def name(text):
        b = text.encode()
        return n(len(b)) + b + b"\0" * (-len(b) % 4)
    out = magic + n(0)
    out += struct.pack(">i", 0x0A) + n(1) + name("time") + n(0)
    out += struct.pack(">i", 0x0C) + n(3)
    out += name("title") + struct.pack(">i", 2) + n(6) + b"Zlevel" + b"\0" * 2
    out += name("version") + struct.pack(">i", 4) + n(1) + struct.pack(">i", 7)
    out += name("bounds") + struct.pack(">i", 6) + n(2) + struct.pack(">2d", -1.5, 2.25)
    out += struct.pack(">i", 0) + n(0)  # no variables
    return out


class Offline(unittest.TestCase):
    def test_nc3_attributes(self):
        for magic in (b"CDF\x01", b"CDF\x02", b"CDF\x05"):
            with self.subTest(magic=magic):
                attrs = collect.nc3_attributes(io.BytesIO(nc3_header(magic)))
                self.assertEqual(list(attrs), ["title", "version", "bounds"])
                self.assertEqual(attrs["title"], "Zlevel")
                self.assertEqual(attrs["version"], 7)
                self.assertEqual(attrs["bounds"], [-1.5, 2.25])

    def test_number_and_size(self):
        self.assertEqual(collect.number(-163.8307), "−163.83")
        self.assertEqual(collect.number(5500.0), "5500")
        self.assertEqual(collect.number(0.25), "0.25")
        self.assertEqual(collect.size_text(1.25e12), "1.25 TB")
        self.assertEqual(collect.size_text(4.6e11), "0.46 TB")
        self.assertEqual(collect.size_text(3e9), "3.00 GB")

    def test_newest(self):
        data = [("a/2026/x_20261118.nc", 1, "2026-11-19T00:00:00Z"),
                ("a/2026/x_20261120.nc", 1, "2026-11-12T00:00:00Z")]
        self.assertEqual(collect.newest(data), ("a/2026/x_20261120.nc", "filename date"))
        data.append(("a/extra.nc", 1, "2026-11-21T00:00:00Z"))
        self.assertEqual(collect.newest(data), ("a/extra.nc", "last modified"))

    def test_netcdf_url_outside_collection(self):
        with self.assertRaises(collect.CollectError):
            collect.source_files("https://data.source.coop/other/x/netcdf/",
                                 "https://data.source.coop/ocean-icechunks/pacioos")


DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@unittest.skipIf(OFFLINE, "ICECHUNK_README_OFFLINE=1")
class Live(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.auto = pathlib.Path(cls.tmp.name) / "auto"
        cls.status, cls.err = quiet(collect.main, [HERE / "source/collection.md", "--out", cls.auto])

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def read(self, pid):
        return json.loads((self.auto / f"{pid}.json").read_text(encoding="utf-8"))

    def test_every_product_written(self):
        self.assertEqual(self.status, 0, self.err)
        for pid in ("roms_hiig", "roms_hiig_reanalysis", "wrf_hi", "ww3_hawaii"):
            with self.subTest(pid=pid):
                a = self.read(pid)
                self.assertEqual(len(a["time_range"]), 2)
                self.assertTrue(all(DATE.match(d) for d in a["time_range"] + [a["last_update"]]))
                self.assertLessEqual(*a["time_range"])
                self.assertRegex(a["snapshot"], r"^[0-9A-Z]{20}$")
                self.assertEqual(a["groups"], ["/"])
                sf = a["source_files"]
                self.assertEqual(sf["format"], "netcdf")
                self.assertTrue(sf["path"].startswith(pid + "/") and sf["path"].endswith("/"))
                self.assertGreater(sf["files"], 100)
                self.assertRegex(sf["size"], r"^\d+\.\d\d [TGM]B$")
                fmt = {"roms_hiig": "NetCDF-3 classic", "ww3_hawaii": "NetCDF-3 classic",
                       "wrf_hi": "NetCDF-4 (HDF5)", "roms_hiig_reanalysis": "NetCDF-4 (HDF5)"}[pid]
                self.assertEqual([f["format"] for f in sf["formats"]], [fmt])
                self.assertTrue(sf["formats"][0]["first"].startswith(sf["path"]))
                variables, coords = a["variables"]["/"], a["coordinates"]["/"]
                self.assertTrue(variables and coords)
                names = {c["name"] for c in coords}
                for v in variables:
                    self.assertTrue(set(v["dims"]) <= names, v)
                time = next(c for c in coords if c["name"] == "time")
                self.assertEqual(time["as_of"], a["last_update"])
                self.assertGreater(len(a["store_attributes"]), 10)

    def test_stable_values_match_fixture(self):
        live, frozen = self.read("roms_hiig"), json.loads((HERE / "auto/roms_hiig.json").read_text())
        pick = lambda vs: {v["name"]: {k: v.get(k) or "" for k in ("dims", "units", "standard_name")}  # noqa: E731
                           for v in vs}
        self.assertEqual(pick(live["variables"]["/"]), pick(frozen["variables"]["/"]))
        stable = lambda cs: {c["name"]: {k: c.get(k) for k in ("on", "values") if k in c}  # noqa: E731
                             for c in cs if c["name"] != "time"}
        self.assertEqual(stable(live["coordinates"]["/"]), stable(frozen["coordinates"]["/"]))
        self.assertEqual(set(live["store_attributes"]), set(frozen["store_attributes"]))
        self.assertEqual(live["source_files"]["path"], frozen["source_files"]["path"])
        nc = live["netcdf_attributes"]
        self.assertEqual(nc["selected_by"], "filename date")
        self.assertEqual(set(nc["attributes"]), set(frozen["netcdf_attributes"]["attributes"]))
        self.assertGreaterEqual(nc["file"], frozen["netcdf_attributes"]["file"])

    def test_renders_from_collected_values(self):
        out = pathlib.Path(self.tmp.name) / "out"
        status, err = quiet(render.main, [HERE / "source/collection.md", "--auto", self.auto, "--out", out])
        self.assertEqual(status, 0, err)
        status, err = quiet(render.main, [HERE / "source/roms_hiig.md", "--auto", self.auto,
                                          "--out", out / "roms_hiig"])
        self.assertEqual(status, 0, err)
        readme = (out / "roms_hiig/README.md").read_text(encoding="utf-8")
        self.assertIn(self.read("roms_hiig")["snapshot"], readme)

    def test_hdf5_attributes(self):
        """wrf_hi files are NetCDF-4/HDF5, unlike roms_hiig's NetCDF-3, so h5py reads them."""
        endpoint, objects = collect.list_prefix("https://data.source.coop/ocean-icechunks/pacioos/wrf_hi/netcdf/2017/")
        key = next(k for k, _, _ in objects if k.endswith(".nc"))
        _, attrs = collect.netcdf_attributes(endpoint, key)
        self.assertIn("title", attrs)
        self.assertFalse(set(attrs) & collect.NC_INTERNAL)


if __name__ == "__main__":
    unittest.main(verbosity=2)
