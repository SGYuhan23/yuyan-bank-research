"""Reproducible source acquisition. No model, conclusions or private credentials."""

import json, hashlib, urllib.request, re
from pathlib import Path
from datetime import datetime, timezone
from html.parser import HTMLParser
from pypdf import PdfReader

ROOT = Path(__file__).parent


class Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.skip = 0

    def handle_starttag(self, t, a):
        if t in ("script", "style"):
            self.skip += 1

    def handle_endtag(self, t):
        if t in ("script", "style"):
            self.skip = max(0, self.skip - 1)

    def handle_data(self, s):
        if not self.skip:
            self.parts.append(s)


def html_text(raw):
    for encoding in ("utf-8", "gb18030"):
        try:
            s = raw.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        s = raw.decode("utf-8", "replace")
    p = Text()
    p.feed(s)
    return " ".join(" ".join(p.parts).split())


def section(text, start, end=None, size=900):
    a = text.index(start)
    b = text.find(end, a + len(start)) if end else -1
    return text[a : b if b >= 0 else a + size].strip()


def build():
    raw = ROOT / "data/raw"
    raw.mkdir(parents=True, exist_ok=True)
    defs = [
        (
            "rifa-accepted",
            "https://gxq.cq.gov.cn/hbslgg/202608/t20260811_15920200.html",
            "环评受理公告（2026年第25号）",
            "高新区生态环境局",
            "2026-08-11",
            "2026-08-11",
            ["rifa", "zishuo"],
            "primary",
        ),
        (
            "rifa-proposed",
            "https://gxq.cq.gov.cn/hbslgg/202608/t20260818_15948374.html",
            "拟审批环评公告（2026年第25号）",
            "高新区生态环境局",
            "2026-08-18",
            "2026-08-18",
            ["rifa", "zishuo"],
            "primary",
        ),
        (
            "rifa-approved",
            "https://gxq.cq.gov.cn/hbslgg/202608/t20260826_15983453.html",
            "环评审批决定公告（2026年第25号）",
            "高新区生态环境局",
            "2026-08-26",
            "2026-08-25",
            ["rifa", "zishuo"],
            "primary",
        ),
        (
            "qinan-2025",
            "https://static.cninfo.com.cn/finalpage/2026-03-28/1225047393.PDF",
            "秦安股份2025年年度报告",
            "重庆秦安机电股份有限公司／巨潮资讯",
            "2026-03-28",
            "2025年度",
            ["qinan", "qinan-cast"],
            "primary",
        ),
        (
            "loncin-2025",
            "https://static.cninfo.com.cn/finalpage/2026-04-18/1225117448.PDF",
            "隆鑫通用2025年年度报告",
            "隆鑫通用动力股份有限公司／巨潮资讯",
            "2026-04-18",
            "2025年度",
            ["loncin"],
            "primary",
        ),
        (
            "smart-factory",
            "https://jjxxw.cq.gov.cn/zwgk_213/zcwj/qtwj/202507/t20250707_14792936.html",
            "2025年重庆市基础级智能工厂名单",
            "重庆市经济和信息化委员会",
            "2025-07-07",
            "2025年名单",
            ["qinan-cast"],
            "primary",
        ),
        (
            "loncin-reprint",
            "https://money.finance.sina.com.cn/corp/view/vCB_AllBulletinDetail.php?id=12107316",
            "隆鑫通用2025年年度报告（转载）",
            "新浪财经",
            "2026-04-18",
            "2025年度",
            ["loncin"],
            "reprint",
        ),
        (
            "loncin-news",
            "https://stock.stockstar.com/notice/IG2026041700041091.shtml",
            "隆鑫通用发布2025年度业绩（转述）",
            "证券之星／智通财经",
            "2026-04-17",
            "2025年度",
            ["loncin"],
            "reprint",
        ),
        (
            "qinan-cash-appendix",
            "https://static.cninfo.com.cn/finalpage/2026-03-28/1225047393.PDF",
            "秦安2025年报补充读取：现金及并购支出附注",
            "重庆秦安机电股份有限公司／巨潮资讯",
            "2026-03-28",
            "2025年度",
            ["qinan"],
            "primary",
        ),
        (
            "loncin-reprint-pdf",
            "https://stockmc.xueqiu.com/202604/603766_20260418_11NK.pdf",
            "隆鑫2025年报转载PDF",
            "雪球",
            "2026-04-18",
            "2025年度",
            ["loncin"],
            "reprint",
        ),
        (
            "qinan-2026h1",
            "https://static.cninfo.com.cn/finalpage/2026-08-22/1225493283.PDF",
            "秦安股份2026年半年度报告摘要",
            "重庆秦安机电股份有限公司／巨潮资讯",
            "2026-08-22",
            "2026年1-6月",
            ["qinan"],
            "primary",
        ),
    ]
    out = []
    for sid, url, title, pub, date, period, companies, kind in defs:
        f = raw / (sid + (".pdf" if url.lower().endswith(".pdf") else ".html"))
        if not f.exists():
            try:
                f.write_bytes(urllib.request.urlopen(url, timeout=30).read())
            except Exception as exc:
                failures = ROOT / "data/acquisition-failures.jsonl"
                with failures.open("a") as log:
                    log.write(
                        json.dumps(
                            {
                                "source_id": sid,
                                "url": url,
                                "at": datetime.now(timezone.utc).isoformat(),
                                "error": str(exc),
                            },
                            ensure_ascii=False,
                        )
                        + "\n"
                    )
                print("FETCH_FAILED", sid, type(exc).__name__)
                continue
        b = f.read_bytes()
        sections = []
        if f.suffix == ".pdf":
            pages = PdfReader(f).pages
            if sid == "qinan-2025":
                picks = [
                    (6, "七、", "(二)"),
                    (30, "截至 2025 年底", "(一)"),
                    (227, "十、", "重庆美沣"),
                ]
            elif sid == "qinan-cash-appendix":
                picks = [(220, "", None)]
            elif sid in ("loncin-2025", "loncin-reprint-pdf"):
                picks = [(7, "七、", "(二)"), (11, "4、销售模式", "报告期内公司新增")]
            else:
                picks = [
                    (i + 1, "2.2", None)
                    for i, p in enumerate(pages)
                    if "2.2" in p.extract_text()
                ]
            for page, start, end in picks:
                txt = section(pages[page - 1].extract_text(), start, end, 1800)
                sections.append(
                    {
                        "page_or_section": f"PDF第{page}页",
                        "text": txt,
                        "selector": {
                            "page": page,
                            "start": start,
                            "end": end,
                            "size": 1800,
                        },
                    }
                )
        else:
            txt = html_text(b)
            if sid.startswith("rifa"):
                # Keep table context and all rows to test company/project disambiguation.
                start = "序号"
                end = "附件：" if sid != "rifa-proposed" else "附件下载："
                sections = [
                    {
                        "page_or_section": "公告项目表（含建设单位列）",
                        "text": section(txt, start, end, 6500),
                        "selector": {"start": start, "end": end, "size": 6500},
                    }
                ]
            elif sid == "smart-factory":
                for start, end in [("209 重庆秦安", "210 "), ("222 重庆秦安", "223 ")]:
                    sections.append(
                        {
                            "page_or_section": "附件名单第" + start[:3] + "行",
                            "text": section(txt, start, end),
                            "selector": {"start": start, "end": end},
                        }
                    )
            elif sid == "loncin-reprint":
                sections = [
                    {
                        "page_or_section": "近三年主要会计数据／营业收入行",
                        "text": section(txt, "营业收入 19,135", "利润总额", 300),
                        "selector": {
                            "start": "营业收入 19,135",
                            "end": "利润总额",
                            "size": 300,
                        },
                    }
                ]
            else:
                sections = [
                    {
                        "page_or_section": "业绩新闻正文首段",
                        "text": section(
                            txt, "智通财经APP讯", "报告期内，公司摩托车", 500
                        ),
                        "selector": {
                            "start": "智通财经APP讯",
                            "end": "报告期内，公司摩托车",
                            "size": 500,
                        },
                    }
                ]
        out.append(
            dict(
                source_id=sid,
                url=url,
                title=title,
                publisher=pub,
                published_at=date,
                period=period,
                retrieved_at=datetime.fromtimestamp(
                    f.stat().st_mtime, timezone.utc
                ).isoformat(),
                company_ids=companies,
                kind=kind,
                canonical_source_id="loncin-2025"
                if kind == "reprint"
                else ("qinan-2025" if sid == "qinan-cash-appendix" else sid),
                sha256=hashlib.sha256(b).hexdigest(),
                sections=sections,
            )
        )
    (ROOT / "data/sources.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2)
    )
    print("Prepared", len(out), "sources")


if __name__ == "__main__":
    build()
