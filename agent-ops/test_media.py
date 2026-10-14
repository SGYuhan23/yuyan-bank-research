"""Provider responses below are explicit test doubles, never runtime fallbacks."""

import httpx, pytest
from media import ImageProvider, ImageUnavailable, validate_prompt


def test_missing_configuration_never_fakes_image():
    with pytest.raises(ImageUnavailable):
        ImageProvider("", "", "").generate("a tree", "1024*1024")


def test_prompt_and_size_validated():
    for p, s in [
        ("", "1024*1024"),
        ("x", "99999*99999"),
        ("x", "abc"),
        ("x" * 6000, "1024*1024"),
    ]:
        with pytest.raises(ValueError):
            validate_prompt(p, s)


def test_provider_contract_and_no_secret_in_error():
    def handle(r):
        assert r.headers["authorization"] == "Bearer secret-test-only"
        return httpx.Response(401, json={"message": "secret-test-only"})

    p = ImageProvider(
        "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation",
        "qwen-image-2.0",
        "secret-test-only",
        transport=httpx.MockTransport(handle),
    )
    with pytest.raises(ImageUnavailable) as e:
        p.generate("a tree", "1024*1024")
    assert "secret-test-only" not in str(e.value)


def test_success_uses_only_declared_model_and_persists_bytes():
    import json
    from PIL import Image
    from io import BytesIO

    b = BytesIO()
    Image.new("RGB", (10, 10)).save(b, format="PNG")

    def handle(r):
        if r.method == "POST":
            assert json.loads(r.content)["model"] == "qwen-image-2.0"
            return httpx.Response(
                200,
                json={
                    "request_id": "test",
                    "output": {
                        "choices": [
                            {
                                "message": {
                                    "content": [
                                        {
                                            "image": "https://dashscope-result.oss-cn-beijing.aliyuncs.com/x.png"
                                        }
                                    ]
                                }
                            }
                        ]
                    },
                },
            )
        assert "authorization" not in r.headers
        return httpx.Response(
            200, content=b.getvalue(), headers={"content-type": "image/png"}
        )

    p = ImageProvider(
        "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation",
        "qwen-image-2.0",
        "test",
        transport=httpx.MockTransport(handle),
    )
    data, meta = p.generate("a tree", "1024*1024")
    assert data == b.getvalue()
    assert meta["model"] == "qwen-image-2.0"


def test_private_download_rejected():
    def handle(r):
        return httpx.Response(
            200,
            json={
                "output": {
                    "choices": [
                        {"message": {"content": [{"image": "https://127.0.0.1/x"}]}}
                    ]
                }
            },
        )

    with pytest.raises(ImageUnavailable):
        ImageProvider(
            "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation",
            "qwen-image-2.0",
            "test",
            transport=httpx.MockTransport(handle),
        ).generate("x", "1024*1024")


def test_generated_image_is_published_atomically_in_tool_result(tmp_path, monkeypatch):
    import media
    from types import SimpleNamespace

    monkeypatch.setattr(media, "_get_thread_id", lambda r: "thread")
    monkeypatch.setattr(media, "resolve_runtime_user_id", lambda r: "user")
    monkeypatch.setattr(
        media,
        "get_paths",
        lambda: SimpleNamespace(
            resolve_virtual_path=lambda t, p, **k: tmp_path / p.rsplit("/", 1)[-1]
        ),
    )
    monkeypatch.setattr(
        media.ImageProvider,
        "generate",
        lambda *a: (b"test-png-bytes", {"model": "test-double"}),
    )
    result = media.generate_image.func(
        runtime=SimpleNamespace(), prompt="test", tool_call_id="call1"
    )
    assert len(result.update["artifacts"]) == 1
    assert result.update["messages"][0].tool_call_id == "call1"
    artifact = result.update["artifacts"][0]
    assert (tmp_path / artifact.rsplit("/", 1)[-1]).read_bytes() == b"test-png-bytes"


def test_edit_sources_reject_paths_and_validate_image(tmp_path, monkeypatch):
    import media
    from types import SimpleNamespace

    monkeypatch.setattr(
        media,
        "get_paths",
        lambda: SimpleNamespace(
            resolve_virtual_path=lambda t, p, **k: tmp_path / p.rsplit("/", 1)[-1]
        ),
    )
    for path in [
        "/etc/passwd",
        "https://example.com/a.png",
        "/mnt/user-data/outputs/../secret.png",
    ]:
        with pytest.raises(ValueError):
            media.load_edit_sources("t", "u", [path])
    (tmp_path / "bad.png").write_text("not an image")
    with pytest.raises(ValueError):
        media.load_edit_sources("t", "u", ["/mnt/user-data/uploads/bad.png"])
    from PIL import Image

    Image.new("RGB", (384, 384)).save(tmp_path / "ok.png")
    images, provenance = media.load_edit_sources(
        "t", "u", ["/mnt/user-data/uploads/ok.png"]
    )
    assert images[0].startswith("data:image/png;base64,")
    assert len(provenance[0]["sha256"]) == 64


def test_edit_provider_sends_source_before_instruction():
    import json

    def handle(r):
        content = json.loads(r.content)["input"]["messages"][0]["content"]
        assert content == [
            {"image": "data:image/png;base64,dGVzdA=="},
            {"text": "make blue"},
        ]
        return httpx.Response(503)

    provider = ImageProvider(
        "https://dashscope.aliyuncs.com/x",
        "qwen-image-2.0",
        "test",
        transport=httpx.MockTransport(handle),
    )
    with pytest.raises(ImageUnavailable):
        provider.generate(
            "make blue", "1024*1024", images=["data:image/png;base64,dGVzdA=="]
        )
