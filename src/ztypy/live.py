from __future__ import annotations

import argparse
import json
import os
import subprocess
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from ztypy import txtify


PAGE = r"""<!doctype html>
<html lang="en" data-theme="system">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Graph</title>
<style>
:root {
  color-scheme: light;
  --background: #ffffff;
  --text: #000000;
  --edge: #595959;
  --label: #000000;
  --halo: #ffffff;
  --node-0: #a60000;
  --node-1: #006800;
  --node-2: #6f5500;
  --node-3: #0031a9;
  --node-4: #721045;
  --node-5: #005e8b;
  --node-6: #972500;
  --node-7: #00663f;
  --node-8: #884900;
  --node-9: #3548cf;
  --node-10: #8f0075;
  --node-11: #005f5f;
}
:root[data-theme="dark"] {
  color-scheme: dark;
  --background: #000000;
  --text: #ffffff;
  --edge: #a6a6a6;
  --label: #ffffff;
  --halo: #000000;
  --node-0: #ff5f59;
  --node-1: #44bc44;
  --node-2: #d0bc00;
  --node-3: #2fafff;
  --node-4: #feacd0;
  --node-5: #00d3d0;
  --node-6: #ff6b55;
  --node-7: #00c06f;
  --node-8: #fec43f;
  --node-9: #79a8ff;
  --node-10: #f78fe7;
  --node-11: #6ae4b9;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    color-scheme: dark;
    --background: #000000;
    --text: #ffffff;
    --edge: #a6a6a6;
    --label: #ffffff;
    --halo: #000000;
    --node-0: #ff5f59;
    --node-1: #44bc44;
    --node-2: #d0bc00;
    --node-3: #2fafff;
    --node-4: #feacd0;
    --node-5: #00d3d0;
    --node-6: #ff6b55;
    --node-7: #00c06f;
    --node-8: #fec43f;
    --node-9: #79a8ff;
    --node-10: #f78fe7;
    --node-11: #6ae4b9;
  }
}
body { background: var(--background); color: var(--text); }
#search { border-radius: 0; }
#graph-actions {
  position: fixed;
  right: 1rem;
  bottom: 1rem;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
#graph-actions button {
  display: grid;
  place-items: center;
  width: 2.5rem;
  height: 2.5rem;
  padding: 0;
}
#left-controls {
  position: fixed;
  left: 1rem;
  bottom: 1rem;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
#settings {
  display: grid;
  place-items: center;
  width: 2.5rem;
  height: 2.5rem;
  padding: 0;
}
#settings-panel {
  position: absolute;
  left: 0;
  bottom: calc(100% + 0.5rem);
  border: 1px solid var(--edge);
  border-radius: 0.25rem;
  padding: 0.75rem;
  background: var(--background);
  color: var(--text);
}
#settings-panel[hidden] { display: none; }
#settings-panel label { display: block; margin: 0.5rem 0; }
#settings-panel label input { margin-right: 0.5rem; }
#generation-control {
  padding: 0.5rem;
  background: var(--background);
}
</style></head>
<body>
<div id="toolbar">
  <input id="search" type="search" aria-label="Search titles and tags" placeholder="Search titles and #tags (title_word #tag_one)">
</div>
<div id="graph-actions">
  <button id="expand" type="button" aria-label="Show full graph" title="Show full graph" disabled><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m15 15 6 6"/><path d="m15 9 6-6"/><path d="M21 16v5h-5"/><path d="M21 8V3h-5"/><path d="M3 16v5h5"/><path d="m3 21 6-6"/><path d="M3 8V3h5"/><path d="M9 9 3 3"/></svg></button>
</div>
<div id="left-controls">
  <div id="settings-panel" hidden aria-label="Graph settings">
    <strong>Graph settings</strong>
    <label><input id="direction" type="checkbox" checked> Show arrowheads</label>
    <label><input id="backlinks" type="checkbox" checked> Include backlinks</label>
    <label><input id="tags" type="checkbox"> Show tags as nodes</label>
  </div>
  <button id="settings" type="button" aria-label="Graph settings" aria-controls="settings-panel" aria-expanded="false" title="Graph settings"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 21v-7M4 10V3M12 21v-9M12 8V3M20 21v-5M20 12V3M2 14h4M10 8h4M18 16h4"/></svg></button>
  <span id="generation-control" hidden><label for="generations">Generations:</label><input id="generations" type="range" min="0" max="10" value="1"><output id="generation-count">1</output></span>
</div>
<svg id="graph" role="img" aria-label="Graph"></svg>
<script>
const graph = document.getElementById('graph');
const search = document.getElementById('search');
const settingsButton = document.getElementById('settings');
const settingsPanel = document.getElementById('settings-panel');
const directionButton = document.getElementById('direction');
const backlinksButton = document.getElementById('backlinks');
const tagsButton = document.getElementById('tags');
const expandButton = document.getElementById('expand');
const generationControl = document.getElementById('generation-control');
const generations = document.getElementById('generations');
const generationCount = document.getElementById('generation-count');
const svgNS = 'http://www.w3.org/2000/svg';
const defs = element('defs', {});
const arrow = element('marker', {
  id: 'link-arrow', viewBox: '0 0 10 10', refX: 9, refY: 5,
  markerWidth: 10, markerHeight: 10, markerUnits: 'userSpaceOnUse', orient: 'auto-start-reverse',
});
arrow.append(element('path', {d: 'M 0 0 L 10 5 L 0 10 Z', fill: 'var(--edge)'}));
defs.append(arrow);
graph.append(defs);
const viewport = element('g', {});
const linksLayer = element('g', {});
const nodesLayer = element('g', {});
viewport.append(linksLayer, nodesLayer);
graph.append(viewport);
const positions = new Map();
let links = [];
let hovered = null;
let drag = null;
let scale = 1, panX = 0, panY = 0;
let energy = 0;
let previous = '';
let allData = {nodes: [], edges: []};
let initialFit = false;
let refitFrames = 0;
let focusRoot = null;
let showDirection = true;
let includeBacklinks = true;
let showTagNodes = false;

// Keep the graph sized to the space below search.
document.body.style.margin = '0';
graph.style.display = 'block';
document.getElementById('toolbar').style.display = 'flex';
search.style.flex = '1';
search.style.minWidth = '0';
search.style.boxSizing = 'border-box';
generationControl.style.alignItems = 'center';
generationControl.style.gap = '0.5em';

function resizeGraph() {
  const width = window.innerWidth;
  const height = Math.max(1, window.innerHeight - graph.getBoundingClientRect().top);
  graph.setAttribute('width', width);
  graph.setAttribute('height', height);
  graph.setAttribute('viewBox', `0 0 ${width} ${height}`);
  if (positions.size) fitGraph();
}

window.addEventListener('resize', resizeGraph);
resizeGraph();

function element(tag, attributes) {
  const node = document.createElementNS(svgNS, tag);
  for (const [name, value] of Object.entries(attributes)) node.setAttribute(name, value);
  return node;
}

function colorForNode(node) {
  let hash = 2166136261;
  const name = node.kind === 'tag' ? node.title : `${node.id}.typ`;
  for (const character of name) {
    hash = Math.imul(hash ^ character.charCodeAt(0), 16777619) >>> 0;
  }
  return `var(--node-${hash % 12})`;
}

async function openNote(id) {
  try {
    const response = await fetch('/open', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({id}),
    });
    if (!response.ok) throw new Error(await response.text());
  } catch (error) {
    console.error('Could not open note:', error);
  }
}

function selectNode(id) {
  search.value = '';
  focusRoot = id;
  hovered = null;
  updateFocusControls();
  filterGraph();
  resizeGraph();
  if (!id.startsWith('tag:')) openNote(id);
}

function updateFocusControls() {
  expandButton.disabled = focusRoot === null;
  generationControl.hidden = focusRoot === null;
  generationControl.style.display = focusRoot === null ? 'none' : 'flex';
}

function setSettingsOpen(open) {
  settingsPanel.hidden = !open;
  settingsButton.setAttribute('aria-expanded', String(open));
}

settingsButton.addEventListener('click', () => setSettingsOpen(settingsPanel.hidden));
document.addEventListener('keydown', event => {
  if (event.key === 'Escape' && !settingsPanel.hidden) {
    setSettingsOpen(false);
    settingsButton.focus();
  }
});

directionButton.addEventListener('change', () => {
  showDirection = directionButton.checked;
  updateArrows();
});

backlinksButton.addEventListener('change', () => {
  includeBacklinks = backlinksButton.checked;
  if (focusRoot !== null) filterGraph();
  else highlight();
});

tagsButton.addEventListener('change', () => {
  showTagNodes = tagsButton.checked;
  filterGraph();
  resizeGraph();
});

expandButton.addEventListener('click', () => {
  focusRoot = null;
  hovered = null;
  updateFocusControls();
  filterGraph();
  resizeGraph();
});

generations.addEventListener('input', () => {
  generationCount.value = generations.value;
  if (focusRoot !== null) filterGraph();
});

function svgPoint(event) {
  const point = graph.createSVGPoint();
  point.x = event.clientX;
  point.y = event.clientY;
  return point.matrixTransform(graph.getScreenCTM().inverse());
}

function transform() {
  viewport.setAttribute('transform', `translate(${panX} ${panY}) scale(${scale})`);
  highlight();
}

function fitGraph() {
  if (!positions.size) return;
  const box = [...positions.values()].reduce((box, node) => {
    box.left = Math.min(box.left, node.x - node.radius);
    box.top = Math.min(box.top, node.y - node.radius);
    box.right = Math.max(box.right, node.x + node.radius);
    box.bottom = Math.max(box.bottom, node.y + node.radius);
    return box;
  }, {left: Infinity, top: Infinity, right: -Infinity, bottom: -Infinity});
  const width = graph.viewBox.baseVal.width;
  const height = graph.viewBox.baseVal.height;
  scale = Math.min(
    2, (width - 100) / Math.max(box.right - box.left, 160),
    (height - 100) / Math.max(box.bottom - box.top, 120),
  );
  panX = width / 2 - scale * (box.left + box.right) / 2;
  panY = height / 2 - scale * (box.top + box.bottom) / 2;
  transform();
}

graph.addEventListener('wheel', event => {
  event.preventDefault();
  refitFrames = 0;
  const point = svgPoint(event);
  const next = Math.max(0.2, Math.min(5, scale * Math.exp(-event.deltaY * 0.001)));
  panX = point.x - (point.x - panX) * next / scale;
  panY = point.y - (point.y - panY) * next / scale;
  scale = next;
  transform();
}, {passive: false});

graph.addEventListener('pointerdown', event => {
  if (event.button !== 0 || event.target.closest('[data-id]')) return;
  refitFrames = 0;
  drag = {kind: 'pan', point: svgPoint(event), x: panX, y: panY};
  graph.setPointerCapture(event.pointerId);
});

graph.addEventListener('pointermove', event => {
  if (!drag) return;
  const point = svgPoint(event);
  if (drag.kind === 'pan') {
    panX = drag.x + point.x - drag.point.x;
    panY = drag.y + point.y - drag.point.y;
    transform();
  } else {
    const node = positions.get(drag.id);
    if (!node) return;
    if (Math.hypot(event.clientX - drag.clientX, event.clientY - drag.clientY) > 4) {
      drag.moved = true;
    }
    if (drag.moved) {
      node.x = (point.x - panX) / scale;
      node.y = (point.y - panY) / scale;
      node.vx = node.vy = 0;
      energy = 1;
      render();
    }
  }
});

graph.addEventListener('pointerup', event => {
  if (!drag) return;
  const selected = drag.kind === 'node' && !drag.moved ? drag.id : null;
  drag = null;
  if (graph.hasPointerCapture(event.pointerId)) graph.releasePointerCapture(event.pointerId);
  if (selected) selectNode(selected);
});
graph.addEventListener('pointercancel', () => { drag = null; });

function highlight() {
  if (focusRoot !== null || search.value.trim()) {
    for (const link of links) link.path.setAttribute('opacity', 1);
    for (const node of positions.values()) {
      node.group.setAttribute('opacity', 1);
      node.label.setAttribute('visibility', 'visible');
    }
    return;
  }
  const connected = new Set([hovered]);
  for (const link of links) {
    if (link.from === hovered) connected.add(link.to);
    if ((includeBacklinks || link.bidirectional) && link.to === hovered) connected.add(link.from);
    const visible = link.from === hovered ||
      ((includeBacklinks || link.bidirectional) && link.to === hovered);
    link.path.setAttribute('opacity', !hovered || visible ? 1 : 0.15);
  }
  for (const node of positions.values()) {
    node.group.setAttribute('opacity', !hovered || connected.has(node.id) ? 1 : 0.3);
    node.label.setAttribute('visibility',
      hovered && connected.has(node.id) ? 'visible' : 'hidden');
  }
}

function updateArrows() {
  for (const link of links) {
    link.path.setAttribute('marker-end', showDirection && !link.tagLink ? 'url(#link-arrow)' : 'none');
    link.path.setAttribute('marker-start',
      showDirection && link.bidirectional && !link.tagLink ? 'url(#link-arrow)' : 'none');
  }
}

function draw(nodes, edges, allEdges) {
  const degree = new Map();
  const seenTagLinks = new Set();
  for (const [from, to] of allEdges) {
    if (from.startsWith('tag:') || to.startsWith('tag:')) {
      const key = [from, to].sort().join('|');
      if (seenTagLinks.has(key)) continue;
      seenTagLinks.add(key);
    }
    degree.set(from, (degree.get(from) ?? 0) + 1);
    if (to !== from) degree.set(to, (degree.get(to) ?? 0) + 1);
  }
  const ids = new Set(nodes.map(node => node.id));
  for (const id of positions.keys()) if (!ids.has(id)) positions.delete(id);
  for (const [index, node] of nodes.entries()) {
    if (!positions.has(node.id)) {
      const neighbor = edges.find(([a, b]) => (a === node.id && positions.has(b)) || (b === node.id && positions.has(a)));
      const anchor = neighbor && positions.get(neighbor[0] === node.id ? neighbor[1] : neighbor[0]);
      const angle = index * 2.4;
      positions.set(node.id, {
        id: node.id, x: (anchor?.x ?? graph.viewBox.baseVal.width / 2) + 110 * Math.cos(angle),
        y: (anchor?.y ?? graph.viewBox.baseVal.height / 2) + 110 * Math.sin(angle), vx: 0, vy: 0,
      });
    }
  }
  if (drag?.kind === 'node' && !positions.has(drag.id)) drag = null;
  linksLayer.replaceChildren();
  nodesLayer.replaceChildren();
  const pairs = new Set(edges.map(([from, to]) => `${from}:${to}`));
  const seenPairs = new Set();
  links = [];
  for (const [from, to] of edges) {
    if (!positions.has(from) || !positions.has(to)) continue;
    const key = [from, to].sort().join(':');
    if (seenPairs.has(key)) continue;
    seenPairs.add(key);
    const bidirectional = from !== to && pairs.has(`${to}:${from}`);
    const path = element('path', {fill: 'none', stroke: 'var(--edge)'});
    linksLayer.append(path);
    links.push({
      from, to, path, bidirectional,
      tagLink: from.startsWith('tag:') || to.startsWith('tag:'),
    });
  }
  updateArrows();
  for (const node of nodes) {
    const position = positions.get(node.id);
    position.radius = Math.min(36, 8 + 4 * Math.sqrt(degree.get(node.id) ?? 0));
    const group = element('g', {
      'data-id': node.id, tabindex: '0', role: 'button',
      'aria-label': `${node.kind === 'tag' ? 'Focus on' : 'Open and focus on'} ${node.title}`,
    });
    group.append(element('circle', {r: position.radius, fill: colorForNode(node)}));
    const label = element('text', {
      x: 0, y: position.radius + 18, 'text-anchor': 'middle',
      fill: 'var(--label)', stroke: 'var(--halo)', 'stroke-width': 4,
      'paint-order': 'stroke', 'font-weight': 'bold',
    });
    label.textContent = node.title;
    group.append(label);
    position.label = label;
    group.addEventListener('pointerdown', event => {
      if (event.button !== 0) return;
      event.stopPropagation();
      refitFrames = 0;
      drag = {kind: 'node', id: node.id, clientX: event.clientX, clientY: event.clientY, moved: false};
      graph.setPointerCapture(event.pointerId);
    });
    group.addEventListener('pointerenter', () => { hovered = node.id; highlight(); });
    group.addEventListener('pointerleave', () => { hovered = null; highlight(); });
    group.addEventListener('keydown', event => {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        selectNode(node.id);
      }
    });
    position.group = group;
    nodesLayer.append(group);
  }
  if (!positions.has(hovered)) hovered = null;
  highlight();
  energy = 1;
  render();
  if (!initialFit && nodes.length) {
    initialFit = true;
    fitGraph();
    refitFrames = 75;
  } else {
    transform();
  }
}

function neighborhood(root, depth, edges, withBacklinks) {
  const neighbors = new Map();
  for (const [from, to] of edges) {
    if (!neighbors.has(from)) neighbors.set(from, []);
    if (!neighbors.has(to)) neighbors.set(to, []);
    neighbors.get(from).push(to);
    if (withBacklinks) neighbors.get(to).push(from);
  }
  const visible = new Set([root]);
  let frontier = [root];
  for (let generation = 0; generation < depth && frontier.length; generation++) {
    const next = [];
    for (const parent of frontier) {
      for (const neighbor of neighbors.get(parent) ?? []) {
        if (visible.has(neighbor)) continue;
        visible.add(neighbor);
        next.push(neighbor);
      }
    }
    frontier = next;
  }
  return visible;
}

function fuzzyMatch(value, term) {
  const text = value.toLowerCase();
  let position = 0;
  for (const character of term.toLowerCase()) {
    position = text.indexOf(character, position);
    if (position === -1) return false;
    position++;
  }
  return true;
}

function matchesSearch(node, query) {
  return query.every(term => {
    if (term.startsWith('#')) {
      const tag = term.slice(1);
      return tag.length > 0 && node.tags.some(value => fuzzyMatch(value, tag));
    }
    return fuzzyMatch(node.title, term);
  });
}

function graphWithTags() {
  if (!showTagNodes) return allData;
  const tags = new Map();
  const edges = [...allData.edges];
  for (const note of allData.nodes) {
    for (const tag of new Set(note.tags)) {
      const id = `tag:${tag}`;
      if (!tags.has(id)) tags.set(id, {id, title: `#${tag}`, tags: [tag], kind: 'tag'});
      edges.push([note.id, id], [id, note.id]);
    }
  }
  return {nodes: [...allData.nodes, ...tags.values()], edges};
}

function filterGraph(fit = true) {
  let focusLost = false;
  const data = graphWithTags();
  if (focusRoot !== null && !data.nodes.some(node => node.id === focusRoot)) {
    focusRoot = null;
    hovered = null;
    updateFocusControls();
    focusLost = true;
  }
  const input = search.value.trim().toLowerCase();
  const query = input.split(/\s+/).filter(Boolean);
  const focused = focusRoot === null ? null
    : neighborhood(focusRoot, Number(generations.value), data.edges, includeBacklinks);
  const nodes = data.nodes.filter(node =>
    (!focused || focused.has(node.id)) && matchesSearch(node, query)
  );
  const ids = new Set(nodes.map(node => node.id));
  draw(nodes, data.edges.filter(([from, to]) => ids.has(from) && ids.has(to)), data.edges);
  if (fit && nodes.length) fitGraph();
  if (focusLost) resizeGraph();
}

search.addEventListener('input', () => filterGraph());

function render() {
  for (const link of links) {
    const a = positions.get(link.from), b = positions.get(link.to);
    if (a === b) {
      const r = a.radius;
      link.path.setAttribute('d', `M ${a.x + r * 0.7} ${a.y - r * 0.7} C ${a.x + r + 40} ${a.y - r - 60}, ${a.x - r - 40} ${a.y - r - 60}, ${a.x - r * 0.7} ${a.y - r * 0.7}`);
    } else {
      const dx = b.x - a.x, dy = b.y - a.y;
      const distance = Math.max(Math.hypot(dx, dy), 1);
      const ux = dx / distance, uy = dy / distance;
      const startOffset = a.radius + (link.bidirectional ? 5 : 2);
      const startX = a.x + ux * startOffset, startY = a.y + uy * startOffset;
      const endX = b.x - ux * (b.radius + 5), endY = b.y - uy * (b.radius + 5);
      link.path.setAttribute('d', `M ${startX} ${startY} L ${endX} ${endY}`);
    }
  }
  for (const node of positions.values()) {
    node.group.setAttribute('transform', `translate(${node.x} ${node.y})`);
  }
}

function animate() {
  if (energy > 0.001) {
    const nodes = [...positions.values()];
    const centerX = graph.viewBox.baseVal.width / 2;
    const centerY = graph.viewBox.baseVal.height / 2;
    for (let i = 0; i < nodes.length; i++) {
      const a = nodes[i];
      a.vx += (centerX - a.x) * 0.0008;
      a.vy += (centerY - a.y) * 0.0008;
      for (let j = i + 1; j < nodes.length; j++) {
        const b = nodes[j];
        const dx = a.x - b.x, dy = a.y - b.y;
        const distance2 = Math.max(dx * dx + dy * dy, 100);
        const force = 4500 / (distance2 * Math.sqrt(distance2));
        a.vx += dx * force; a.vy += dy * force;
        b.vx -= dx * force; b.vy -= dy * force;
      }
    }
    for (const link of links) {
      const a = positions.get(link.from), b = positions.get(link.to);
      const dx = b.x - a.x, dy = b.y - a.y;
      const distance = Math.max(Math.hypot(dx, dy), 1);
      const force = (distance - 180) * 0.012;
      a.vx += dx / distance * force; a.vy += dy / distance * force;
      b.vx -= dx / distance * force; b.vy -= dy / distance * force;
    }
    for (const node of nodes) {
      if (drag?.kind === 'node' && drag.id === node.id) continue;
      node.vx *= 0.6; node.vy *= 0.6;
      node.x += node.vx; node.y += node.vy;
    }
    render();
    if (refitFrames > 0 && --refitFrames === 0) fitGraph();
    energy *= 0.97;
  }
  requestAnimationFrame(animate);
}

async function refresh() {
  try {
    const response = await fetch('/graph', {cache: 'no-store'});
    if (!response.ok) throw new Error(await response.text());
    const data = await response.json();
    const snapshot = JSON.stringify(data);
    if (snapshot !== previous) {
      allData = data;
      filterGraph(false);
      previous = snapshot;
    }
  } catch (error) {
    console.error('Could not load notes:', error);
  }
}

refresh();
setInterval(refresh, 1000);
requestAnimationFrame(animate);
</script>
</body>
</html>
"""


