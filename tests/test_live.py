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
    def test_settings_panel_and_toggles(self) -> None:
        if not shutil.which("node"):
            self.skipTest("Node.js is needed to run the browser settings test")
        handlers = "function setSettingsOpen(" + live.PAGE.split(
            "function setSettingsOpen(", 1
        )[1].split("\nexpandButton.addEventListener(", 1)[0]
        script = """
function control() {
  return {
    hidden: true, checked: false, attributes: {}, listeners: {},
    setAttribute(key, value) { this.attributes[key] = value; },
    addEventListener(key, listener) { this.listeners[key] = listener; },
    focus() { this.focused = true; },
  };
}
const settingsButton = control(), settingsPanel = control();
const directionButton = control(), backlinksButton = control(), tagsButton = control();
const document = control();
let showDirection = true, includeBacklinks = true, showTagNodes = false, focusRoot = null;
let arrowsUpdated = 0, filtered = 0, highlighted = 0, resized = 0;
function updateArrows() { arrowsUpdated++; }
function filterGraph() { filtered++; }
function highlight() { highlighted++; }
function resizeGraph() { resized++; }
""" + handlers + """
settingsButton.listeners.click();
if (settingsPanel.hidden || settingsButton.attributes['aria-expanded'] !== 'true') {
  throw new Error('settings did not open');
}
directionButton.checked = false;
directionButton.listeners.change();
backlinksButton.checked = false;
backlinksButton.listeners.change();
tagsButton.checked = true;
tagsButton.listeners.change();
if (showDirection || includeBacklinks || !showTagNodes ||
    arrowsUpdated !== 1 || highlighted !== 1 || filtered !== 1 || resized !== 1) {
  throw new Error('settings did not apply');
}
document.listeners.keydown({key: 'Escape'});
if (!settingsPanel.hidden || settingsButton.attributes['aria-expanded'] !== 'false' ||
    !settingsButton.focused) throw new Error('Escape did not close settings');
settingsButton.listeners.click();
settingsButton.listeners.click();
if (!settingsPanel.hidden) throw new Error('settings button did not toggle settings');
"""
        result = subprocess.run(["node"], input=script, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_tag_nodes_and_note_clicks(self) -> None:
        if not shutil.which("node"):
            self.skipTest("Node.js is needed to run the browser tag graph test")
        script = "function graphWithTags(" + live.PAGE.split("function graphWithTags(", 1)[1].split(
            "\nfunction filterGraph(", 1
        )[0]
        script += "\nfunction selectNode(" + live.PAGE.split("function selectNode(", 1)[1].split(
            "\nfunction updateFocusControls(", 1
        )[0]
        script += "\nfunction neighborhood(" + live.PAGE.split("function neighborhood(", 1)[1].split(
            "\nfunction fuzzyMatch(", 1
        )[0]
        script += """
const allData = {nodes: [
  {id: '12345678901234', title: 'First', tags: ['algebra']},
  {id: '12345678901235', title: 'Second', tags: ['algebra', 'geometry']},
], edges: [['12345678901234', '12345678901235']]};
let showTagNodes = true, focusRoot = null, hovered = null;
const search = {value: 'first #alg'};
const opened = [];
function updateFocusControls() {}
function filterGraph() {}
function resizeGraph() {}
function openNote(id) { opened.push(id); }
const graph = graphWithTags();
if (graph.nodes.length !== 4 || graph.edges.length !== 7 ||
    !graph.nodes.some(node => node.id === 'tag:algebra' && node.title === '#algebra')) {
  throw new Error('tag nodes missing');
}
if (!neighborhood('tag:algebra', 1, graph.edges, false).has('12345678901234') ||
    !neighborhood('12345678901234', 1, graph.edges, false).has('tag:algebra')) {
  throw new Error('tag membership not traversable');
}
selectNode('tag:algebra');
if (search.value !== '' || focusRoot !== 'tag:algebra' || opened.length) {
  throw new Error('tag click opened a file or did not focus');
}
search.value = 'second';
selectNode('12345678901235');
if (search.value !== '' || focusRoot !== '12345678901235' ||
    opened[0] !== '12345678901235') throw new Error('note click did not open file');
"""
        result = subprocess.run(["node"], input=script, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_hover_respects_backlink_toggle(self) -> None:
        if not shutil.which("node"):
            self.skipTest("Node.js is needed to run the browser hover test")
        script = "function highlight(" + live.PAGE.split("function highlight(", 1)[1].split(
            "\nfunction updateArrows(", 1
        )[0]
        script += """
let focusRoot = null, hovered = 'B', includeBacklinks = false;
const search = {value: ''};
function element() { return {attrs: {}, setAttribute(key, value) { this.attrs[key] = value; }}; }
const positions = new Map(['A', 'B', 'C', 'D'].map(id =>
  [id, {id, group: element(), label: element()}]));
const links = [
  {from: 'A', to: 'B', bidirectional: false, path: element()},
  {from: 'B', to: 'C', bidirectional: false, path: element()},
  {from: 'D', to: 'B', bidirectional: true, path: element()},
];
highlight();
if (positions.get('A').label.attrs.visibility !== 'hidden' ||
    positions.get('C').label.attrs.visibility !== 'visible' ||
    positions.get('D').label.attrs.visibility !== 'visible' ||
    links[0].path.attrs.opacity !== 0.15) throw new Error(JSON.stringify({
      a: positions.get('A').label.attrs.visibility,
      c: positions.get('C').label.attrs.visibility,
      d: positions.get('D').label.attrs.visibility,
      edge: links[0].path.attrs.opacity,
    }));
includeBacklinks = true;
highlight();
if (positions.get('A').label.attrs.visibility !== 'visible' ||
    links[0].path.attrs.opacity !== 1) throw new Error('backlink not highlighted');
"""
        result = subprocess.run(["node"], input=script, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)

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
                    self.assertIn('#left-controls {\n  position: fixed;\n  left: 1rem;\n  bottom: 1rem;', page)
                    self.assertIn('bottom: calc(100% + 0.5rem);', page)
                    self.assertNotIn("unpkg.com", page)
                    for interaction in (
                        "requestAnimationFrame(animate)", "pointerdown", "wheel", "highlight()",
                        "marker-end", "marker-start", "auto-start-reverse",
                        "seenPairs.has(key)", "bidirectional", "fitGraph()",
                        "'text-anchor': 'middle'", "8 + 4 * Math.sqrt(degree.get(node.id)",
                        "fill: colorForNode(node)", "node.kind === 'tag' ? node.title : `${node.id}.typ`",
                        "hovered && connected.has(node.id) ? 'visible' : 'hidden'",
                        "'paint-order': 'stroke'", "'font-weight': 'bold'",
                        "fill: 'var(--label)', stroke: 'var(--halo)'",
                        "stroke: 'var(--edge)'", "fill: 'var(--edge)'",
                        "showDirection && link.bidirectional && !link.tagLink", "function neighborhood(root, depth, edges, withBacklinks)",
                        "neighbors.get(from).push(to)", "if (withBacklinks) neighbors.get(to).push(from)",
                        "focusRoot = id", "if (selected) selectNode(selected)",
                        "search.value = '';", "if (!id.startsWith('tag:')) openNote(id);",
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
                    self.assertIn('id="settings" type="button" aria-label="Graph settings"', page)
                    self.assertIn('aria-controls="settings-panel" aria-expanded="false"', page)
                    self.assertIn('id="settings-panel" hidden', page)
                    self.assertIn('#settings-panel[hidden] { display: none; }', page)
                    self.assertIn('id="direction" type="checkbox" checked', page)
                    self.assertIn('id="backlinks" type="checkbox" checked', page)
                    self.assertIn('id="tags" type="checkbox"', page)
                    self.assertNotIn('id="close-settings"', page)
                    self.assertIn("showDirection = directionButton.checked", page)
                    self.assertIn("includeBacklinks = backlinksButton.checked", page)
                    self.assertIn("showTagNodes = tagsButton.checked", page)
                    self.assertIn("settingsPanel.hidden = !open", page)
                    self.assertIn("event.key === 'Escape' && !settingsPanel.hidden", page)
                    self.assertNotIn('<select id="theme">', page)
                    self.assertIn('id="expand" type="button"', page)
                    self.assertIn('d="m15 15 6 6"', page)
                    self.assertIn('id="generations" type="range" min="0" max="10" value="1"', page)
                    self.assertLess(page.index('id="settings" type="button"'), page.index('id="generation-control"'))
                    self.assertIn('generationControl.style.alignItems = \'center\'', page)
                    self.assertIn("generationControl.style.display = focusRoot === null ? 'none' : 'flex'", page)
                    self.assertIn('id="search" type="search" aria-label="Search titles and tags"', page)
                    self.assertIn('placeholder="Search titles and #tags (title_word #tag_one)"', page)
                    self.assertIn('<title>Graph</title>', page)
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
