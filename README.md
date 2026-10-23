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
the browser window below search and resizes with it. The graph uses
force-based layout with room between nodes that settles quickly: scroll to zoom,
drag the background to pan, drag notes to rearrange them, and hover to reveal
a note's title and its connected notes'
titles at any zoom level. Titles are otherwise hidden. Arrows point from
each note to the notes it links to; reciprocal links share one line with arrows
at both ends. Nodes have stable colors based on their
filenames; nodes with more incoming or outgoing links are larger, with
high-contrast titles centered beneath them when hovered. The initial view fits
the graph. Search title words directly and prefix tag searches with `#`. For
example, `title_word #tag_one #tag_two` matches a title and both tags from a
note's colon-delimited tag line (for example, `:tag_one:tag_two:`). Matching is
case-insensitive and fuzzy (letters in order); all terms must match. Matching
nodes show their titles while searching. Clicking a node clears the search,
focuses its subgraph, and opens it in Neovim if it has a file. The settings
button at the bottom left opens a panel for showing tag nodes, arrowheads, and
backlinks. Tag nodes connect to the notes carrying those tags by undirected
lines and can be focused, but do not open a file. Close the panel with the
settings button or Escape.
`live` defaults to the system color scheme; use `--theme light` or
`--theme dark` to override it:

```bash
uv run ztypy live slipbox --theme dark
```

The light and dark graph palettes use the Modus colors from the Alacritty theme
files; in system mode they follow your browser's color scheme. Clicking a note
(or focusing it and pressing Enter) shows its linked children and backlinks.
The generation slider to the right of the settings button
controls how many steps to follow in either direction (0–10). Click a visible
node to focus on it instead. Focused subgraphs show all their titles without
hover highlighting. Backlinks are included by default for both hover highlights
and subgraphs; turn them off in settings to see only outgoing links. Use the
expand icon at the bottom right to restore the full graph
and normal hover behavior. The icons are bundled Lucide SVGs; see
`src/ztypy/LUCIDE-LICENSE.txt`.

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
