"""Bounded graph renderer with SVG preview and editable Draw.io source."""

import json
import uuid
from html import escape
from xml.etree.ElementTree import Element, SubElement, tostring
from pydantic import BaseModel, Field, ConfigDict
from typing import Annotated
from langchain.tools import tool, InjectedToolCallId
from langchain_core.messages import ToolMessage
from langgraph.types import Command
from deerflow.tools.types import Runtime
from deerflow.tools.builtins.present_file_tool import _get_thread_id
from deerflow.runtime.user_context import resolve_runtime_user_id
from deerflow.config.paths import get_paths


class Node(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(min_length=1, max_length=40, pattern=r"^[a-zA-Z][a-zA-Z0-9_-]*$")
    label: str = Field(min_length=1, max_length=60)


class Edge(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source: str
    target: str
    label: str = Field(default="", max_length=30)


def graph_positions(nodes, edges):
    """Layer a directed graph; break DFS back edges for ranking, retain them in output."""
    nodes = [Node.model_validate(n) for n in nodes]
    edges = [Edge.model_validate(e) for e in edges]
    adjacency = {n.id: [] for n in nodes}
    for edge in edges:
        adjacency[edge.source].append(edge.target)
    colors, forward, order = {}, {n.id: [] for n in nodes}, []

    def visit(node):
        colors[node] = 1
        for target in adjacency[node]:
            if colors.get(target) == 1:
                continue
            forward[node].append(target)
            if not colors.get(target):
                visit(target)
        colors[node] = 2
        order.append(node)

    for node in nodes:
        if not colors.get(node.id):
            visit(node.id)
    ranks = {n.id: 0 for n in nodes}
    for node in reversed(order):
        for target in forward[node]:
            ranks[target] = max(ranks[target], ranks[node] + 1)
    layers = {}
    for node in nodes:
        layers.setdefault(ranks[node.id], []).append(node.id)
    # Barycentric sweeps reduce crossing of branch/merge connections.
    for _ in range(4):
        for rank in sorted(layers):
            previous = {
                n: i
                for r, layer in layers.items()
                if r < rank
                for i, n in enumerate(layer)
            }

            def center(node):
                parents = [
                    previous[e.source]
                    for e in edges
                    if e.target == node and e.source in previous
                ]
                return (
                    sum(parents) / len(parents) if parents else layers[rank].index(node)
                )

            layers[rank] = sorted(layers[rank], key=center)
    width = max(map(len, layers.values())) * 300 + 160
    height = (max(layers) + 1) * 190 + 100
    positions = {
        node: ((width - len(layer) * 300) / 2 + i * 300 + 40, 90 + rank * 190)
        for rank, layer in layers.items()
        for i, node in enumerate(layer)
    }
    return positions, width, height


def render_diagram(title, nodes, edges):
    nodes = [Node.model_validate(n) for n in nodes]
    edges = [Edge.model_validate(e) for e in edges]
    ids = {n.id for n in nodes}
    if (
        not 1 <= len(nodes) <= 24
        or len(ids) != len(nodes)
        or len(edges) > 48
        or len(title) > 80
    ):
        raise ValueError(
            "流程图需要 1–24 个唯一节点、至多 48 条连接，标题至多 80 字符。"
        )
    if any(e.source not in ids or e.target not in ids for e in edges):
        raise ValueError("连接必须引用存在的节点。")
    if any(e.source == e.target for e in edges):
        raise ValueError("当前布局不支持自连接。")
    positions, width, height = graph_positions(nodes, edges)
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}"><rect width="100%" height="100%" fill="#f8fafc"/><defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8" fill="#64748b"/></marker></defs>',
        f'<text x="40" y="42" font-family="sans-serif" font-size="22" fill="#0f172a">{escape(title)}</text>',
    ]
    doc = Element("mxfile", host="app.diagrams.net")
    page = SubElement(doc, "diagram", name="Page-1", id="main")
    model = SubElement(
        page, "mxGraphModel", page="1", pageWidth=str(width), pageHeight=str(height)
    )
    root = SubElement(model, "root")
    SubElement(root, "mxCell", id="0")
    SubElement(root, "mxCell", id="1", parent="0")
    for i, e in enumerate(edges):
        x, y = positions[e.source]
        tx, ty = positions[e.target]
        x += 110
        y += 80
        tx += 110
        if ty <= y:
            # Feedback travels outside the node columns instead of through boxes.
            lane = width - 18 - (i % 5) * 12
            path = f"M{x + 110},{y - 40} L{lane},{y - 40} L{lane},{ty + 40} L{tx + 110},{ty + 40}"
            lx, ly = lane - 8, (y + ty) / 2
        else:
            mid = (y + ty) / 2
            path = f"M{x},{y} L{x},{mid} L{tx},{mid} L{tx},{ty}"
            lx, ly = (x + tx) / 2 + 6, mid - 8
        svg.append(
            f'<path d="{path}" fill="none" stroke="#64748b" stroke-width="2" marker-end="url(#arrow)"/>'
        )
        if e.label:
            svg.append(
                f'<text x="{lx}" y="{ly}" font-family="sans-serif" font-size="12" fill="#334155" paint-order="stroke" stroke="#f8fafc" stroke-width="4">{escape(e.label)}</text>'
            )
        cell = SubElement(
            root,
            "mxCell",
            id=f"edge-{i}",
            value=e.label,
            edge="1",
            parent="1",
            source="node-" + e.source,
            target="node-" + e.target,
            style="edgeStyle=orthogonalEdgeStyle;rounded=1;html=0;endArrow=block;",
        )
        SubElement(cell, "mxGeometry", relative="1", **{"as": "geometry"})
    for n in nodes:
        x, y = positions[n.id]
        svg.append(
            f'<rect x="{x}" y="{y}" width="220" height="80" rx="12" fill="white" stroke="#94a3b8"/>'
        )
        lines = [n.label[i : i + 16] for i in range(0, len(n.label), 16)]
        for j, line in enumerate(lines):
            svg.append(
                f'<text x="{x + 110}" y="{y + 22 + j * 16}" text-anchor="middle" font-family="sans-serif" font-size="13" fill="#0f172a">{escape(line)}</text>'
            )
        cell = SubElement(
            root,
            "mxCell",
            id="node-" + n.id,
            value=n.label,
            vertex="1",
            parent="1",
            style="rounded=1;whiteSpace=wrap;html=0;fillColor=#ffffff;strokeColor=#94a3b8;",
        )
        SubElement(
            cell,
            "mxGeometry",
            x=str(x),
            y=str(y),
            width="220",
            height="80",
            **{"as": "geometry"},
        )
    svg.append("</svg>")
    return "".join(svg), tostring(doc, encoding="unicode")


