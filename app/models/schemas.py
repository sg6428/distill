"""Pydantic models shared across agents, the API, and file output."""

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class FigureRef(BaseModel):
    """Lightweight pointer to a figure or table mention in the PDF text."""

    page: int | None = None
    label: str | None = None
    caption_hint: str | None = None


class ParsedPaper(BaseModel):
    """Normalized paper content after ingestion (text, sections, figure hints)."""

    title: str | None = None
    raw_text: str = ""
    sections: list[dict[str, Any]] = Field(default_factory=list)
    figures: list[FigureRef] = Field(default_factory=list)
    source_url: str | None = None


class ResearchNotes(BaseModel):
    """External context and reasoning hooks from the research agent."""

    key_concepts: list[str] = Field(default_factory=list)
    web_context_bullets: list[str] = Field(default_factory=list)
    novelty_notes: str = ""
    well_known_notes: str = ""


class ConceptSummary(BaseModel):
    """Structured conceptual summary plus jargon simplifications."""

    problem: str = ""
    method: str = ""
    results: str = ""
    limitations: str = ""
    simplified_terms: dict[str, str] = Field(default_factory=dict)


class ReviewVerdict(BaseModel):
    """Reflection agent output: pass/fail, issues, and guidance for revision."""

    ok: bool = False
    issues: list[str] = Field(default_factory=list)
    suggested_fixes: str = ""


class PipelineState(BaseModel):
    """Typed view of everything produced along the pipeline (optional helper)."""

    parsed: ParsedPaper | None = None
    research: ResearchNotes | None = None
    summary: ConceptSummary | None = None
    review: ReviewVerdict | None = None
    output_path: Path | None = None


class SummarizeRequest(BaseModel):
    """HTTP body for `POST /summarize`: supply a URL and/or local PDF path string."""

    paper_url: str | None = None
    pdf_path: str | None = None
