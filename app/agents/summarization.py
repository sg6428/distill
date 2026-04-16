"""Turn parsed paper + research notes into a structured conceptual summary."""

from typing import Any

from app.agents.base import Agent
from app.models.schemas import ConceptSummary, ParsedPaper, ResearchNotes


class SummarizationAgent(Agent):
    """Produces `ConceptSummary` (replace stub with real LLM calls as needed)."""

    name = "summarization"

    async def run(self, state: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        """Write `state['summary']`, optionally incorporating `revision_notes`."""
        parsed: ParsedPaper = state["parsed"]
        research = state.get("research") or ResearchNotes()
        summary = self._abstractive_stub(parsed, research, revision_notes=kwargs.get("revision_notes"))
        state["summary"] = summary
        return state

    def _abstractive_stub(
        self,
        paper: ParsedPaper,
        research: ResearchNotes,
        revision_notes: str | None,
    ) -> ConceptSummary:
        """Placeholder abstractive summary using abstract snippet and reviewer hints."""
        _ = research  # reserved for LLM grounding with research notes
        abstract = ""
        for s in paper.sections:
            if str(s.get("name", "")).lower().startswith("abstract"):
                abstract = str(s.get("body", ""))[:2000]
                break
        if not abstract:
            abstract = paper.raw_text[:2000]
        fix = f"\nReviewer: {revision_notes}" if revision_notes else ""
        snippet = (abstract[:500] + "…") if len(abstract) > 500 else abstract
        return ConceptSummary(
            problem=f"Conceptual problem (LLM hook): {snippet}{fix}",
            method="Method overview (LLM hook): tie to Methods/Approach sections.",
            results="Results (LLM hook): key metrics and claims from experiments.",
            limitations="Limitations (LLM hook): failure modes and future work.",
            simplified_terms={
                "LLM": "large language model — a model trained to predict text",
                "abstractive": "paraphrasing in new words, not copy-paste",
            },
        )