@tool("draw_diagram", parse_docstring=True)
def draw_diagram(
    runtime: Runtime,
    title: str,
    nodes: list[Node],
    edges: list[Edge],
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> Command | str:
    """Create a directed flowchart with layered branch/merge layout, feedback edges, SVG preview and editable Draw.io source. Never use this as a substitute for photographic image generation. Present the returned files with present_files.

    Args:
        title: Diagram title, up to 80 characters.
        nodes: 1–24 nodes with unique id and short label, in reading order.
        edges: Connections with source and target node ids and optional label.
    """
    tid = _get_thread_id(runtime)
    uid = resolve_runtime_user_id(runtime)
    if not tid or not uid or uid == "default":
        return json.dumps(
            {"status": "error", "message": "需要已鉴权会话。"}, ensure_ascii=False
        )
    try:
        svg, xml = render_diagram(title, nodes, edges)
        prefix = "/mnt/user-data/outputs/diagram-" + uuid.uuid4().hex
        for suffix, content in [(".svg", svg), (".drawio", xml)]:
            path = get_paths().resolve_virtual_path(tid, prefix + suffix, user_id=uid)
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("x") as f:
                f.write(content)
        artifacts = [prefix + ".svg", prefix + ".drawio"]
        return Command(
            update={
                "artifacts": artifacts,
                "messages": [
                    ToolMessage(
                        json.dumps(
                            {
                                "status": "success",
                                "artifacts": artifacts,
                                "layout": "layered-directed",
                                "editable": True,
                            },
                            ensure_ascii=False,
                        ),
                        tool_call_id=tool_call_id,
                    )
                ],
            }
        )
    except ValueError as e:
        return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)
