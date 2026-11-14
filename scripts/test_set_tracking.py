#!/usr/bin/env python3
"""Checks GA and Search Console staging without writing a real ID into the repo."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import set_tracking
import tracking_util


class TrackingUtilTests(unittest.TestCase):
    def test_ga_rules(self) -> None:
        self.assertFalse(tracking_util.valid_ga("G-XXXXXXXXXX"))
        self.assertFalse(tracking_util.valid_ga("G-abc"))
        self.assertFalse(tracking_util.valid_ga("UA-123456"))
        self.assertTrue(tracking_util.valid_ga("G-TEST1234"))

    def test_replace_only_the_assignment(self) -> None:
        source = 'var GA_ID = "G-XXXXXXXXXX";\nvar LIVE = /^G-[A-Z0-9]{6,}$/.test(GA_ID) && GA_ID !== "G-XXXXXXXXXX";\n'
        updated = tracking_util.replace_ga_id(source, "G-TEST1234")
        self.assertIn('var GA_ID = "G-TEST1234";', updated)
        self.assertIn('GA_ID !== "G-XXXXXXXXXX"', updated)

    def test_gsc_kinds(self) -> None:
        self.assertEqual(tracking_util.classify_gsc("google1234abcd.html"), "file")
        self.assertEqual(tracking_util.classify_gsc("abcDEFghi_12-zz"), "meta")
        with self.assertRaises(ValueError):
            tracking_util.classify_gsc("short")
        with self.assertRaises(ValueError):
            tracking_util.classify_gsc("has space token")

    def test_verification_body(self) -> None:
        self.assertEqual(
            tracking_util.verification_body("google1234abcd.html"),
            "google-site-verification: google1234abcd.html\n",
        )

    def test_meta_inject_is_idempotent(self) -> None:
        page = '<head><meta charset="utf-8"><title>Hi</title></head>'
        once = tracking_util.apply_gsc_meta(page, "abcDEFghi_12")
        twice = tracking_util.apply_gsc_meta(once, "abcDEFghi_12")
        self.assertEqual(once, twice)
        self.assertIn('<meta name="google-site-verification" content="abcDEFghi_12">', once)
        self.assertEqual(once.count("google-site-verification"), 1)
        self.assertEqual(tracking_util.apply_gsc_meta(page, None), page)


class StageTests(unittest.TestCase):
    def _root(self, tmp: str) -> Path:
        root = Path(tmp)
        (root / "assets").mkdir()
        (root / "scripts" / "templates").mkdir(parents=True)
        (root / "assets" / "track.js").write_text(
            'var GA_ID = "G-XXXXXXXXXX"; // placeholder\n',
            encoding="utf-8",
        )
        (root / "index.html").write_text(
            '<html><head><meta charset="utf-8"><title>Home</title></head><body></body></html>',
            encoding="utf-8",
        )
        (root / "scripts" / "templates" / "post.html").write_text(
            '<html><head><meta charset="utf-8">%%TITLE%%</head></html>',
            encoding="utf-8",
        )
        return root

    def test_stage_file_verification_without_build(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = self._root(tmp)
            set_tracking.stage(root, "G-TEST1234", "google1234abcd.html", run_build=False)
            track = (root / "assets" / "track.js").read_text(encoding="utf-8")
            self.assertIn('var GA_ID = "G-TEST1234";', track)
            body = (root / "google1234abcd.html").read_text(encoding="utf-8")
            self.assertEqual(body, "google-site-verification: google1234abcd.html\n")
            self.assertFalse((root / "scripts" / "gsc-meta.txt").exists())

    def test_stage_meta_token_without_build(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = self._root(tmp)
            (root / "googleoldfile.html").write_text("stale\n", encoding="utf-8")
            set_tracking.stage(root, None, "metaToken_1234", run_build=False)
            self.assertEqual((root / "scripts" / "gsc-meta.txt").read_text(encoding="utf-8").strip(), "metaToken_1234")
            self.assertFalse((root / "googleoldfile.html").exists())

    def test_refuses_placeholder_ga(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = self._root(tmp)
            with self.assertRaises(ValueError):
                set_tracking.stage(root, "G-XXXXXXXXXX", None, run_build=False)


if __name__ == "__main__":
    unittest.main()
