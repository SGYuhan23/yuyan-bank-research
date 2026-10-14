from xml.etree import ElementTree as ET
import pytest
from diagram import render_diagram


def test_editable_diagram_and_safe_labels():
    svg, xml = render_diagram(
        "流程 <test>",
        [{"id": "a", "label": "输入 <数据>"}, {"id": "b", "label": "输出 & 检查"}],
        [{"source": "a", "target": "b", "label": "确认"}],
    )
    ET.fromstring(svg)
    root = ET.fromstring(xml)
    assert len(root.findall('.//mxCell[@vertex="1"]')) == 2
    assert len(root.findall('.//mxCell[@edge="1"]')) == 1
    assert "<数据>" not in svg and "&lt;数据&gt;" in svg


def test_invalid_graph_is_rejected():
    for nodes, edges in [
        ([{"id": "a", "label": "a"}, {"id": "a", "label": "b"}], []),
        ([{"id": "a", "label": "a"}], [{"source": "a", "target": "missing"}]),
        ([], []),
    ]:
        with pytest.raises(ValueError):
            render_diagram("test", nodes, edges)


def test_tool_publishes_both_artifacts_without_second_llm_call(tmp_path, monkeypatch):
    import diagram
    from types import SimpleNamespace

    monkeypatch.setattr(diagram, "_get_thread_id", lambda r: "thread")
    monkeypatch.setattr(diagram, "resolve_runtime_user_id", lambda r: "user")
    monkeypatch.setattr(
        diagram,
        "get_paths",
        lambda: SimpleNamespace(
            resolve_virtual_path=lambda t, p, **k: tmp_path / p.rsplit("/", 1)[-1]
        ),
    )
    result = diagram.draw_diagram.func(
        runtime=SimpleNamespace(),
        title="测试",
        nodes=[diagram.Node(id="a", label="起点")],
        edges=[],
        tool_call_id="call1",
    )
    assert len(result.update["artifacts"]) == 2
    assert result.update["messages"][0].tool_call_id == "call1"
    for artifact in result.update["artifacts"]:
        assert (tmp_path / artifact.rsplit("/", 1)[-1]).stat().st_size > 0


def test_branch_merge_and_cycle_layout():
    from diagram import graph_positions

    nodes = [{"id": i, "label": i} for i in ["start", "left", "right", "end"]]
    edges = [
        {"source": a, "target": b}
        for a, b in [
            ("start", "left"),
            ("start", "right"),
            ("left", "end"),
            ("right", "end"),
        ]
    ]
    p, w, h = graph_positions(nodes, edges)
    assert p["start"][1] < p["left"][1] == p["right"][1] < p["end"][1]
    assert abs(p["left"][0] - p["right"][0]) >= 300
    p, w, h = graph_positions(nodes, edges + [{"source": "end", "target": "start"}])
    assert len(set(p.values())) == 4
    assert all(0 <= x < w and 0 <= y < h for x, y in p.values())
