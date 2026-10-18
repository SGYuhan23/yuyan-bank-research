"""Delivery is verified from files, never from an assistant's success claim."""
from types import SimpleNamespace
from pathlib import Path
from langchain_core.messages import AIMessage, HumanMessage
from delivery_guard import DeliveryGuard, requested_outputs


def state(tmp_path, prompt="生成 result.json 和 summary.md 并展示"):
    return {"messages": [HumanMessage(content=prompt), AIMessage(content="已经完成。")],
            "thread_data": {"outputs_path": str(tmp_path)}, "artifacts": []}


def runtime():
    return SimpleNamespace(context={"run_id": "run-1"})


def test_extract_only_output_names():
    assert requested_outputs("读取 sales.csv，用Python计算，在 outputs 生成 result.json、summary.md 和 report.html") == {"result.json", "summary.md", "report.html"}


def test_full_output_paths_and_trailing_input_reference():
    assert requested_outputs("生成 /mnt/user-data/outputs/a.json 和 /mnt/user-data/outputs/b.md") == {"a.json", "b.md"}
    assert requested_outputs("请生成 result.json 和 summary.md，输入文件为 sales.csv") == {"result.json", "summary.md"}


def test_explain_how_is_not_execution(tmp_path):
    assert DeliveryGuard().after_model(state(tmp_path, "请解释如何生成 PDF 文件"), runtime()) is None


def test_old_unpublished_file_cannot_be_claimed_as_new(tmp_path):
    s = state(tmp_path, "生成 result.json")
    (tmp_path / "result.json").write_text("old")
    g = DeliveryGuard()
    s.update(g.before_agent(s, runtime()))
    s["artifacts"] = ["/mnt/user-data/outputs/result.json"]
    assert g.after_model(s, runtime())["jump_to"] == "model"


def test_read_only_question_does_not_require_file(tmp_path):
    s = state(tmp_path, "解释如何读取 result.json，不要创建文件")
    assert DeliveryGuard().after_model(s, runtime()) is None


def test_premature_terminal_response_is_reengaged(tmp_path):
    s = state(tmp_path)
    assert DeliveryGuard().after_model(s, runtime())["jump_to"] == "model"


def test_missing_or_partial_published_files_do_not_pass(tmp_path):
    (tmp_path / "result.json").write_text('{"total": 5350}')
    s = state(tmp_path)
    s["artifacts"] = ["/mnt/user-data/outputs/result.json", "/mnt/user-data/outputs/summary.md"]
    assert DeliveryGuard().after_model(s, runtime())["jump_to"] == "model"


def test_empty_and_symlink_artifacts_do_not_pass(tmp_path):
    (tmp_path / "result.json").write_text("")
    (tmp_path / "summary.md").symlink_to(Path(__file__))
    s = state(tmp_path)
    s["artifacts"] = ["/mnt/user-data/outputs/result.json", "/mnt/user-data/outputs/summary.md"]
    assert DeliveryGuard().after_model(s, runtime())["jump_to"] == "model"


def test_actual_published_files_pass(tmp_path):
    s = state(tmp_path)
    for n in ("result.json", "summary.md"):
        (tmp_path / n).write_text("real content")
        s["artifacts"].append("/mnt/user-data/outputs/" + n)
    assert DeliveryGuard().after_model(s, runtime()) is None


def test_old_artifact_does_not_satisfy_new_creation(tmp_path):
    s = state(tmp_path, "制作一个HTML报告并交付文件")
    (tmp_path / "old.html").write_text("old")
    s["artifacts"] = ["/mnt/user-data/outputs/old.html"]
    g = DeliveryGuard()
    s.update(g.before_agent(s, runtime()))
    assert g.after_model(s, runtime())["jump_to"] == "model"


def test_bounded_failure_is_error_not_success(tmp_path):
    s = state(tmp_path)
    s.update(delivery_run_id="run-1", delivery_retries=2)
    update = DeliveryGuard().after_model(s, runtime())
    assert "jump_to" not in update
    assert update["messages"][0].additional_kwargs["deerflow_error_fallback"] is True
    assert "未完成" in update["messages"][0].content


def test_provider_failure_is_not_retried(tmp_path):
    s = state(tmp_path)
    s["messages"][-1].additional_kwargs["deerflow_error_fallback"] = True
    assert DeliveryGuard().after_model(s, runtime()) is None


def test_active_tools_are_left_alone(tmp_path):
    s = state(tmp_path)
    s["messages"][-1] = AIMessage(content="", tool_calls=[{"name": "ask_clarification", "args": {}, "id": "clarify"}])
    assert DeliveryGuard().after_model(s, runtime()) is None


def test_real_graph_caps_reengagement_and_keeps_reminder_out_of_history():
    from langchain.agents import create_agent
    from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
    model = FakeMessagesListChatModel(responses=[AIMessage(content="我将生成文件。")])
    graph = create_agent(model, tools=[], middleware=[DeliveryGuard()])
    result = graph.invoke({"messages": [HumanMessage(content="生成 result.json 文件")]})
    assert result["delivery_retries"] == 2
    assert result["messages"][-1].additional_kwargs["delivery_incomplete"]
    assert not any(m.name == "delivery_check" for m in result["messages"])
