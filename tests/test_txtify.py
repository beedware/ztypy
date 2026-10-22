from __future__ import annotations

import argparse
import tempfile
import unittest
from pathlib import Path

from ztypy import txtify


class TxtifyTests(unittest.TestCase):
    def test_extract_title_returns_title(self) -> None:
        content = '#let title = "Hello"\n'
        self.assertEqual(txtify.extract_title(content, Path("x.typ")), "Hello")

    def test_extract_title_raises_without_title(self) -> None:
        with self.assertRaises(ValueError):
            txtify.extract_title("= Links\n", Path("x.typ"))

    def test_extract_children_ids_empty_without_links_section(self) -> None:
        self.assertEqual(txtify.extract_links("# nothing\n"), [])

    def test_extract_children_ids_reads_only_valid_ids(self) -> None:
        content = "= Links\n- 20260101010101\n- bad\n- 20260101010102\n"
        self.assertEqual(
            txtify.extract_links(content), ["20260101010101", "20260101010102"]
        )

    def test_extract_children_ids_stops_at_next_heading(self) -> None:
        content = "= Links\n- 20260101010101\n= Next\n- 20260101010102\n"
        self.assertEqual(txtify.extract_links(content), ["20260101010101"])

    def test_populate_backlinks(self) -> None:
        nodes = {
            "20260101010101": txtify.Node(
                "20260101010101",
                "A",
                ["20260101010102"],
                [],
            ),
            "20260101010102": txtify.Node(
                "20260101010102",
                "B",
                [],
                [],
            ),
        }

        txtify.populate_backlinks(nodes)

        self.assertEqual(nodes["20260101010102"].backlinks, ["20260101010101"])

    def test_populate_backlinks_skips_unknown_links(self) -> None:
        nodes = {
            "20260101010101": txtify.Node(
                "20260101010101",
                "A",
                ["missing"],
                [],
            ),
        }

        txtify.populate_backlinks(nodes)

        self.assertEqual(nodes["20260101010101"].backlinks, [])

    def test_load_nodes_from_directory_raises_if_empty(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, self.assertRaises(ValueError):
            txtify.load_nodes_from_directory(Path(temp_dir))

    def test_load_nodes_from_directory_raises_on_invalid_filename(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "bad.typ"
            path.write_text('#let title = "Bad"\n', encoding="utf-8")
            with self.assertRaises(ValueError):
                txtify.load_nodes_from_directory(Path(temp_dir))

    def test_load_nodes_from_directory_reads_valid_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "20260101010101.typ"
            path.write_text('#let title = "Good"\n= Links\n', encoding="utf-8")
            self.assertEqual(len(txtify.load_nodes_from_directory(Path(temp_dir))), 1)

    def test_build_adjacency_text_skips_unknown_children(self) -> None:
        nodes = {
            "20260101010101": txtify.Node(
                "20260101010101",
                "A",
                ["missing"],
                [],
            ),
        }
        self.assertEqual(txtify.build_adjacency_text(nodes), "A\n")

    def test_build_adjacency_text_uses_backlinks(self) -> None:
        nodes = {
            "20260101010101": txtify.Node(
                "20260101010101",
                "A",
                [],
                ["20260101010102"],
            ),
            "20260101010102": txtify.Node(
                "20260101010102",
                "B",
                [],
                [],
            ),
        }

        result = txtify.build_adjacency_text(nodes, backlinks=True)

        self.assertEqual(
            result,
            "A\n    B\n\nB\n",
        )

    def test_run_raises_for_missing_directory(self) -> None:
        with self.assertRaises(FileNotFoundError):
            txtify.run("/definitely/missing")

    def test_run_writes_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            (temp_path / "20260101010101.typ").write_text(
                '#let title = "A"\n= Links\n',
                encoding="utf-8",
            )

            self.assertTrue(txtify.run(temp_dir).exists())

    def test_run_writes_backlinks_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            (temp_path / "20260101010101.typ").write_text(
                '#let title = "A"\n= Links\n- 20260101010102\n',
                encoding="utf-8",
            )

            (temp_path / "20260101010102.typ").write_text(
                '#let title = "B"\n= Links\n',
                encoding="utf-8",
            )

            output = txtify.run(temp_dir, backlinks=True)

            self.assertTrue(output.exists())

            content = output.read_text(encoding="utf-8")

            self.assertIn("B", content)
            self.assertIn("A", content)

    def test_add_subparser_registers_txtify(self) -> None:
        parser = argparse.ArgumentParser()
        subs = parser.add_subparsers(dest="command")

        txtify.add_subparser(subs)

        args = parser.parse_args(["txtify", "."])

        self.assertTrue(callable(args.func))

    def test_add_subparser_accepts_backlinks_flag(self) -> None:
        parser = argparse.ArgumentParser()
        subs = parser.add_subparsers(dest="command")

        txtify.add_subparser(subs)

        args = parser.parse_args(["txtify", ".", "--backlinks"])

        self.assertTrue(args.backlinks)


if __name__ == "__main__":
    unittest.main()
