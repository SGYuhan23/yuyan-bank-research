import pytest

from research_policy import is_lookup, unsupported_answer


def test_lookup_routing_is_general_and_respects_no_web():
    assert is_lookup("你知道理想l8 livis吗")
    assert is_lookup("你知道 Acme 新发布的相机吗？")
    assert not is_lookup("不要联网，你知道理想L8吗")
    assert not is_lookup("帮我画一张猫咪插画")
    assert not is_lookup("你知道怎么修改这个文件吗")


def test_absence_and_invented_citations_fail_closed():
    assert unsupported_answer("这个车型不是真实存在的车型。", set())
    assert unsupported_answer(
        "见 [官方](https://example.org/fake)", {"https://example.org/real"}
    )
    assert not unsupported_answer("未能核实这个型号。", set())
    assert not unsupported_answer(
        "有的，见 [来源](https://example.org/real)", {"https://example.org/real"}
    )


@pytest.mark.asyncio
async def test_lookup_changes_actual_model_request():
    from langchain.agents.middleware.types import ModelRequest, ModelResponse
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
    from research_policy import ResearchPolicy, LOOKUP_SYSTEM

    request = ModelRequest(
        model=None,
        messages=[HumanMessage("你知道理想l8 livis吗", name="user-input")],
        system_message=SystemMessage("old"),
        tools=[{"name": "web_search"}, {"name": "web_fetch"}],
    )
    seen = []

    async def handle(req):
        seen.append(req)
        return ModelResponse(result=[AIMessage("未能核实。")])

    await ResearchPolicy().awrap_model_call(request, handle)
    assert seen[0].system_message.content == LOOKUP_SYSTEM
    assert seen[0].model_settings["tool_choice"]["function"]["name"] == "web_search"


@pytest.mark.asyncio
async def test_profile_removes_framework_hints_and_bounds_output():
    from langchain.agents.middleware.types import ModelRequest, ModelResponse
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
    from research_policy import ResearchPolicy

    request = ModelRequest(
        model=None,
        messages=[
            HumanMessage("framework hint " * 100),
            HumanMessage("你知道理想l8 livis吗", name="user-input"),
        ],
        system_message=SystemMessage("old"),
        tools=[{"name": "web_search"}, {"name": "web_fetch"}],
    )

    async def handle(req):
        assert len(req.messages) == 1
        assert req.model_settings["max_tokens"] == 450
        return ModelResponse(result=[AIMessage("未能核实。")])

    await ResearchPolicy().awrap_model_call(request, handle)


def test_final_state_guard_blocks_denial_and_preserves_id():
    from langchain_core.messages import HumanMessage, AIMessage
    from research_policy import ResearchPolicy

    m = AIMessage("不是真实存在的量产车型。", id="final")
    result = ResearchPolicy().after_model(
        {"messages": [HumanMessage("你知道某某新车吗"), m]}, None
    )
    assert "未能可靠核实" in result["messages"][0].content
    assert result["messages"][0].id == "final"


def test_positive_correction_is_not_a_denial():
    assert not unsupported_answer("这不是误传，而是官方命名的版本。", set())
    assert not unsupported_answer("Livis并非虚构名称，属于官方命名。", set())


def test_final_state_keeps_positive_answer_and_real_source():
    from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
    from research_policy import ResearchPolicy

    url = "https://manufacturer.example/news/new-product"
    messages = [
        HumanMessage("你知道示例新产品吗"),
        AIMessage(
            "", tool_calls=[{"name": "web_fetch", "id": "fetch1", "args": {"url": url}}]
        ),
        ToolMessage(
            "Official source text. " * 20, name="web_fetch", tool_call_id="fetch1"
        ),
        AIMessage("这不是误传，而是官方命名的版本。\n\n不需要展开的内容。", id="final"),
    ]
    result = ResearchPolicy().after_model({"messages": messages}, None)["messages"][0]
    assert "官方命名" in result.content and url in result.content
    assert "不需要展开" in result.content


def test_simple_lookup_omits_unsolicited_specification_expansion():
    from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
    from research_policy import ResearchPolicy

    url = "https://example.org/release"
    messages = [
        HumanMessage("你知道Zeta-X9吗"),
        AIMessage(
            "", tool_calls=[{"name": "web_fetch", "id": "f", "args": {"url": url}}]
        ),
        ToolMessage("official article " * 30, name="web_fetch", tool_call_id="f"),
        AIMessage("Zeta-X9是已发布的新版本。\n\n" + ("不需要的配置扩写。" * 60)),
    ]
    result = ResearchPolicy().after_model({"messages": messages}, None)["messages"][0]
    assert "新版本" in result.content and "配置扩写" not in result.content
    assert url in result.content
