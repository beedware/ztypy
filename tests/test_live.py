from __future__ import annotations

import json
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from ztypy import live


class LiveTests(unittest.TestCase):
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
                    self.assertNotIn("<style", page)
                    self.assertNotIn("unpkg.com", page)
                    for interaction in (
                        "requestAnimationFrame(animate)", "pointerdown", "wheel", "highlight()",
                        "marker-end", "reciprocal", "fitGraph()", "scale < 0.7",
                        "'text-anchor': 'middle'", "Math.sqrt(degree.get(node.id)",
                    ):
                        self.assertIn(interaction, page)
                    with urlopen(url + "/graph") as response:
                        data = json.load(response)
                    self.assertEqual(data["nodes"], [{"id": note.stem, "title": "<Note>", "tags": []}])
                    self.assertIn('id="search"', page)
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
