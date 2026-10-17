import unittest, tempfile, json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engine import ResearchRun, ResearchError, SOURCES, ROOT


class Integrity(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.run = ResearchRun("test", "rifa", run_dir=self.tmp.name)

    def test_unread_quote_rejected(self):
        d = json.loads((ROOT / "runs/rifa-initial/run.json").read_text())["result"][
            "dossier"
        ]
        with self.assertRaises(ResearchError):
            self.run.validate(d)

    def test_fabricated_project_rejected(self):
        d = json.loads((ROOT / "runs/rifa-initial/run.json").read_text())["result"][
            "dossier"
        ]
        self.run.read_source("rifa-accepted")
        d["events"][0]["project_id"] = "invented-project"
        with self.assertRaisesRegex(ResearchError, "项目代码"):
            self.run.validate(d)

    def test_calculation_requires_evidence(self):
        with self.assertRaises(ResearchError):
            self.run.calculate(
                "ratio_percent", "30", "553", "万元", "计划", ["rifa-proposed"]
            )
        self.run.read_source("rifa-proposed")
        self.assertEqual(
            self.run.calculate(
                "ratio_percent", "30", "553", "万元", "计划", ["rifa-proposed"]
            )["result"],
            "5.42",
        )
        with self.assertRaises(ResearchError):
            self.run.calculate(
                "ratio_percent", "999999", "553", "万元", "计划", ["rifa-proposed"]
            )

    def test_unknown_source_cannot_fetch(self):
        with self.assertRaises(ResearchError):
            self.run.read_source("http://127.0.0.1/secret")

    def test_forged_financial_number_rejected(self):
        self.run.read_source("rifa-accepted")
        d = json.loads((ROOT / "runs/rifa-initial/run.json").read_text())["result"][
            "dossier"
        ]
        d["events"][0]["project_id"] = None
        d["facts"][0]["statement"] = "公司融资缺口9988776655元"
        with self.assertRaisesRegex(ResearchError, "数字"):
            self.run.validate(d)

    def test_reference_not_model_input(self):
        source = (ROOT / "engine.py").read_text()
        self.assertNotIn("reference-facts.json", source)
        self.assertNotIn("manual-rifa", source)

    def test_sources_reprint_same_canonical(self):
        s = next(s for s in SOURCES if s["source_id"] == "loncin-reprint")
        self.assertEqual(s["canonical_source_id"], "loncin-2025")
        self.assertEqual(s["kind"], "reprint")

    def test_missing_model_is_failure_not_replay(self):
        import os
        from unittest.mock import patch

        with patch.dict(os.environ, {"QWEN_API_KEY": ""}):
            with self.assertRaisesRegex(ResearchError, "MODEL_UNAVAILABLE"):
                self.run.model([], "test")
        self.assertIsNone(self.run.result)


if __name__ == "__main__":
    unittest.main()


class UpdateAndDedupe(unittest.TestCase):
    def test_reprint_does_not_create_new_event(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = ResearchRun("test", "loncin", run_dir=tmp)
            r.read_source("loncin-2025")
            r.read_source("loncin-reprint")
            d = {
                "company_id": "loncin",
                "what_changed": "test",
                "why_relevant": "test",
                "facts": [],
                "events": [
                    {
                        "event_id": "original",
                        "source_ids": ["loncin-2025"],
                        "supersedes": [],
                    },
                    {
                        "event_id": "copy",
                        "source_ids": ["loncin-reprint"],
                        "supersedes": [],
                    },
                ],
                "hypotheses": [],
                "missing_information": [],
                "next_questions": [],
                "coverage_limit": "test",
                "stop_reason": "test",
            }
            r.finish(d)
            self.assertEqual(len(r.result["dossier"]["events"]), 1)
            self.assertEqual(len(r.result["dossier"]["events"][0]["source_ids"]), 2)

    def test_update_invalidates_prior_review_and_lists_withdrawal(self):
        old = {
            "company_id": "rifa",
            "what_changed": "test",
            "why_relevant": "test",
            "facts": [],
            "events": [],
            "hypotheses": [
                {
                    "hypothesis_id": "h1",
                    "title": "test",
                    "status": "needs_review",
                    "reasoning_summary": "test",
                    "supporting_evidence": [],
                    "counter_evidence": [],
                    "missing_information": [],
                }
            ],
            "missing_information": [],
            "next_questions": [],
            "coverage_limit": "test",
            "stop_reason": "test",
        }
        with tempfile.TemporaryDirectory() as tmp:
            r = ResearchRun(
                "test",
                "rifa",
                parent={"run_id": "parent", "result": {"dossier": old}},
                run_dir=tmp,
            )
            new = json.loads(json.dumps(old))
            new["hypotheses"][0]["status"] = "withdrawn"
            r.finish(new)
            self.assertEqual(r.result["delta"]["withdrawn_hypotheses"], ["h1"])
            self.assertTrue(r.result["delta"]["review_invalidated"])
            self.assertEqual(old["hypotheses"][0]["status"], "needs_review")


class GuardRules(unittest.TestCase):
    def test_finance_assertion_withdrawn_without_fabricated_model_trace(self):
        old = {
            "company_id": "rifa",
            "what_changed": "test",
            "why_relevant": "test",
            "facts": [],
            "events": [],
            "hypotheses": [
                {
                    "hypothesis_id": "h",
                    "title": "存在融资需求",
                    "status": "needs_review",
                    "reasoning_summary": "环评获批，建设启动在即",
                    "supporting_evidence": [],
                    "counter_evidence": [],
                    "missing_information": [],
                }
            ],
            "missing_information": [],
            "next_questions": [],
            "coverage_limit": "test",
            "stop_reason": "test",
        }
        with tempfile.TemporaryDirectory() as tmp:
            r = ResearchRun(
                "test",
                "rifa",
                parent={"run_id": "p", "result": {"dossier": old}},
                run_dir=tmp,
            )
            r.finish(json.loads(json.dumps(old)))
            self.assertEqual(
                r.result["dossier"]["hypotheses"][0]["status"], "withdrawn"
            )
            self.assertFalse(any(x["kind"] == "model_call" for x in r.records))
            self.assertTrue(
                any(x["kind"] == "hypothesis_assertion_guard" for x in r.records)
            )
