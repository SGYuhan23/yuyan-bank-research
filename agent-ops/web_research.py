"""Explicit Qwen search adapter. Return retrieved sources, never synthetic facts."""

import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo
import httpx
from langchain.tools import tool
from deerflow.tools.types import Runtime
from langchain_core.messages import ToolMessage
from research_policy import current_turn, is_lookup


def search_qwen(query, *, endpoint, model, key, max_results=8, transport=None):
    if not key or not endpoint or not model:
        return {
            "status": "unavailable",
            "provider": "qwen-search",
            "error": "Search configuration missing.",
        }
    payload = {
        "model": model,
        "input": {
            "messages": [
                {
                    "role": "system",
                    "content": "Retrieve web sources for the user query. Prefer original announcements, official documentation and primary evidence. Keep your summary under 80 words. Do not invent sources. Today is "
                    + datetime.now(ZoneInfo("Asia/Shanghai")).date().isoformat(),
                },
                {"role": "user", "content": query},
            ]
        },
        "parameters": {
            "enable_thinking": False,
            "enable_search": True,
            "search_options": {
                "forced_search": True,
                "enable_source": True,
                "search_strategy": "max",
            },
            "result_format": "message",
            "max_tokens": 200,
        },
    }
    try:
        with httpx.Client(timeout=50, transport=transport) as client:
            response = client.post(
                endpoint, json=payload, headers={"Authorization": "Bearer " + key}
            )
        if response.status_code != 200:
            return {
                "status": "unavailable",
                "provider": "qwen-search",
                "error": f"Provider HTTP {response.status_code}; no model fallback.",
            }
        body = response.json()
        results = (
            body.get("output", {}).get("search_info", {}).get("search_results", [])
        )
        sources = []
        seen = set()
        for result in results:
            url = result.get("url", "")
            if (
                not isinstance(url, str)
                or not url.startswith(("https://", "http://"))
                or url in seen
            ):
                continue
            seen.add(url)
            sources.append(
                {
                    "title": str(result.get("title", ""))[:400],
                    "url": url,
                    "site_name": str(result.get("site_name", ""))[:100],
                }
            )
        if not sources:
            return {
                "status": "unavailable",
                "provider": "qwen-search",
                "error": "Provider returned no verifiable search sources. Do not infer the subject does not exist.",
            }
        return {
            "status": "success",
            "provider": "qwen-search",
            "model": model,
            "query": query,
            "results": sources[: max(1, min(max_results, 10))],
            "usage": body.get("usage", {}),
            "request_id": body.get("request_id"),
            "evidence_note": "These are search results, not downloaded files or verified page contents. Use web_fetch on returned URLs. No synthetic provider answer has been included.",
        }
    except (httpx.HTTPError, ValueError, TypeError, AttributeError):
        return {
            "status": "unavailable",
            "provider": "qwen-search",
            "error": "Search request failed. Do not infer nonexistence.",
        }


@tool("web_search", parse_docstring=True)
def web_search_tool(runtime: Runtime, query: str, max_results: int = 8) -> str:
    """Search current web sources with forced provider retrieval. Returns actual source URLs, not a model-written answer. Fetch relevant URLs to verify facts. If sources are weak, refine your query or find the organization's news/investor-relations site. Search failures never prove nonexistence.

    Args:
        query: Specific search query, retaining the user's original product or entity name.
        max_results: Maximum source results, between 1 and 10.
    """
    turn = current_turn(runtime.state.get("messages", []))
    if turn:
        original = str(
            turn[0].additional_kwargs.get("original_user_content") or turn[0].content
        )
        if is_lookup(original) and not any(
            isinstance(m, ToolMessage) and m.name == "web_search" for m in turn
        ):
            query = original
    if not query.strip() or len(query) > 1000:
        return json.dumps(
            {"status": "error", "error": "Search query must contain 1–1000 characters."}
        )
    config = {
        "endpoint": os.environ.get("QWEN_SEARCH_ENDPOINT", ""),
        "model": os.environ.get("QWEN_MODEL", ""),
        "key": os.environ.get("QWEN_API_KEY", ""),
    }
    from concurrent.futures import ThreadPoolExecutor

    with ThreadPoolExecutor(max_workers=2) as pool:
        native = pool.submit(search_qwen, query, **config, max_results=10)
        translated = (
            english_query(query, **config)
            if any("\u4e00" <= ch <= "\u9fff" for ch in query)
            else None
        )
        other = (
            search_qwen(translated, **config, max_results=10) if translated else None
        )
        result = native.result()
    if other and other.get("status") == "success":
        seen = set()
        merged = []
        for item in [*other["results"], *result.get("results", [])]:
            if item["url"] not in seen:
                merged.append(item)
                seen.add(item["url"])
        result = {
            **result,
            "status": "success",
            "results": merged[:16],
            "queries": [query, translated],
            "secondary_usage": other.get("usage", {}),
            "secondary_request_id": other.get("request_id"),
        }
        result.pop("error", None)
    return json.dumps(result, ensure_ascii=False)


def english_query(query, *, endpoint, model, key):
    """Translate search terms only. Output is an untrusted query, never evidence."""
    try:
        with httpx.Client(timeout=25) as c:
            r = c.post(
                endpoint,
                json={
                    "model": model,
                    "input": {
                        "messages": [
                            {
                                "role": "system",
                                "content": "Translate the search query into English for finding primary sources. Preserve product/version names verbatim. Use the official English company name if known. Return only the query plus official press release. Never answer the question or add years, specifications, prices, facts or URLs.",
                            },
                            {"role": "user", "content": query},
                        ]
                    },
                    "parameters": {
                        "enable_thinking": False,
                        "result_format": "message",
                        "max_tokens": 80,
                    },
                },
                headers={"Authorization": "Bearer " + key},
            )
        if r.status_code != 200:
            return None
        text = r.json()["output"]["choices"][0]["message"]["content"].strip()
        return text if 0 < len(text) < 350 and "http" not in text else None
    except (httpx.HTTPError, KeyError, IndexError, ValueError):
        return None
