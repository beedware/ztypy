from __future__ import annotations

import argparse
import html
import json
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory


def parse_adjacency_layout(
    layout_path: Path,
) -> tuple[list[str], list[tuple[str, str]]]:
    nodes: set[str] = set()
    edges: set[tuple[str, str]] = set()
    current_parent: str | None = None

    for raw in layout_path.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue

        if raw[:1].isspace():
            child = raw.strip()
            if current_parent is None:
                raise ValueError(f"Found child without parent: {raw!r}")
            nodes.add(child)
            edges.add((current_parent, child))
        else:
            current_parent = raw.strip()
            nodes.add(current_parent)

    return sorted(nodes), sorted(edges)


def populate_edge_payload(edges: list[tuple[str, str]]) -> list[dict[str, str]]:
    payload = {}
    for src, dst in edges:
        if (dst, src) in payload:
            payload[(dst, src)]["arrows"] = "to, from"
        else:
            payload[(src, dst)] = {
                "from": src,
                "to": dst,
                "arrows": "to",
            }
    return list(payload.values())


def build_html(
    graph_title: str, node_titles: list[str], edges: list[tuple[str, str]]
) -> str:
    node_payload = [{"id": title, "label": title} for title in node_titles]
    edge_payload = populate_edge_payload(edges)

    return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>{html.escape(graph_title)}</title>
  <script src=\"https://unpkg.com/vis-network@9.1.9/dist/vis-network.min.js\"></script>
  <style>
    :root {{
      --bg: #f4f7fb;
      --panel: #ffffff;
      --text: #12202f;
      --muted: #4a5d75;
      --node: #e6f0ff;
      --node-border: #7aa2d8;
      --edge: #6b7f99;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100vh;
      background: radial-gradient(circle at 10% 10%, #e8f2ff 0%, var(--bg) 45%, #edf3f9 100%);
      color: var(--text);
      font-family: Georgia, \"Times New Roman\", serif;
      display: grid;
      grid-template-rows: auto 1fr;
    }}
    header {{
      padding: 16px 20px;
      border-bottom: 1px solid #d4e0ee;
      background: color-mix(in srgb, var(--panel) 85%, #dce9f8 15%);
    }}
    h1 {{ margin: 0; font-size: 1.2rem; }}
    p {{ margin: 6px 0 0; color: var(--muted); font-size: 0.95rem; }}
    #network {{ width: 100%; height: calc(100vh - 84px); }}
  </style>
</head>
<body>
  <header>
    <h1>{html.escape(graph_title)}</h1>
    <p>{len(node_titles)} nodes, {len(edges)} directed links</p>
  </header>
  <div id=\"network\"></div>

  <script>
    const nodes = new vis.DataSet({json.dumps(node_payload)});
    const edges = new vis.DataSet({json.dumps(edge_payload)});
    const container = document.getElementById('network');

    const data = {{ nodes, edges }};
    const options = {{
      nodes: {{
        shape: 'box',
        margin: 10,
        color: {{
          background: getComputedStyle(document.documentElement).getPropertyValue('--node').trim(),
          border: getComputedStyle(document.documentElement).getPropertyValue('--node-border').trim(),
        }},
        font: {{
          color: getComputedStyle(document.documentElement).getPropertyValue('--text').trim(),
          size: 18,
          face: 'Georgia',
        }},
      }},
      edges: {{
        color: getComputedStyle(document.documentElement).getPropertyValue('--edge').trim(),
        arrows: {{ to: {{ enabled: true, scaleFactor: 0.8 }} }},
        smooth: {{ type: 'dynamic' }},
      }},
      physics: {{
        stabilization: true,
        barnesHut: {{ springLength: 150, springConstant: 0.04 }},
      }},
      interaction: {{
        hover: true,
        tooltipDelay: 120,
      }},
    }};

    new vis.Network(container, data, options);
  </script>
</body>
</html>
"""


def serve_html(html_content: str, port: int, open_browser: bool) -> None:
    with TemporaryDirectory(prefix="slipbox-graph-") as temp_dir:
        index_path = Path(temp_dir) / "index.html"
        index_path.write_text(html_content, encoding="utf-8")

        class Handler(SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=temp_dir, **kwargs)

        server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
        url = f"http://127.0.0.1:{server.server_port}/index.html"
        print(f"Serving graph at {url}")
        print("Press Ctrl+C to stop.")

        if open_browser:
            webbrowser.open(url)

        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            server.server_close()


def run(txt_file: str, port: int = 8000, no_open: bool = False) -> None:
    txt_path = Path(txt_file).resolve()
    if not txt_path.exists() or not txt_path.is_file():
        raise FileNotFoundError(f"Text file not found: {txt_path}")

    node_titles, edges = parse_adjacency_layout(txt_path)
    page_title = f"Graph View: {txt_path.name}"
    html_content = build_html(page_title, node_titles, edges)
    serve_html(html_content, port=port, open_browser=not no_open)


def add_subparser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    parser = subparsers.add_parser(
        "view",
        help="Visualize an adjacency text file as an interactive graph",
        description=(
            "Parse an adjacency-list text file and serve an interactive graph "
            "visualization in the browser."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False,
    )
    parser.add_argument(
        "-h", "--help", action="help", help="Show this help message and exit"
    )
    parser.add_argument(
        "txt_file",
        metavar="FILE",
        help="Path to adjacency-list text file",
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=8000,
        metavar="PORT",
        help="Port for local server (default: %(default)s)",
    )
    parser.add_argument(
        "-n",
        "--no-open",
        action="store_true",
        help="Do not auto-open browser",
    )
    parser.set_defaults(func=lambda args: run(args.txt_file, args.port, args.no_open))
