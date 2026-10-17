"""Local-only single-process server. No public deployment/authentication claim."""

import json, uuid, threading, re, io, hashlib
from pathlib import Path
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
import httpx
from pypdf import PdfReader
import engine
from engine import ROOT, ResearchRun, atomic, now, digest
from models import Review
from prepare_sources import html_text

LOCK = threading.RLock()
RUNS = ROOT / "local/runs"
RUNS.mkdir(parents=True, exist_ok=True)
BUSY = threading.Semaphore(1)


def load_run(rid):
    if not re.fullmatch(r"[a-zA-Z0-9_-]{1,80}", rid):
        raise ValueError("INVALID_RUN_ID")
    p = RUNS / rid / "run.json"
    if not p.exists():
        p = ROOT / "runs" / rid / "run.json"
    return json.loads(p.read_text()), p


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def send(self, data, status=200, ctype="application/json; charset=utf-8"):
        raw = (
            data
            if isinstance(data, bytes)
            else json.dumps(data, ensure_ascii=False).encode()
        )
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        try:
            if self.path == "/api/catalog":
                return self.send(
                    {
                        "companies": engine.COMPANIES,
                        "sources": [
                            {
                                k: s[k]
                                for k in (
                                    "source_id",
                                    "title",
                                    "url",
                                    "published_at",
                                    "company_ids",
                                )
                            }
                            for s in engine.SOURCES
                        ],
                        "mode": "local_live_model",
                        "model_configured": bool(engine.os.getenv("QWEN_API_KEY")),
                    }
                )
            if self.path == "/api/runs":
                result = []
                for base in (ROOT / "runs", RUNS):
                    for p in base.glob("*/run.json"):
                        d = json.loads(p.read_text())
                        result.append(
                            {
                                "id": p.parent.name,
                                "run_id": d["run_id"],
                                "company_id": d["company_id"],
                                "status": d["status"],
                                "started_at": d["started_at"],
                                "mode": d["mode"],
                            }
                        )
                return self.send(result)
            if self.path.startswith("/api/runs/"):
                rid = self.path.split("/")[3]
                d, p = load_run(rid)
                if self.path.endswith("/export"):
                    if not d.get("result"):
                        return self.send({"error": "档案尚未完成"}, 409)
                    text = (
                        (p.parent / "dossier.md").read_text()
                        if (p.parent / "dossier.md").exists()
                        else json.dumps(d["result"], ensure_ascii=False, indent=2)
                    )
                    reviews = ROOT / "local/reviews" / f"{d['run_id']}.json"
                    text += "\n\n## 人工复核记录（不修改原运行）\n" + (
                        reviews.read_text() if reviews.exists() else "尚无人工复核"
                    )
                    return self.send(
                        text.encode(), ctype="text/markdown; charset=utf-8"
                    )
                reviewfile = ROOT / "local/reviews" / f"{d['run_id']}.json"
                d["reviews"] = (
                    json.loads(reviewfile.read_text()) if reviewfile.exists() else []
                )
                return self.send(d)
            files = {"/": "index.html", "/app.js": "app.js", "/style.css": "style.css"}
            if self.path not in files:
                return self.send({"error": "NOT_FOUND"}, 404)
            p = ROOT / "web" / files[self.path]
            return self.send(
                p.read_bytes(),
                ctype={
                    "html": "text/html; charset=utf-8",
                    "js": "text/javascript; charset=utf-8",
                    "css": "text/css; charset=utf-8",
                }[p.suffix[1:]],
            )
        except (ValueError, FileNotFoundError, KeyError):
            self.send({"error": "NOT_FOUND"}, 404)

    def do_POST(self):
        # Prevent cross-origin websites from spending local model quota or writing reviews.
        origin = self.headers.get("Origin")
        if origin and origin != f"http://{self.headers.get('Host')}":
            return self.send({"error": "ORIGIN_REJECTED"}, 403)
        if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
            return self.send({"error": "JSON_REQUIRED"}, 415)
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length < 200_000:
                raise ValueError("INVALID_SIZE")
            body = json.loads(self.rfile.read(length))
            if self.path == "/api/runs":
                cid = body["company_id"]
                task = body["task"]
                if not isinstance(task, str) or not 1 <= len(task) <= 2000:
                    raise ValueError("INVALID_TASK")
                if cid not in [c["company_id"] for c in engine.COMPANIES]:
                    raise ValueError("未知主体，请先导入具有明确主体的来源")
                ids = body.get("source_ids")
                if ids is not None and (
                    not isinstance(ids, list)
                    or any(
                        x not in [s["source_id"] for s in engine.SOURCES] for x in ids
                    )
                ):
                    raise ValueError("INVALID_SOURCES")
                mode = body.get("mode", "snapshot")
                if mode not in ("snapshot", "live"):
                    raise ValueError("INVALID_MODE")
                parent = load_run(body["parent"])[0] if body.get("parent") else None
                if parent and (not parent.get("result") or parent["company_id"] != cid):
                    raise ValueError("INVALID_PARENT")
                if not BUSY.acquire(blocking=False):
                    return self.send({"error": "已有研究执行中"}, 409)
                try:
                    run = ResearchRun(task, cid, ids, mode, parent)
                except Exception:
                    BUSY.release()
                    raise

                def work():
                    try:
                        run.run_update() if parent else run.run()
                    except Exception:
                        pass
                    finally:
                        BUSY.release()

                threading.Thread(target=work, daemon=True).start()
                return self.send({"id": run.id}, 202)
            if self.path == "/api/reviews":
                d, p = load_run(body["run_id"])
                if body["evidence_version"] != d["result"]["evidence_version"]:
                    raise ValueError("STALE_EVIDENCE_VERSION")
                h = next(
                    h
                    for h in d["result"]["dossier"]["hypotheses"]
                    if h["hypothesis_id"] == body["hypothesis_id"]
                )
                if body["action"] == "confirm" and h["status"] in (
                    "withdrawn",
                    "insufficient",
                ):
                    raise ValueError("撤回或不足的假设不能直接确认；需补充证据后研究")
                if (
                    not body.get("note", "").strip()
                    or not body.get("reviewer", "").strip()
                ):
                    raise ValueError("请填写复核人及依据")
                if body["action"] == "modify" and not body.get("text", "").strip():
                    raise ValueError("修改内容不能为空")
                after = {
                    **h,
                    "review_status": body["action"],
                    "review_text": body.get("text", h["reasoning_summary"]),
                }
                review = Review(
                    review_id=uuid.uuid4().hex,
                    run_id=d["run_id"],
                    hypothesis_id=h["hypothesis_id"],
                    evidence_version=body["evidence_version"],
                    action=body["action"],
                    before=h,
                    after=after,
                    note=body["note"],
                    reviewer=body["reviewer"],
                    created_at=now(),
                ).model_dump()
                with LOCK:
                    path = ROOT / "local/reviews" / f"{d['run_id']}.json"
                    items = json.loads(path.read_text()) if path.exists() else []
                    items.append(review)
                    atomic(path, items)
                return self.send(review)
            if self.path == "/api/sources":
                url = body["url"]
                u = urlparse(url)
                host = u.hostname or ""
                if (
                    u.scheme != "https"
                    or u.username
                    or u.password
                    or u.port not in (None, 443)
                    or not (
                        host.endswith(".cq.gov.cn")
                        or host == "cq.gov.cn"
                        or host in ("static.cninfo.com.cn", "www.sse.com.cn")
                    )
                ):
                    raise ValueError(
                        "仅接受重庆政府、巨潮静态文件或上交所HTTPS原始链接；不跟随重定向"
                    )
                if body["company_id"] not in [
                    c["company_id"] for c in engine.COMPANIES
                ]:
                    raise ValueError("INVALID_COMPANY")
                from datetime import date

                date.fromisoformat(body["published_at"])
                if not body["title"].strip() or not body["publisher"].strip():
                    raise ValueError("需填写标题和发布机构")
                with httpx.stream("GET", url, timeout=25, follow_redirects=False) as r:
                    r.raise_for_status()
                    data = bytearray()
                    for chunk in r.iter_bytes():
                        data.extend(chunk)
                        if len(data) > 12_000_000:
                            raise ValueError("SOURCE_TOO_LARGE")
                raw = bytes(data)
                if raw.startswith(b"%PDF"):
                    reader = PdfReader(io.BytesIO(raw))
                    pages = body.get("pages", [1])
                    if len(pages) > 6 or any(
                        type(p) != int or p < 1 or p > len(reader.pages) for p in pages
                    ):
                        raise ValueError("最多选择6个有效PDF页码")
                    sections = [
                        {
                            "page_or_section": f"PDF第{p}页",
                            "text": reader.pages[p - 1].extract_text()[:9000],
                            "selector": {
                                "page": p,
                                "start": "",
                                "end": None,
                                "size": 9000,
                            },
                        }
                        for p in pages
                    ]
                else:
                    sections = [
                        {
                            "page_or_section": "网页正文前12000字符（请核对截断）",
                            "text": html_text(raw)[:12000],
                            "selector": {"start": "", "end": None, "size": 12000},
                        }
                    ]
                sid = "import-" + hashlib.sha256(raw).hexdigest()[:12]
                s = dict(
                    source_id=sid,
                    url=url,
                    title=body["title"],
                    publisher=body["publisher"],
                    published_at=body["published_at"],
                    period=body.get("period", "待核实"),
                    retrieved_at=now(),
                    company_ids=[body["company_id"]],
                    kind="primary",
                    canonical_source_id=sid,
                    sha256=hashlib.sha256(raw).hexdigest(),
                    sections=sections,
                    metadata_review="user_supplied_pending_verification",
                )
                with LOCK:
                    engine.SOURCES[:] = [
                        x for x in engine.SOURCES if x["source_id"] != sid
                    ] + [s]
                    atomic(
                        ROOT / "local/imported-sources.json",
                        [
                            x
                            for x in engine.SOURCES
                            if x["source_id"].startswith("import-")
                        ],
                    )
                return self.send(s, 201)
            self.send({"error": "NOT_FOUND"}, 404)
        except (
            ValueError,
            KeyError,
            StopIteration,
            TypeError,
            FileNotFoundError,
            httpx.HTTPError,
        ) as e:
            self.send({"error": str(e)[:600]}, 400)


def main():
    import argparse
    from dotenv import load_dotenv

    p = argparse.ArgumentParser()
    p.add_argument("--env")
    p.add_argument("--port", type=int, default=8765)
    a = p.parse_args()
    if a.env:
        load_dotenv(a.env)
    imported = ROOT / "local/imported-sources.json"
    if imported.exists():
        engine.SOURCES.extend(json.loads(imported.read_text()))
    print(f"渝研本地研究 http://127.0.0.1:{a.port}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", a.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
