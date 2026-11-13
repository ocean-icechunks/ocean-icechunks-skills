#!/usr/bin/env python3
"""Offline test of skills/archive-to-cloud/scripts/verify_copy.py.

Runs a tiny local stand-in for a public S3 bucket (paginated ListObjectsV2 and GET), so every
outcome can be produced: OK, BAD, NO-MD5, MISSING, EXTRA, SIZE. Standard library only.

    python3 -I evals/archive-to-cloud/test_verify_copy.py
"""
import contextlib
import hashlib
import importlib.util
import io
import pathlib
import sys
import tempfile
import threading
import unittest
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from xml.sax.saxutils import escape

sys.dont_write_bytecode = True  # keep __pycache__ out of the skill bundle
ROOT = pathlib.Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "verify_copy", ROOT / "skills/archive-to-cloud/scripts/verify_copy.py")
verify_copy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verify_copy)

BUCKET = "acct"
PAGE = 2  # small, to exercise continuation tokens


def md5(b):
    return hashlib.md5(b).hexdigest()


def build_objects():
    good, bad, nomd5 = b"good bytes" * 100, b"changed bytes", b"interrupted"
    sizey = b"twelve bytes"
    return {
        "p/netcdf/2020/a.nc": good,
        "p/netcdf/2020/a.nc.md5": ("%s  a.nc\n" % md5(good)).encode(),
        "p/netcdf/2020/b.nc": bad,
        "p/netcdf/2020/b.nc.md5": ("%s  b.nc\n" % md5(b"original bytes")).encode(),
        "p/netcdf/2020/c.nc": nomd5,
        "p/netcdf/2021/d e.nc": sizey,  # a space, to check URL quoting
        "p/netcdf/2021/d e.nc.md5": ("%s  d e.nc\n" % md5(sizey)).encode(),
        "p/netcdf/README.md": b"not data",
        "p/icechunk/repo": b"store object",
    }


class Bucket(BaseHTTPRequestHandler):
    objects = {}
    seen_agents = []

    def log_message(self, *args):
        pass

    def do_GET(self):
        self.seen_agents.append(self.headers.get("User-Agent", ""))
        u = urllib.parse.urlsplit(self.path)
        path = urllib.parse.unquote(u.path)
        q = urllib.parse.parse_qs(u.query)
        if path == "/" + BUCKET and q.get("list-type") == ["2"]:
            return self.listing(q.get("prefix", [""])[0], q.get("continuation-token", [None])[0])
        key = path[len(BUCKET) + 2:]
        if path.startswith("/%s/" % BUCKET) and key in self.objects:
            body = self.objects[key]
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_error(404)

    def listing(self, prefix, token):
        keys = sorted(k for k in self.objects if k.startswith(prefix))
        start = int(token) if token else 0
        page, more = keys[start:start + PAGE], start + PAGE < len(keys)
        items = "".join("<Contents><Key>%s</Key><Size>%d</Size></Contents>"
                        % (escape(k), len(self.objects[k])) for k in page)
        nxt = "<NextContinuationToken>%d</NextContinuationToken>" % (start + PAGE) if more else ""
        body = ('<?xml version="1.0"?><ListBucketResult '
                'xmlns="http://s3.amazonaws.com/doc/2006-03-01/">%s<IsTruncated>%s</IsTruncated>%s'
                '</ListBucketResult>' % (items, "true" if more else "false", nxt)).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/xml")
        self.end_headers()
        self.wfile.write(body)


class VerifyCopyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Bucket.objects = build_objects()
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Bucket)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.url = "http://127.0.0.1:%d/%s/p/netcdf/" % (cls.server.server_port, BUCKET)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def run_verify(self, *args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            status = verify_copy.main([self.url, *args])
        return status, out.getvalue()

    def lines(self, text, tag):
        return [l for l in text.splitlines() if l.startswith(tag + " ")]

    def test_full_check(self):
        status, out = self.run_verify()
        self.assertEqual(status, 1)
        self.assertIn("4 data files", out)  # README.md and icechunk/ are not data
        self.assertEqual(len(self.lines(out, "OK")), 2)  # a.nc, and "d e.nc" (quoted URL)
        self.assertEqual(len(self.lines(out, "BAD")), 1)
        self.assertIn("2020/b.nc", self.lines(out, "BAD")[0])
        self.assertEqual(len(self.lines(out, "NO-MD5")), 1)
        self.assertIn("2 problems", out)

    def test_list_only_downloads_nothing(self):
        status, out = self.run_verify("--list-only")
        self.assertEqual(status, 1)  # c.nc has no sidecar
        self.assertFalse(self.lines(out, "OK") or self.lines(out, "BAD"))

    def test_manifest(self):
        with tempfile.NamedTemporaryFile("w", suffix=".tsv", delete=False) as f:
            f.write("2020/a.nc\t1000\n"      # matches
                    "2020/b.nc\t13\n"        # matches size (bytes differ: found only by download)
                    "2020/c.nc\t11\n"
                    "2021/d e.nc\t999\n"     # size differs
                    "2022/missing.nc\t5\n")  # never copied
        status, out = self.run_verify("--list-only", "--manifest", f.name)
        pathlib.Path(f.name).unlink()
        self.assertEqual(status, 1)
        self.assertEqual(self.lines(out, "MISSING"), ["MISSING  2022/missing.nc  size=5"])
        self.assertEqual(self.lines(out, "SIZE"), ["SIZE     2021/d e.nc  copy=12 source=999"])
        self.assertEqual(self.lines(out, "EXTRA"), [])
        self.assertIn("5 files on the source, 4 copied", out)

    def test_sample_is_repeatable(self):
        _, one = self.run_verify("--sample", "1", "--seed", "7")
        _, two = self.run_verify("--sample", "1", "--seed", "7")
        pick = lambda t: [l.split()[1] for l in t.splitlines() if l.split()[0] in ("OK", "BAD")]
        self.assertEqual(len(pick(one)), 1)
        self.assertEqual(pick(one), pick(two))

    def test_glob_and_clean_pass(self):
        status, out = self.run_verify("--glob", "a.nc")
        self.assertEqual(status, 0)
        self.assertIn("0 problems", out)

    def test_user_agent_is_not_pythons_default(self):
        self.run_verify("--list-only")
        self.assertTrue(Bucket.seen_agents)
        self.assertFalse(any(a.startswith("Python-urllib") for a in Bucket.seen_agents))

    def test_bad_url_and_failed_listing_exit_2(self):
        err = io.StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(verify_copy.main(["not-a-url"]), 2)
            port = self.server.server_port
            self.assertEqual(verify_copy.main(["http://127.0.0.1:%d/nobucket/x/" % port]), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
