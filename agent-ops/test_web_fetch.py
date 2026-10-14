import pytest
import web_fetch


@pytest.mark.asyncio
async def test_source_content_404_is_not_http_failure(monkeypatch):
    async def crawl(*a, **k):
        return "A legitimate article mentions HTTP 404. " * 100

    monkeypatch.setattr(web_fetch.JinaClient, "crawl", crawl)
    monkeypatch.setattr(
        web_fetch.socket,
        "getaddrinfo",
        lambda *a, **k: [(2, 1, 6, "", ("93.184.216.34", 443))],
    )
    web_fetch._CACHE.clear()
    first = await web_fetch.fetch_page("https://example.org/article")
    second = await web_fetch.fetch_page("https://example.org/article")
    assert first["status"] == "success" and second["cached"]
    assert first["sha256"] == second["sha256"]


@pytest.mark.asyncio
async def test_error_not_cached_as_evidence(monkeypatch):
    async def crawl(*a, **k):
        return "Error: blocked"

    monkeypatch.setattr(web_fetch.JinaClient, "crawl", crawl)
    monkeypatch.setattr(
        web_fetch.socket,
        "getaddrinfo",
        lambda *a, **k: [(2, 1, 6, "", ("93.184.216.34", 443))],
    )
    web_fetch._CACHE.clear()
    assert (await web_fetch.fetch_page("https://example.org/error"))[
        "status"
    ] == "unavailable"
    assert not web_fetch._CACHE


@pytest.mark.asyncio
async def test_private_targets_rejected(monkeypatch):
    monkeypatch.setattr(
        web_fetch.socket,
        "getaddrinfo",
        lambda *a, **k: [(2, 1, 6, "", ("127.0.0.1", 443))],
    )
    assert (await web_fetch.fetch_page("http://localhost/secrets"))[
        "status"
    ] == "unavailable"
