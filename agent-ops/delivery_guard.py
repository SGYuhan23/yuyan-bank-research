"""Bounded delivery verification for explicit file-creation requests.

Operator-configured middleware, not a model tool. It cannot authorize operations.
Only the current thread's existing, nonempty published files count as delivery.
"""
import asyncio
import os
import re
from pathlib import Path
from typing import NotRequired

from langchain.agents import AgentState
from langchain.agents.middleware import AgentMiddleware, hook_config
from langchain_core.messages import AIMessage, HumanMessage
from deerflow.agents.middlewares.model_response import has_tool_call_intent

PREFIX = "/mnt/user-data/outputs/"
CREATE = re.compile(r"生成|制作|创建|导出|保存为|写入|交付|create\b|generate\b|export\b|save\b", re.I)
FILE = re.compile(r"(?<![\w.-])([\w\-]+\.(?:json|md|html|csv|txt|pdf|xlsx|docx|pptx|png|jpg|svg|drawio|zip))\b", re.I)
KINDS = re.compile(r"文件|报告|图片|插画|流程图|表格|HTML|PDF|CSV|JSON|report|image|file|spreadsheet|diagram", re.I)
NO_CREATE = re.compile(r"不要(?:创建|生成|写入|保存)|不(?:需要|用)(?:创建|生成|保存)|只(?:需|要)?(?:解释|说明)|(?:解释|说明|介绍)(?:一下)?(?:如何|怎么)|do not (?:create|write|save)|explain how", re.I)
INPUT_CLAUSE = re.compile(r"(?:输入文件|输入为|源文件|读取|input files?\b|from\b)", re.I)
REMINDER = "交付检查尚未通过：本轮请求的成果文件未全部生成并展示。继续执行已授权任务，实际写入、核对文件并用 present_files 展示；保留旧版本。不要只描述将要执行的操作。若确实缺信息，使用 ask_clarification；工具不可用就如实说明，禁止虚构文件。"


def creation_clause(text):
    if NO_CREATE.search(text):
        return None
    start = CREATE.search(text)
    if not start:
        return None
    clause = INPUT_CLAUSE.split(text[start.start():], maxsplit=1)[0]
    return clause if KINDS.search(clause) or FILE.search(clause) else None


def requested_outputs(text):
    clause = creation_clause(text)
    return set(FILE.findall(clause)) if clause else set()


def current_prompt(state):
    for m in reversed(state.get("messages", [])):
        if isinstance(m, HumanMessage) and not m.additional_kwargs.get("hide_from_ui"):
            return str(m.content)
    return ""


def published_files(state):
    """Host path is provisioned by thread middleware; never read model paths."""
    root_value = (state.get("thread_data") or {}).get("outputs_path")
    if not root_value:
        return {}
    root = Path(root_value).resolve()
    found = {}
    for virtual in (state.get("artifacts") or [])[:1000]:
        if not isinstance(virtual, str) or not virtual.startswith(PREFIX):
            continue
        relative = Path(virtual[len(PREFIX):])
        if relative.is_absolute() or ".." in relative.parts:
            continue
        path = root / relative
        try:
            # Reject links, including a linked parent, even if their target is inside.
            if any((root / Path(*relative.parts[:i])).is_symlink() for i in range(1, len(relative.parts) + 1)):
                continue
            if not path.resolve().is_relative_to(root) or not path.is_file():
                continue
            stat = path.stat()
            if stat.st_size:
                found[relative.as_posix()] = f"{stat.st_size}:{stat.st_mtime_ns}"
        except OSError:
            continue
    return found


def existing_files(state):
    """Snapshot all outputs, including files never presented in an earlier run."""
    value = (state.get("thread_data") or {}).get("outputs_path")
    if not value:
        return {}
    root = Path(value).resolve()
    paths = []
    for base, dirs, names in os.walk(root, followlinks=False):
        dirs[:] = [d for d in dirs if not (Path(base) / d).is_symlink()]
        for name in names:
            paths.append(PREFIX + (Path(base) / name).relative_to(root).as_posix())
            if len(paths) > 1000:
                # Fail explicitly; never silently accept files beyond a partial baseline.
                raise ValueError("Too many output files to establish a complete delivery baseline (limit 1000).")
    return published_files({**state, "artifacts": paths})


class DeliveryState(AgentState):
    delivery_run_id: NotRequired[str]
    delivery_retries: NotRequired[int]
    delivery_baseline: NotRequired[dict[str, str]]


class DeliveryGuard(AgentMiddleware[DeliveryState]):
    state_schema = DeliveryState

    def before_agent(self, state, runtime):
        return {"delivery_run_id": (runtime.context or {}).get("run_id", ""),
                "delivery_retries": 0, "delivery_baseline": existing_files(state) if creation_clause(current_prompt(state)) else {}}

    async def abefore_agent(self, state, runtime):
        return await asyncio.to_thread(self.before_agent, state, runtime)

    @hook_config(can_jump_to=["model"])
    def after_model(self, state, runtime):
        messages = state.get("messages") or []
        if not messages or not isinstance(messages[-1], AIMessage):
            return None
        last = messages[-1]
        if has_tool_call_intent(last) or any(last.additional_kwargs.get(k) for k in (
            "deerflow_error_fallback", "model_length_termination", "safety_termination")):
            return None
        if (runtime.context or {}).get("stop_reason"):
            return None
        prompt = current_prompt(state)
        if not creation_clause(prompt):
            return None
        files = published_files(state)
        baseline = state.get("delivery_baseline", {})
        fresh = {Path(n).name for n, sig in files.items() if baseline.get(n) != sig}
        expected = requested_outputs(prompt)
        if fresh and (not expected or expected <= fresh):
            return None
        count = state.get("delivery_retries", 0) if state.get("delivery_run_id", "") == (runtime.context or {}).get("run_id", "") else 0
        if count < 2:
            return {"delivery_run_id": (runtime.context or {}).get("run_id", ""),
                    "delivery_retries": count + 1, "jump_to": "model"}
        failure = last.model_copy(update={
            "content": "本次文件交付未完成：未能核验全部所需文件已生成并展示。已进行两次继续执行尝试，现停止自动重试。已生成的文件和执行记录保留，你可以查看错误并继续任务。",
            "additional_kwargs": {**last.additional_kwargs, "deerflow_error_fallback": True,
                                  "error_reason": "Requested file delivery was not verified", "delivery_incomplete": True}})
        return {"messages": [failure]}

    @hook_config(can_jump_to=["model"])
    async def aafter_model(self, state, runtime):
        return await asyncio.to_thread(self.after_model, state, runtime)

    def _request(self, request):
        if not request.state.get("delivery_retries"):
            return request
        return request.override(messages=[*request.messages, HumanMessage(
            content=REMINDER, name="delivery_check", additional_kwargs={"hide_from_ui": True})])

    def wrap_model_call(self, request, handler):
        return handler(self._request(request))

    async def awrap_model_call(self, request, handler):
        return await handler(self._request(request))
