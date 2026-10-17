from typing import Literal
from pydantic import BaseModel, Field, ConfigDict


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Company(Strict):
    company_id: str
    legal_name: str
    aliases: list[str] = []
    parent_relationship: dict | None = None
    region: str | None = None
    industry: str | None = None
    sources: list[str] = []


class Evidence(Strict):
    source_id: str
    url: str
    title: str
    publisher: str
    published_at: str | None
    retrieved_at: str
    excerpt: str
    page_or_section: str
    period: str | None = None
    sha256: str


class Fact(Strict):
    fact_id: str
    company_id: str
    statement: str
    source_id: str
    excerpt: str
    page_or_section: str
    period: str
    scope: Literal["project", "company", "consolidated", "subsidiary", "unknown"]
    limitations: str


class Event(Strict):
    event_id: str
    company_id: str
    project_id: str | None = None
    event_type: str
    event_date: str | None = None
    published_at: str
    stage: Literal[
        "accepted",
        "proposed",
        "approved",
        "construction",
        "completed",
        "disclosed",
        "unknown",
    ]
    source_ids: list[str]
    supersedes: list[str] = []
    conflicts: list[str] = []


class ServiceHypothesis(Strict):
    hypothesis_id: str
    title: str
    supporting_evidence: list[str]
    counter_evidence: list[str] = []
    reasoning_summary: str
    missing_information: list[str]
    questions_to_verify: list[str]
    status: Literal["proposed", "insufficient", "withdrawn", "needs_review"]


class Review(Strict):
    review_id: str
    run_id: str
    hypothesis_id: str
    evidence_version: str
    action: Literal["confirm", "modify", "withdraw"]
    before: dict
    after: dict
    note: str
    reviewer: str
    created_at: str


class Dossier(Strict):
    company_id: str
    what_changed: str
    why_relevant: str
    facts: list[Fact]
    events: list[Event]
    hypotheses: list[ServiceHypothesis]
    calculation_ids: list[str] = []
    missing_information: list[str]
    next_questions: list[str]
    stop_reason: str
    coverage_limit: str
