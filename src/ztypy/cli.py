from __future__ import annotations

import argparse

from ztypy import slipify, txtify, view


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ztypy",
        description="CLI for slipbox tools: txtify, view, slipify",
        add_help=False,
    )
    parser.add_argument(
        "-h", "--help", action="help", help="Show this help message and exit"
    )
    subparsers = parser.add_subparsers(dest="command", metavar="<command>")

    txtify.add_subparser(subparsers)
    view.add_subparser(subparsers)
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
