"""Serialize pipeline state into a human-readable text report."""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.models.schemas import ConceptSummary, ParsedPaper, ResearchNotes, ReviewVerdict


def write_summary_txt(state: dict[str, Any], output_dir: Path) -> Path:
    """Write a timestamped `.txt` summary under `output_dir` and return its path."""
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = output_dir / f"summary_{stamp}.txt"
    parsed: ParsedPaper | None = state.get("parsed")
    research: ResearchNotes | None = state.get("research")
    summary: ConceptSummary | None = state.get("summary")
    review: ReviewVerdict | None = state.get("review")
    lines = [
        "Conceptual summary",
        "==================",
        "",
        f"Source: {getattr(parsed, 'source_url', None) or 'n/a'}",
        f"Title: {getattr(parsed, 'title', None) or 'n/a'}",
        "",
        "--- Problem ---",
        (summary.problem if summary else ""),
        "",
        "--- Method ---",
        (summary.method if summary else ""),
        "",
        "--- Results ---",
        (summary.results if summary else ""),
        "",
        "--- Limitations ---",
        (summary.limitations if summary else ""),
        "",
        "--- Simplified terms ---",
    ]
    if summary and summary.simplified_terms:
        for k, v in summary.simplified_terms.items():
            lines.append(f"  {k}: {v}")
    else:
        lines.append("  (none)")
    lines.extend(
        [
            "",
            "--- Research context (ReAct) ---",
        ]
    )
    if research:
        lines.append("Key concepts: " + ", ".join(research.key_concepts[:20]))
        for b in research.web_context_bullets[:10]:
            lines.append(f"  - {b}")
        lines.append("Novelty: " + research.novelty_notes)
        lines.append("Well-known: " + research.well_known_notes)
    lines.extend(
        [
            "",
            "--- Review ---",
            f"OK: {review.ok if review else 'n/a'}",
        ]
    )
    if review and review.issues:
        for issue in review.issues:
            lines.append(f"  Issue: {issue}")
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
