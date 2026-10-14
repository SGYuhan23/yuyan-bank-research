"""Qwen image adapter. No model substitution, implicit retries, or fake output."""

import base64
import hashlib
from pathlib import PurePosixPath
import json
import os
import re
import uuid
from io import BytesIO
from urllib.parse import urlsplit
import httpx
from PIL import Image

from typing import Annotated
from langchain.tools import tool, InjectedToolCallId
from langchain_core.messages import ToolMessage
from langgraph.types import Command
from deerflow.tools.types import Runtime
from deerflow.config.paths import get_paths
from deerflow.tools.builtins.present_file_tool import _get_thread_id
from deerflow.runtime.user_context import resolve_runtime_user_id


MAX_BYTES = 20 * 1024 * 1024


class ImageUnavailable(RuntimeError):
    pass


def validate_prompt(prompt, size):
    if not prompt.strip() or len(prompt) > 4000:
        raise ValueError("图片描述必须为 1–4000 字符。")
    if not re.fullmatch(r"\d{3,4}\*\d{3,4}", size):
        raise ValueError("尺寸格式为 宽*高。")
    w, h = map(int, size.split("*"))
    if not 512**2 <= w * h <= 2048**2 or min(w, h) < 256:
        raise ValueError("图片总像素必须在 512² 到 2048² 之间。")


class ImageProvider:
    def __init__(self, endpoint, model, api_key, *, transport=None):
        self.endpoint, self.model, self.key, self.transport = (
            endpoint,
            model,
            api_key,
            transport,
        )

    def generate(self, prompt, size, *, images=None):
        validate_prompt(prompt, size)
        if not all((self.endpoint, self.model, self.key)):
            raise ImageUnavailable(
                "图片模型未配置；请配置 QWEN_IMAGE_ENDPOINT、QWEN_IMAGE_MODEL 和 QWEN_API_KEY。"
            )
        u = urlsplit(self.endpoint)
        if (
            u.scheme != "https"
            or not u.hostname
            or not (u.hostname.endswith(".aliyuncs.com"))
        ):
            raise ImageUnavailable("图片端点必须为配置的阿里云 HTTPS 地址。")
        payload = {
            "model": self.model,
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": [{"image": image} for image in (images or [])]
                        + [{"text": prompt}],
                    }
                ]
            },
            "parameters": {
                "size": size,
                "n": 1,
                "prompt_extend": False,
                "watermark": True,
            },
        }
        try:
            with httpx.Client(
                timeout=150, transport=self.transport, follow_redirects=False
            ) as c:
                r = c.post(
                    self.endpoint,
                    json=payload,
                    headers={"Authorization": "Bearer " + self.key},
                )
                if r.status_code != 200:
                    raise ImageUnavailable(
                        f"图片模型请求失败（HTTP {r.status_code}），未切换模型，未自动重试。"
                    )
                result = r.json()
                content = result["output"]["choices"][0]["message"]["content"]
                url = next(x["image"] for x in content if "image" in x)
                parsed = urlsplit(url)
                # Provider-owned download hosts only; reject redirects and credentials.
                if (
                    parsed.scheme != "https"
                    or not parsed.hostname
                    or not parsed.hostname.endswith(".aliyuncs.com")
                    or parsed.username
                    or parsed.port not in (None, 443)
                ):
                    raise ImageUnavailable("模型返回了不允许的图片下载地址。")
                with c.stream("GET", url) as download:
                    if download.status_code != 200:
                        raise ImageUnavailable("图片下载失败。")
                    data = bytearray()
                    for chunk in download.iter_bytes():
                        data.extend(chunk)
                        if len(data) > MAX_BYTES:
                            raise ImageUnavailable("图片超过 20 MB 限额。")
                with Image.open(BytesIO(data)) as im:
                    if im.format != "PNG" or im.width * im.height > 2048**2:
                        raise ImageUnavailable("图片格式或分辨率不符合约定。")
                    im.verify()
                return bytes(data), {
                    "model": self.model,
                    "request_id": result.get("request_id"),
                    "size": size,
                    "provider": "qwen",
                    "watermark": True,
                }
        except ImageUnavailable:
            raise
        except (
            httpx.HTTPError,
            ValueError,
            KeyError,
            IndexError,
            StopIteration,
            OSError,
        ) as exc:
            raise ImageUnavailable(
                "图片生成或下载未完成（"
                + type(exc).__name__
                + "）；未自动重试，请检查运行记录。"
            ) from None