def graph_data(directory: Path) -> dict[str, list]:
    if not any(directory.glob("*.typ")):
        return {"nodes": [], "edges": []}
    nodes = txtify.load_nodes_from_directory(directory)
    ordered = [nodes[note_id] for note_id in sorted(nodes)]
    return {
        "nodes": [
            {"id": node.note_id, "title": node.title, "tags": node.tags}
            for node in ordered
        ],
        "edges": [
            [node.note_id, link]
            for node in ordered
            for link in dict.fromkeys(node.links)
            if link in nodes
        ],
    }


def make_handler(
    directory: Path, nvim_server: str | None, theme: str = "system"
) -> type[BaseHTTPRequestHandler]:
    if theme not in {"system", "light", "dark"}:
        raise ValueError(f"Invalid theme: {theme}")
    page = PAGE.replace('data-theme="system"', f'data-theme="{theme}"', 1)

    class Handler(BaseHTTPRequestHandler):
        def send(self, code: int, content: str, content_type: str = "text/plain") -> None:
            body = content.encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", f"{content_type}; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:
            if self.path == "/":
                self.send(200, page, "text/html")
            elif self.path == "/graph":
                try:
                    data = graph_data(directory)
                except (ValueError, OSError) as error:
                    self.send(503, str(error))
                    return
                self.send(200, json.dumps(data), "application/json")
            else:
                self.send(404, "Not found")

        def do_POST(self) -> None:
            if self.path != "/open":
                self.send(404, "Not found")
                return
            origin = self.headers.get("Origin")
            host = f"127.0.0.1:{self.server.server_port}"
            if origin != f"http://{host}" or self.headers.get("Host") != host:
                self.send(403, "Invalid origin")
                return
            if self.headers.get("Content-Type") != "application/json":
                self.send(415, "Expected JSON")
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 4096:
                    raise ValueError("Invalid request size")
                note_id = json.loads(self.rfile.read(length))["id"]
                if not isinstance(note_id, str) or note_id not in {
                    node["id"] for node in graph_data(directory)["nodes"]
                }:
                    raise ValueError("Unknown note")
            except (ValueError, KeyError, TypeError, OSError) as error:
                self.send(400, str(error))
                return
            if not nvim_server:
                self.send(503, "Set --nvim-server or NVIM_LISTEN_ADDRESS")
                return
            try:
                subprocess.run(
                    [
                        "nvim", "--server", nvim_server, "--remote",
                        str(directory / f"{note_id}.typ"),
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
            except (OSError, subprocess.SubprocessError) as error:
                self.send(502, f"Neovim remote failed: {error}")
                return
            self.send(200, "Opened")

    return Handler


def run(
    directory: str, port: int = 8000, no_open: bool = False,
    nvim_server: str | None = None, theme: str = "system",
) -> None:
    typ_dir = Path(directory).resolve()
    if not typ_dir.is_dir():
        raise FileNotFoundError(f"Directory not found: {typ_dir}")
    graph_data(typ_dir)
    handler = make_handler(typ_dir, nvim_server or os.environ.get("NVIM_LISTEN_ADDRESS"), theme)
    with ThreadingHTTPServer(("127.0.0.1", port), handler) as server:
        url = f"http://127.0.0.1:{server.server_port}/"
        print(f"Serving live graph at {url} (Ctrl+C to stop)")
        if not no_open:
            webbrowser.open(url)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


def add_subparser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser(
        "live", help="Watch Typst notes and show a live graph in the browser",
        description="Serve a local graph that refreshes as Typst notes change.",
    )
    parser.add_argument("directory", metavar="DIR", help="Directory containing .typ notes")
    parser.add_argument("-p", "--port", type=int, default=8000, metavar="PORT")
    parser.add_argument("-n", "--no-open", action="store_true", help="Do not open the browser")
    parser.add_argument("--nvim-server", help="Neovim listen address (or set NVIM_LISTEN_ADDRESS)")
    parser.add_argument(
        "--theme", choices=("system", "light", "dark"), default="system",
        help="Graph theme (default: %(default)s)",
    )
    parser.set_defaults(func=lambda args: run(
        args.directory, args.port, args.no_open, args.nvim_server, args.theme,
    ))
