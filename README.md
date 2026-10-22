# ztypy

Python CLI for my zettelkasten system using Typst.

## Project layout

- `src/ztypy/cli.py` - CLI entry point
- `src/ztypy/live.py` - live local graph and Neovim integration
- `src/ztypy/txtify.py` - Typst note parser
- `src/ztypy/slipify.py` - adjacency text to generated `.typ` notes
- `tests/` - `unittest` test suite

## Usage

Run commands from the repo root:

```bash
uv run ztypy live slipbox --port 8000
uv run ztypy generate layout.txt --output-dir output
```

`live` reads `.typ` files from the given directory and serves a graph at
`http://127.0.0.1:8000/`. The browser checks for changes every second; no
intermediate text file or external JavaScript service is needed. The graph fills
the browser window below the search bar and resizes with it. The graph uses
force-based layout: scroll to zoom, drag the background to pan, drag notes to
rearrange them, and hover to highlight a note's connections. Arrows point from
each note to the notes it links to. Nodes with more incoming or outgoing links
are larger, with titles centered beneath them. The initial view fits the graph,
and labels disappear when zoomed out. The search bar matches whole tags from
each note's colon-delimited tag line (for example, `:tag_one:tag_two:`).
The search bar's placeholder shows the space-separated format, such as
`tag_one tag_two`. All entered tags must match. Click a note
(or focus it and press Enter) to open
its file in an existing Neovim instance.

To enable note clicks, start Neovim with a local server socket, then pass the
same address to `live`:

```bash
nvim --listen /tmp/ztypy-nvim.sock
uv run ztypy live slipbox --nvim-server /tmp/ztypy-nvim.sock
```

Alternatively set `NVIM_LISTEN_ADDRESS=/tmp/ztypy-nvim.sock` when launching
`ztypy live`. Neovim must be installed, running, and accessible at that socket.
Use `--no-open` to avoid opening the browser automatically. The web server
listens only on localhost; keep the Neovim socket private to your user.

Links in a note's `= Links` section use `- YYYYMMDDHHMMSS` or
`- YYYYMMDDHHMMSS:Title`. The ID identifies the target note; the optional title
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

Add `debugpy` as a dev dependency:

```bash
uv add --dev debugpy
```

Then launch the script with debugpy listening:

```bash
uv run python -m debugpy --listen 5678 --wait-for-client -m ztypy --help
```
