from __future__ import annotations

import argparse
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ztypy import view


class _FakeServer:
    def __init__(self, *_args, **_kwargs):
        self.server_port = 8123
        self.closed = False

    def serve_forever(self) -> None:
        raise KeyboardInterrupt

    def server_close(self) -> None:
        self.closed = True


class ViewTests(unittest.TestCase):
    def test_parse_adjacency_layout_parses_nodes_and_edges(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "x.txt"
            path.write_text("Root\n  Child\n", encoding="utf-8")
            self.assertEqual(view.parse_adjacency_layout(path)[1], [("Root", "Child")])

    def test_parse_adjacency_layout_raises_for_child_without_parent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "x.txt"
            path.write_text("  Child\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                view.parse_adjacency_layout(path)

    def test_build_html_escapes_title(self) -> None:
        html = view.build_html("<unsafe>", ["A"], [])
        self.assertIn("&lt;unsafe&gt;", html)

    def test_serve_html_calls_browser_open_when_enabled(self) -> None:
        with (
            patch("ztypy.view.ThreadingHTTPServer", _FakeServer),
            patch("ztypy.view.webbrowser.open") as open_mock,
        ):
            view.serve_html("<html></html>", 8000, True)
            self.assertTrue(open_mock.called)

    def test_serve_html_does_not_call_browser_open_when_disabled(self) -> None:
        with (
            patch("ztypy.view.ThreadingHTTPServer", _FakeServer),
            patch("ztypy.view.webbrowser.open") as open_mock,
        ):
            view.serve_html("<html></html>", 8000, False)
            self.assertFalse(open_mock.called)

    def test_run_raises_for_missing_file(self) -> None:
        with self.assertRaises(FileNotFoundError):
            view.run("/definitely/missing.txt")

    def test_run_calls_serve_html(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "layout.txt"
            path.write_text("A\n  B\n", encoding="utf-8")
            with patch("ztypy.view.serve_html") as serve_mock:
                view.run(str(path), 9000, True)
                self.assertTrue(serve_mock.called)

    def test_add_subparser_registers_view(self) -> None:
        parser = argparse.ArgumentParser()
        subs = parser.add_subparsers(dest="command")
        view.add_subparser(subs)
        args = parser.parse_args(["view", "file.txt"])
        self.assertTrue(callable(args.func))


if __name__ == "__main__":
    unittest.main()
