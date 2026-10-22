from __future__ import annotations

import unittest
from unittest.mock import patch

from ztypy import cli


class MainCliTests(unittest.TestCase):
    def test_build_parser_has_live_and_generate_commands(self) -> None:
        parser = cli.build_parser()
        self.assertEqual(parser.parse_args(["live", "."]).command, "live")
        self.assertEqual(parser.parse_args(["generate", "layout.txt"]).command, "generate")
        for old_name in ("txtify", "view", "slipify"):
            with self.subTest(old_name=old_name), self.assertRaises(SystemExit):
                parser.parse_args([old_name])

    def test_main_prints_help_without_command(self) -> None:
        with (
            patch("argparse.ArgumentParser.print_help") as help_mock,
            patch("sys.argv", ["ztypy"]),
        ):
            cli.main()
            self.assertTrue(help_mock.called)

    def test_main_executes_selected_command(self) -> None:
        with (
            patch("ztypy.live.run") as run_mock,
            patch("sys.argv", ["ztypy", "live", "."]),
        ):
            cli.main()
            self.assertTrue(run_mock.called)


if __name__ == "__main__":
    unittest.main()
