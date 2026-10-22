from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from ztypy import cli, live


class LiveTests(unittest.TestCase):
    def test_subgraph_backlink_toggle(self) -> None:
        if not shutil.which("node"):
            self.skipTest("Node.js is needed to run the browser graph test")
        script = "function neighborhood(" + live.PAGE.split("function neighborhood(", 1)[1].split(
            "\nfunction fuzzyMatch(", 1
        )[0]
        script += """
const edges = [['A', 'B'], ['C', 'A'], ['B', 'D'], ['D', 'A']];
const cases = [
  [0, true, 'A'],
  [1, true, 'A,B,C,D'],
  [1, false, 'A,B'],
  [2, false, 'A,B,D'],
];
for (const [depth, backlinks, expected] of cases) {
  if ([...neighborhood('A', depth, edges, backlinks)].join(',') !== expected) {
    throw new Error(`${depth}, ${backlinks}`);
  }
}
"""
        subprocess.run(["node"], input=script, text=True, capture_output=True, check=True)

    def test_fuzzy_title_and_tag_search(self) -> None:
        if not shutil.which("node"):
            self.skipTest("Node.js is needed to run the browser search test")
        script = "function fuzzyMatch(" + live.PAGE.split("function fuzzyMatch(", 1)[1].split(
            "\nfunction filterGraph(", 1
        )[0]
        script += """
const note = {title: 'Linear Algebra Basics', tags: ['linear_algebra', 'definition']};
const cases = [
  [[], true],
  [['lnr', 'bs'], true],
  [['#lin_alg', 'bas'], true],
  [['#defn', '#lin_alg'], true],
  [['#linear_algebra'], true],
  [['linear_algebra'], false],
  [['#'], false],
  [['#other'], false],
  [['bas', '#other'], false],
];
for (const [query, expected] of cases) {
  if (matchesSearch(note, query) !== expected) throw new Error(JSON.stringify(query));
}
"""
        subprocess.run(["node"], input=script, text=True, capture_output=True, check=True)

    def test_theme_cli_options(self) -> None:
        parser = cli.build_parser()
        self.assertEqual(parser.parse_args(["live", "."]).theme, "system")
        args = parser.parse_args(["live", ".", "--theme", "dark"])
        with patch("ztypy.live.run") as run_mock:
            args.func(args)
        run_mock.assert_called_once_with(".", 8000, False, None, "dark")
        with self.assertRaises(SystemExit):
            parser.parse_args(["live", ".", "--theme", "other"])

    def test_handler_uses_selected_theme(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            with ThreadingHTTPServer(
                ("127.0.0.1", 0), live.make_handler(Path(temp_dir), None, "dark")
            ) as server:
                thread = threading.Thread(target=server.serve_forever)
                thread.start()
                try:
                    with urlopen(f"http://127.0.0.1:{server.server_port}/") as response:
                        self.assertIn('data-theme="dark"', response.read().decode())
                finally:
                    server.shutdown()
                    thread.join()
        with self.assertRaises(ValueError):
            live.make_handler(Path("."), None, "invalid")

    def test_graph_data_tracks_note_edits(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.assertEqual(live.graph_data(root), {"nodes": [], "edges": []})
            a = root / "20260101010101.typ"
            b = root / "20260101010102.typ"
            a.write_text('#let title = "A"\n:theorem:algebra:\n= Links\n', encoding="utf-8")
            b.write_text('#let title = "B"\n= Links\n', encoding="utf-8")
            self.assertEqual(live.graph_data(root)["edges"], [])
            self.assertEqual(live.graph_data(root)["nodes"][0]["tags"], ["theorem", "algebra"])
            a.write_text('#let title = "A"\n:theorem:algebra:\n= Links\n- 20260101010102\n', encoding="utf-8")
            self.assertEqual(live.graph_data(root)["edges"], [["20260101010101", "20260101010102"]])
            b.write_text('#let title = "B"\n= Links\n- 20260101010101:A\n', encoding="utf-8")
            self.assertEqual(
                live.graph_data(root)["edges"],
                [["20260101010101", "20260101010102"], ["20260101010102", "20260101010101"]],
            )

    def test_endpoints_and_safe_remote_open(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            note = root / "20260101010101.typ"
            note.write_text('#let title = "<Note>"\n= Links\n', encoding="utf-8")
            with ThreadingHTTPServer(("127.0.0.1", 0), live.make_handler(root, "/tmp/nvim.sock")) as server:
                thread = threading.Thread(target=server.serve_forever)
                thread.start()
                try:
                    url = f"http://127.0.0.1:{server.server_port}"
                    with urlopen(url + "/") as response:
                        page = response.read().decode()
                    self.assertIn("<style", page)
                    self.assertIn('@media (prefers-color-scheme: dark)', page)
                    self.assertIn(':root[data-theme="dark"]', page)
                    self.assertIn('data-theme="system"', page)
                    self.assertIn('--node-0: #a60000', page)
                    self.assertIn('--node-0: #ff5f59', page)
                    self.assertIn('--node-9: #79a8ff', page)
                    self.assertIn('return `var(--node-${hash % 12})`', page)
                    self.assertIn('#search { border-radius: 0; }', page)
                    self.assertIn('#graph-actions {\n  position: fixed;', page)
                    self.assertIn('place-items: center;', page)
                    self.assertIn('left: 1rem;\n  bottom: 1rem;', page)
                    self.assertNotIn("unpkg.com", page)
                    for interaction in (
                        "requestAnimationFrame(animate)", "pointerdown", "wheel", "highlight()",
                        "marker-end", "marker-start", "auto-start-reverse",
                        "seenPairs.has(key)", "bidirectional", "fitGraph()",
                        "'text-anchor': 'middle'", "8 + 4 * Math.sqrt(degree.get(node.id)",
                        "fill: colorForFile(node.id)", "for (const character of `${id}.typ`)",
                        "hovered && connected.has(node.id) ? 'visible' : 'hidden'",
                        "'paint-order': 'stroke'", "'font-weight': 'bold'",
                        "fill: 'var(--label)', stroke: 'var(--halo)'",
                        "stroke: 'var(--edge)'", "fill: 'var(--edge)'",
                        "showDirection && link.bidirectional", "function neighborhood(root, depth, edges, withBacklinks)",
                        "neighbors.get(from).push(to)", "if (withBacklinks) neighbors.get(to).push(from)",
                        "focusRoot = id", "if (selected) selectNode(selected)",
                        "filterGraph();\n  resizeGraph();\n  openNote(id);",
                        "if (focusRoot !== null)",
                        "node.label.setAttribute('visibility', 'visible')",
                        "node.vx *= 0.6; node.vy *= 0.6", "energy *= 0.97",
                        "(distance - 180) * 0.012", "const force = 4500 /",
                    ):
                        self.assertIn(interaction, page)
                    with urlopen(url + "/graph") as response:
                        data = json.load(response)
                    self.assertEqual(data["nodes"], [{"id": note.stem, "title": "<Note>", "tags": []}])
                    self.assertIn('id="search"', page)
                    self.assertIn('id="direction" type="button"', page)
                    self.assertIn('id="backlinks" type="button"', page)
                    self.assertIn('aria-label="Include backlinks" title="Hide backlinks" aria-pressed="true"', page)
                    self.assertIn("backlinksSlash.setAttribute('display', includeBacklinks ? 'none' : 'inline')", page)
                    self.assertIn('id="direction-slash" d="M22 2 2 22" display="none"', page)
                    self.assertIn("directionSlash.setAttribute('display', showDirection ? 'none' : 'inline')", page)
                    self.assertNotIn('<select id="theme">', page)
                    self.assertIn('id="expand" type="button"', page)
                    self.assertIn('d="m15 15 6 6"', page)
                    self.assertIn('id="generations" type="range" min="0" max="10" value="1"', page)
                    self.assertIn('generationControl.style.alignItems = \'center\'', page)
                    self.assertIn("generationControl.style.display = focusRoot === null ? 'none' : 'flex'", page)
                    self.assertIn('id="search" type="search" aria-label="Search titles and tags"', page)
                    self.assertIn('placeholder="Search titles and #tags (title_word #tag_one)"', page)
                    self.assertIn('<title>Graph</title>', page)
                    self.assertNotIn('id="settings"', page)
                    self.assertIn("search.style.flex = '1'", page)
                    self.assertIn("window.addEventListener('resize', resizeGraph)", page)
                    self.assertIn('window.innerHeight - graph.getBoundingClientRect().top', page)
                    self.assertIn("matchesSearch(node, query)", page)
                    self.assertIn('input.split(/\\s+/).filter(Boolean)', page)
                    self.assertNotIn('<h1>', page)
                    self.assertNotIn('id="status"', page)

                    def request(note_id: str, origin: str | None = None) -> Request:
                        return Request(
                            url + "/open",
                            data=json.dumps({"id": note_id}).encode(),
                            headers={"Content-Type": "application/json", "Origin": origin or url},
                        )

                    with patch("ztypy.live.subprocess.run") as remote:
                        with urlopen(request(note.stem)) as response:
                            self.assertEqual(response.status, 200)
                        remote.assert_called_once_with(
                            ["nvim", "--server", "/tmp/nvim.sock", "--remote", str(note)],
                            check=True, capture_output=True, text=True, timeout=10,
                        )
                        for bad_request in (request("../../etc/passwd"), request(note.stem, "http://evil.test")):
                            with self.assertRaises(HTTPError) as caught:
                                urlopen(bad_request)
                            caught.exception.close()
                        remote.assert_called_once()
                finally:
                    server.shutdown()
                    thread.join()

    def test_missing_directory(self) -> None:
        with self.assertRaises(FileNotFoundError):
            live.run("/definitely/missing")


if __name__ == "__main__":
    unittest.main()
