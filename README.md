# ztypy

Python CLI for my zettelkasten system using Typst.

## Project layout

- `src/ztypy/cli.py` - CLI entry point
- `src/ztypy/txtify.py` - `.typ` files to adjacency text
- `src/ztypy/view.py` - adjacency text to interactive graph view
- `src/ztypy/slipify.py` - adjacency text to generated `.typ` notes
- `tests/` - `unittest` test suite

## Usage

Run commands from the repo root:

```bash
uv run ztypy txtify slipbox
uv run ztypy view slipbox/output.txt --port 8000
uv run ztypy slipify layout.txt --output-dir output
```

Links in a note's `= Links` section use `- YYYYMMDDHHMMSS:Title`, for example
`- 20261022140066:Group action`. The ID identifies the target note; the title
labels it for readers.

## Run tests

```bash
uv run python -m unittest discover -s tests -v
```

## Install

```bash
uv tool install .
```

## Debugging

### VS Code (attach)

Add `debugpy` as a dev dependency:

```bash
uv add --dev debugpy
```

Then launch the script with debugpy listening:

```bash
uv run python -m debugpy --listen 5678 --wait-for-client -m ztypy --help
```
