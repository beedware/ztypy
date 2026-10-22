from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path


@dataclass(frozen=True)
class Note:
    title: str
    note_id: str


def parse_adjacency_layout(layout_path: Path) -> tuple[dict[str, list[str]], set[str]]:
    adjacency: dict[str, list[str]] = {}
    all_nodes: set[str] = set()
    current_parent: str | None = None

    for raw in layout_path.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue

        if raw[:1].isspace():
            child = raw.strip()
            if current_parent is None:
                raise ValueError(f"Found child without parent: {raw!r}")
            adjacency.setdefault(current_parent, []).append(child)
            all_nodes.add(child)
        else:
            current_parent = raw.strip()
            adjacency.setdefault(current_parent, [])
            all_nodes.add(current_parent)

    return adjacency, all_nodes


def generate_note_ids(nodes: list[str]) -> dict[str, Note]:
    base = datetime.now(timezone.utc).replace(microsecond=0)
    notes: dict[str, Note] = {}

    for index, title in enumerate(nodes):
        note_time = base + timedelta(seconds=index)
        note_id = note_time.strftime("%Y%m%d%H%M%S")
        notes[title] = Note(title=title, note_id=note_id)

    return notes


def phase_1_create_files(output_dir: Path, notes: dict[str, Note]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    base_content = (
        '#import ".utility/style.typ": style\n'
        "#show: style\n\n"
        '#let title = ""\n'
        "#let id = 0\n\n"
        "#id:ghost:\n\n"
        "= #title\n\n"
        "= Links\n\n"
        '#bibliography(".utility/sources.yaml")\n'
    )

    for note in notes.values():
        file_path = output_dir / f"{note.note_id}.typ"
        file_path.write_text(base_content, encoding="utf-8")


def phase_2_add_titles(output_dir: Path, notes: dict[str, Note]) -> None:
    for note in notes.values():
        file_path = output_dir / f"{note.note_id}.typ"
        content = file_path.read_text(encoding="utf-8")
        content = content.replace('#let title = ""', f'#let title = "{note.title}"', 1)
        content = content.replace("#let id = 0", f"#let id = {note.note_id}", 1)
        file_path.write_text(content, encoding="utf-8")


def phase_3_add_links(
    output_dir: Path, notes: dict[str, Note], adjacency: dict[str, list[str]]
) -> None:
    for title, note in notes.items():
        child_links: set[tuple[str, str]] = set()
        for child in adjacency.get(title, []):
            child_note = notes[child]
            child_links.add((child_note.note_id, child_note.title))

        file_path = output_dir / f"{note.note_id}.typ"
        content = file_path.read_text(encoding="utf-8")

        if child_links:
            links_block = "\n".join(
                f"- {link_id}:{link_title}"
                for link_id, link_title in sorted(child_links)
            )
        else:
            links_block = ""

        content = content.replace("= Links", f"= Links\n\n{links_block}", 1)
        file_path.write_text(content, encoding="utf-8")


def build_slip_layout_text(
    adjacency: dict[str, list[str]], notes: dict[str, Note]
) -> str:
    lines: list[str] = []

    for parent_title in sorted(adjacency):
        parent_name = f"{notes[parent_title].note_id}.typ"
        lines.append(parent_name)

        child_names = sorted(
            {f"{notes[child].note_id}.typ" for child in adjacency[parent_title]}
        )
        for child_name in child_names:
            lines.append(f"    {child_name}")

        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def run(layout_file: str, output_dir: str = "output") -> Path:
    layout_path = Path(layout_file).resolve()
    if not layout_path.exists() or not layout_path.is_file():
        raise FileNotFoundError(f"Layout file not found: {layout_path}")

    target_dir = Path(output_dir).resolve()
    adjacency, all_nodes = parse_adjacency_layout(layout_path)
    ordered_nodes = sorted(all_nodes)
    notes = generate_note_ids(ordered_nodes)

    phase_1_create_files(target_dir, notes)
    phase_2_add_titles(target_dir, notes)
    phase_3_add_links(target_dir, notes, adjacency)

    slip_layout_path = layout_path.with_name(f"{layout_path.stem}.slip.txt")
    slip_layout_text = build_slip_layout_text(adjacency, notes)
    slip_layout_path.write_text(slip_layout_text, encoding="utf-8")

    print(f"Generated {len(notes)} files in {target_dir}")
    print(f"Wrote slip layout to {slip_layout_path}")
    return target_dir


def add_subparser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    parser = subparsers.add_parser(
        "generate",
        help="Generate Typst slipbox files from an adjacency layout",
        description=(
            "Convert an adjacency-list text file into a collection of "
            "Typst Zettelkasten notes."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False,
    )
    parser.add_argument(
        "-h", "--help", action="help", help="Show this help message and exit"
    )

    parser.add_argument(
        "layout_file",
        metavar="LAYOUT",
        help="Adjacency-list text file",
    )

    parser.add_argument(
        "-o",
        "--output-dir",
        metavar="DIR",
        default="output",
        help="Output directory for generated .typ files (default: %(default)s)",
    )

    parser.set_defaults(func=lambda args: run(args.layout_file, args.output_dir))
