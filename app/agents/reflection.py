"""Review summarization output and decide whether another revision pass is needed."""

from typing import Any

from app.agents.base import Agent
from app.config import settings
from app.models.schemas import ConceptSummary, ReviewVerdict


class ReflectionAgent(Agent):
    """Sets `state['review']` and `needs_revision` / `revision_notes` for the loop."""

    name = "reflection"

    async def run(self, state: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        """Critique the current summary and bump revision counters when appropriate."""
        summary: ConceptSummary = state["summary"]
        review = self._critique_stub(summary)
        state["review"] = review
        round_idx = state.get("revision_round", 0)
        if not review.ok and round_idx < settings.max_revision_rounds:
            state["revision_round"] = round_idx + 1
            state["needs_revision"] = True
            state["revision_notes"] = review.suggested_fixes
        else:
            state["needs_revision"] = False
        return state

    def _critique_stub(self, summary: ConceptSummary) -> ReviewVerdict:
        """Minimal quality gate: non-empty required sections pass."""
        issues: list[str] = []
        for name, field in (
            ("problem", summary.problem),
            ("method", summary.method),
            ("results", summary.results),
            ("limitations", summary.limitations),
        ):
            if not (field or "").strip():
                issues.append(f"Empty {name}.")
        ok = len(issues) == 0
        return ReviewVerdict(
            ok=ok,
            issues=issues,
            suggested_fixes="Regenerate sections with tighter grounding to extracted text.",
        )
