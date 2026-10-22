from __future__ import annotations

import argparse
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from ztypy import slipify


class SlipifyTests(unittest.TestCase):
    def test_parse_adjacency_layout_collects_all_nodes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "layout.txt"
            path.write_text("A\n  B\nC\n", encoding="utf-8")
            self.assertEqual(slipify.parse_adjacency_layout(path)[1], {"A", "B", "C"})

    def test_parse_adjacency_layout_raises_for_orphan_child(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "layout.txt"
            path.write_text("  B\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                slipify.parse_adjacency_layout(path)

    def test_generate_note_ids_preserves_count(self) -> None:
        self.assertEqual(len(slipify.generate_note_ids(["A", "B"])), 2)

    def test_phase_1_create_files_creates_expected_count(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            notes = {"A": slipify.Note("A", "20260101010101")}
            slipify.phase_1_create_files(Path(temp_dir), notes)
            self.assertEqual(len(list(Path(temp_dir).glob("*.typ"))), 1)

    def test_phase_2_add_titles_writes_title(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            notes = {"A": slipify.Note("A", "20260101010101")}
            out = Path(temp_dir)
            slipify.phase_1_create_files(out, notes)
            slipify.phase_2_add_titles(out, notes)
            content = (out / "20260101010101.typ").read_text(encoding="utf-8")
            self.assertIn('#let title = "A"', content)

    def test_phase_3_add_links_writes_child_id(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            notes = {
                "A": slipify.Note("A", "20260101010101"),
                "B": slipify.Note("B", "20260101010102"),
            }
            out = Path(temp_dir)
            slipify.phase_1_create_files(out, notes)
            slipify.phase_2_add_titles(out, notes)
            slipify.phase_3_add_links(out, notes, {"A": ["B"], "B": []})
            content = (out / "20260101010101.typ").read_text(encoding="utf-8")
            self.assertIn("- 20260101010102:B", content)

    def test_phase_3_add_links_preserves_titles_with_colons_and_deduplicates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            notes = {
                "A": slipify.Note("A", "20260101010101"),
                "Group action: intro": slipify.Note(
                    "Group action: intro", "20260101010102"
                ),
            }
            out = Path(temp_dir)
            slipify.phase_1_create_files(out, notes)
            slipify.phase_3_add_links(
                out, notes, {"A": ["Group action: intro", "Group action: intro"]}
            )
            content = (out / "20260101010101.typ").read_text(encoding="utf-8")
            self.assertEqual(content.count("- 20260101010102:Group action: intro"), 1)

    def test_build_slip_layout_text_uses_typ_filenames(self) -> None:
        notes = {
            "A": slipify.Note("A", "20260101010101"),
            "B": slipify.Note("B", "20260101010102"),
        }
        text = slipify.build_slip_layout_text({"A": ["B"], "B": []}, notes)
        self.assertIn("20260101010101.typ", text)

    def test_run_raises_for_missing_layout_file(self) -> None:
        with self.assertRaises(FileNotFoundError):
            slipify.run("/definitely/missing-layout.txt")

    def test_run_creates_slip_layout_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            layout = root / "layout.txt"
            layout.write_text("A\n  B\n", encoding="utf-8")

            with patch("ztypy.slipify.datetime") as mocked_datetime:
                mocked_datetime.now.return_value = datetime(
                    2026, 1, 1, 1, 1, 1, tzinfo=timezone.utc
                )
                slipify.run(str(layout), str(root / "out"))

            self.assertTrue((root / "layout.slip.txt").exists())

    def test_add_subparser_registers_slipify(self) -> None:
        parser = argparse.ArgumentParser()
        subs = parser.add_subparsers(dest="command")
        slipify.add_subparser(subs)
        args = parser.parse_args(["slipify", "layout.txt"])
        self.assertTrue(callable(args.func))


if __name__ == "__main__":
    unittest.main()