@tool("generate_image", parse_docstring=True)
def generate_image(
    runtime: Runtime,
    prompt: str,
    tool_call_id: Annotated[str, InjectedToolCallId],
    size: str = "1024*1024",
) -> Command | str:
    """Generate a real PNG using the configured Qwen image model and save it to this user's current thread. Use for illustrations, posters and photos. Use code/SVG for exact charts or diagrams. Call present_files after success. Unavailable/error means no image was generated; do not pretend otherwise.

    Args:
        prompt: Detailed description of the desired image, at most 4000 characters.
        size: Pixel dimensions, width*height, defaults to 1024*1024.
    """
    tid = _get_thread_id(runtime)
    uid = resolve_runtime_user_id(runtime)
    if not tid or not uid or uid == "default":
        return json.dumps(
            {"status": "error", "message": "图片生成需要已鉴权会话。"},
            ensure_ascii=False,
        )
    try:
        provider = ImageProvider(
            os.environ.get("QWEN_IMAGE_ENDPOINT", ""),
            os.environ.get("QWEN_IMAGE_MODEL", ""),
            os.environ.get("QWEN_API_KEY", ""),
        )
        data, metadata = provider.generate(prompt, size)
        name = "image-" + uuid.uuid4().hex
        virtual = "/mnt/user-data/outputs/" + name + ".png"
        target = get_paths().resolve_virtual_path(tid, virtual, user_id=uid)
        target.parent.mkdir(parents=True, exist_ok=True)
        # Unique immutable artifacts: no overwriting an earlier image.
        with target.open("xb") as f:
            f.write(data)
        metadata.update(prompt=prompt, artifact=virtual, bytes=len(data))
        target.with_suffix(".json").write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2)
        )
        return Command(
            update={
                "artifacts": [virtual],
                "messages": [
                    ToolMessage(
                        json.dumps(
                            {"status": "success", **metadata}, ensure_ascii=False
                        ),
                        tool_call_id=tool_call_id,
                    )
                ],
            }
        )
    except (ImageUnavailable, ValueError) as exc:
        return json.dumps(
            {"status": "unavailable", "message": str(exc)}, ensure_ascii=False
        )


def load_edit_sources(tid, uid, paths):
    if not 1 <= len(paths) <= 3:
        raise ValueError("图片编辑需要 1–3 张当前会话图片。")
    images, provenance = [], []
    for virtual in paths:
        parts = PurePosixPath(virtual).parts
        if (
            not virtual.startswith(
                ("/mnt/user-data/uploads/", "/mnt/user-data/outputs/")
            )
            or ".." in parts
        ):
            raise ValueError("只允许编辑当前会话上传或生成的图片。")
        path = get_paths().resolve_virtual_path(tid, virtual, user_id=uid)
        try:
            with path.open("rb") as source:
                data = source.read(10 * 1024 * 1024 + 1)
            if len(data) > 10 * 1024 * 1024:
                raise ValueError("每张原图不得超过 10 MB。")
            with Image.open(BytesIO(data)) as im:
                if (
                    im.format not in {"PNG", "JPEG", "WEBP", "BMP", "TIFF", "GIF"}
                    or im.width * im.height > 3072**2
                ):
                    raise ValueError("原图格式或尺寸不受支持。")
                mime = Image.MIME[im.format]
                im.verify()
        except (OSError, Image.DecompressionBombError):
            raise ValueError("原图不存在或不是可读取的图片。") from None
        images.append(
            "data:" + mime + ";base64," + base64.b64encode(data).decode("ascii")
        )
        provenance.append(
            {"artifact": virtual, "sha256": hashlib.sha256(data).hexdigest()}
        )
    return images, provenance


@tool("edit_image", parse_docstring=True)
def edit_image(
    runtime: Runtime,
    prompt: str,
    source_paths: list[str],
    tool_call_id: Annotated[str, InjectedToolCallId],
    size: str = "1024*1024",
) -> Command | str:
    """Edit existing images with the configured real Qwen image model. Save a new PNG, preserving originals. Use only images uploaded or generated in the current conversation. Never claim an edit succeeded on error.

    Args:
        prompt: Precise edit instruction including what should remain unchanged.
        source_paths: One to three current-thread virtual image paths under /mnt/user-data/uploads/ or /mnt/user-data/outputs/.
        size: Output width*height, defaults to 1024*1024.
    """
    tid, uid = _get_thread_id(runtime), resolve_runtime_user_id(runtime)
    if not tid or not uid or uid == "default":
        return json.dumps(
            {"status": "error", "message": "图片编辑需要已鉴权会话。"},
            ensure_ascii=False,
        )
    try:
        images, parents = load_edit_sources(tid, uid, source_paths)
        provider = ImageProvider(
            os.environ.get("QWEN_IMAGE_ENDPOINT", ""),
            os.environ.get("QWEN_IMAGE_MODEL", ""),
            os.environ.get("QWEN_API_KEY", ""),
        )
        data, metadata = provider.generate(prompt, size, images=images)
        virtual = "/mnt/user-data/outputs/edit-" + uuid.uuid4().hex + ".png"
        target = get_paths().resolve_virtual_path(tid, virtual, user_id=uid)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as output:
            output.write(data)
        metadata.update(
            operation="edit",
            prompt=prompt,
            parents=parents,
            artifact=virtual,
            bytes=len(data),
        )
        target.with_suffix(".json").write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return Command(
            update={
                "artifacts": [virtual],
                "messages": [
                    ToolMessage(
                        json.dumps(
                            {"status": "success", **metadata}, ensure_ascii=False
                        ),
                        tool_call_id=tool_call_id,
                    )
                ],
            }
        )
    except (ImageUnavailable, ValueError, OSError) as exc:
        message = (
            str(exc)
            if isinstance(exc, (ImageUnavailable, ValueError))
            else "图片文件读写失败。"
        )
        return json.dumps(
            {"status": "unavailable", "message": message}, ensure_ascii=False
        )
