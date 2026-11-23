#!/usr/bin/env python3
"""Tests of skills/icechunk-layout/scripts/scan_layout.py.

Offline: classify() on folder trees shaped like real Source Cooperative products. Live
(skipped with ICECHUNK_LAYOUT_OFFLINE=1): scans of products whose layout is known, read
anonymously. Needs Python 3.10+; the live --groups test also needs icechunk and zarr.

    python3 -I -B evals/icechunk-layout/test_scan.py
"""
import importlib.util
import os
import pathlib
import sys
import unittest

sys.dont_write_bytecode = True  # keep __pycache__ out of the skill bundle
ROOT = pathlib.Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("scan_layout", ROOT / "skills/icechunk-layout/scripts/scan_layout.py")
scan = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scan)
OFFLINE = os.environ.get("ICECHUNK_LAYOUT_OFFLINE") == "1"
STORE = {"folders": ["manifests", "refs", "snapshots", "transactions"], "files": ["repo"], "store": True}


def tree(**folders):
    """{path: listing}; a value of STORE marks a store, a list gives that folder's files."""
    out = {}
    for path, value in folders.items():
        path = "" if path == "root" else path.replace("__", "/")
        out[path] = value if isinstance(value, dict) else {"folders": [], "files": value, "store": False}
    for path in list(out):  # parents list their children
        if path:
            parent, _, name = path.rpartition("/")
            out.setdefault(parent, {"folders": [], "files": [], "store": False})["folders"].append(name)
    return out


class Offline(unittest.TestCase):
    def test_standard_collection(self):
        t = tree(root=["README.md"], docs=[], a=["README.md"], a__docs=[], a__icechunk=STORE,
                 b=["README.md"], b__docs=[], b__icechunk__x=STORE, b__icechunk__y=STORE)
        t["b/icechunk"] = {"folders": ["x", "y"], "files": [], "store": False}
        out = scan.classify(t, {"a/icechunk": ["/"], "b/icechunk/x": ["/"], "b/icechunk/y": ["/", "/g"]})
        self.assertTrue(out["standard"])
        self.assertEqual(out["top"], "collection")
        self.assertEqual(out["products"]["a"]["shape"], "one-store")
        self.assertEqual(out["products"]["b"]["shape"], "several-stores-groups")
        self.assertEqual(out["moves"], [])
        self.assertEqual(out["deviations"], [])

    def test_stores_at_root_standalone(self):
        """noaa-ohc: regions at the root, build files loose, no docs/."""
        t = tree(root=["README.md", "icechunk_utils.py", "requirements.txt"], na=STORE, np=STORE, viewer=[])
        out = scan.classify(t)
        self.assertEqual(out["top"], "standalone")
        self.assertFalse(out["standard"])
        self.assertEqual(out["moves"], [["na", "icechunk/na"], ["np", "icechunk/np"]])
        self.assertIn("collection whose products are na, np", out["alternatives"][0])
        self.assertTrue(any("icechunk_utils.py, requirements.txt" in d for d in out["deviations"]))

    def test_docs_per_dataset_means_collection(self):
        """Old hycom: the store at the root, its docs in docs/<dataset>/."""
        t = tree(root=["README.md", "LICENSE"], docs__ds=["README.md"], ds=STORE)
        out = scan.classify(t)
        self.assertEqual(out["top"], "collection")
        self.assertEqual(out["moves"], [["ds", "ds/icechunk"], ["docs/ds", "ds/docs"]])
        self.assertFalse(any("LICENSE" in d for d in out["deviations"]))

    def test_one_store_renamed(self):
        """noaa-oisst, txla-roms: one store with a .icechunk suffix goes to icechunk/."""
        out = scan.classify(tree(root=["README.md"], docs=[], **{"oisst.icechunk": STORE}), {"oisst.icechunk": ["/daily", "/monthly"]})
        self.assertEqual(out["products"]["."]["shape"], "one-store-groups")
        self.assertEqual(out["moves"], [["oisst.icechunk", "icechunk"]])

    def test_extra_level_offers_collection(self):
        """pace-oci: stores under inregion/."""
        t = tree(root=["README.md"], inregion__CHL=STORE, inregion__KD=STORE)
        out = scan.classify(t)
        self.assertIn("collection with product inregion", out["alternatives"])
        self.assertEqual(out["moves"][0], ["inregion/CHL", "icechunk/CHL"])

    def test_no_store(self):
        with self.assertRaises(scan.ScanError):
            scan.classify(tree(root=["README.md"]))


@unittest.skipIf(OFFLINE, "ICECHUNK_LAYOUT_OFFLINE=1")
class Live(unittest.TestCase):
    def test_pacioos_is_a_standard_collection(self):
        out = scan.classify(scan.walk("ocean-icechunks", "pacioos/", 4))
        self.assertEqual(out["top"], "collection")
        self.assertTrue(out["standard"])
        self.assertIn("roms_hiig/icechunk", out["stores"])

    def test_ohc_with_groups(self):
        t = scan.walk("ocean-icechunks", "noaa-ohc/", 4)
        stores = [p for p, v in t.items() if v["store"]]
        groups = {s: scan.groups_of(f"{scan.HOST}/ocean-icechunks/noaa-ohc/{s}") for s in stores}
        out = scan.classify(t, groups)
        self.assertEqual(out["top"], "standalone")
        self.assertEqual(out["products"]["."]["shape"], "several-stores-groups")
        self.assertEqual(sorted(groups["na"]), ["/14day", "/14day_v1", "/daily"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
