from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

FILENAME_RE = re.compile(r"^(\d{14})\.typ$")
TITLE_RE = re.compile(r'^#let\s+title\s*=\s*"(.*)"\s*$')


@dataclass
class Node:
    note_id: str
    title: str
    links: List[str]
    backlinks: List[str]


def extract_title(content: str, file_path: Path) -> str:
    for line in content.splitlines():
        match = TITLE_RE.match(line.strip())
        if match:
            return match.group(1)
    raise ValueError(f"Missing '#let title = \"...\"' in {file_path}")


def extract_links(content: str) -> List[str]:
    lines = content.splitlines()
    links_index = None

    for idx, line in enumerate(lines):
        if line.strip() == "= Links":
            links_index = idx
            break

    if links_index is None:
        return []

    links: List[str] = []
    for line in lines[links_index + 1 :]:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("=") or stripped.startswith("#bibliography"):
            break
        if stripped.startswith("- "):
            link_id = stripped[2:].strip()
            if re.fullmatch(r"\d{14}", link_id):
                links.append(link_id)

    return links


def populate_backlinks(nodes: Dict[str, Node]) -> None:
    for node in nodes.values():
        for link in node.links:
            if link in nodes:
                nodes[link].backlinks.append(node.note_id)


def load_nodes_from_directory(typ_dir: Path) -> Dict[str, Node]:
    typ_files = sorted(typ_dir.glob("*.typ"))
    if not typ_files:
        raise ValueError(f"No .typ files found in {typ_dir}")

    nodes: Dict[str, Node] = {}
    invalid_names: List[str] = []

    for path in typ_files:
        match = FILENAME_RE.fullmatch(path.name)
        if not match:
            invalid_names.append(path.name)
            continue

        note_id = match.group(1)
        content = path.read_text(encoding="utf-8")
        title = extract_title(content, path)
        links = extract_links(content)
        nodes[note_id] = Node(note_id=note_id, title=title, links=links, backlinks=[])

    if invalid_names:
        invalid_list = "\n".join(f"- {name}" for name in invalid_names)
        raise ValueError(
            "Found .typ files with invalid names. Expected YYYYMMDDHHMMSS.typ:\n"
            f"{invalid_list}"
        )

    return nodes


def build_adjacency_text(nodes: Dict[str, Node], backlinks: bool = False) -> str:
    id_to_title = {node.note_id: node.title for node in nodes.values()}
    ordered_nodes = [nodes[note_id] for note_id in sorted(nodes)]

    blocks: List[str] = []

    for node in ordered_nodes:
        block_lines = [node.title]

        edges = node.backlinks if backlinks else node.links

        for link in sorted(set(edges)):
            link_title = id_to_title.get(link)
            if link_title is not None:
                block_lines.append(f"    {link_title}")

        blocks.append("\n".join(block_lines))

    return "\n\n".join(blocks) + "\n"


def run(directory: str, backlinks: bool = False) -> Path:
    typ_dir = Path(directory).resolve()
    if not typ_dir.exists() or not typ_dir.is_dir():
        raise FileNotFoundError(f"Directory not found: {typ_dir}")

    nodes = load_nodes_from_directory(typ_dir)
    populate_backlinks(nodes)

    adjacency_text = build_adjacency_text(nodes, backlinks=backlinks)

    output_path = typ_dir / "output.txt"
    output_path.write_text(adjacency_text, encoding="utf-8")

    mode = "backlinks" if backlinks else "adjacency list"
    print(f"Wrote {mode} to {output_path}")

    return output_path


def add_subparser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    parser = subparsers.add_parser(
        "txtify", help="Generate output.txt from Typst notes"
    )
    parser.add_argument("directory", help="Directory containing .typ files")
    parser.add_argument(
        "-b",
        "--backlinks",
        action="store_true",
        help="Generate output.txt using backlinks instead of outgoing links",
    )
    parser.set_defaults(func=lambda args: run(args.directory, args.backlinks))
