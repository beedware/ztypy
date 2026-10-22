from __future__ import annotations

import argparse

from ztypy import live, slipify


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ztypy",
        description="Tools for viewing and generating Typst slipbox notes",
        add_help=False,
    )
    parser.add_argument(
        "-h", "--help", action="help", help="Show this help message and exit"
    )
    subparsers = parser.add_subparsers(dest="command", metavar="<command>")

    live.add_subparser(subparsers)
    slipify.add_subparser(subparsers)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    command_fn = getattr(args, "func", None)
    if command_fn is None:
        parser.print_help()
        return

    command_fn(args)


if __name__ == "__main__":
    main()
