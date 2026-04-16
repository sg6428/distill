"""Runs agents in order and persists the final summary to disk."""

from typing import Any

from app.agents.ingestion import IngestionAgent
from app.agents.react_research import ReActResearchAgent
from app.agents.reflection import ReflectionAgent
from app.agents.summarization import SummarizationAgent
from app.config import settings
from app.services.output import write_summary_txt


class Orchestrator:
    """Coordinates ingestion → research → summarize ↔ reflect → file output."""

    def __init__(self) -> None:
        """Wire default agent instances used by `run`."""
        self.ingestion = IngestionAgent()
        self.research = ReActResearchAgent()
        self.summarizer = SummarizationAgent()
        self.reflection = ReflectionAgent()

    async def run(self, paper_url: str | None, pdf_path: str | None) -> dict[str, Any]:
        """Execute the pipeline end-to-end; final state includes `output_path`."""
        state: dict[str, Any] = {
            "paper_url": paper_url,
            "pdf_path": pdf_path,
            "revision_round": 0,
        }
        state = await self.ingestion.run(state)
        state = await self.research.run(state)
        while True:
            revision = state.get("revision_notes") if state.get("revision_round") else None
            state = await self.summarizer.run(state, revision_notes=revision)
            state = await self.reflection.run(state)
            if not state.get("needs_revision"):
                break
        path = write_summary_txt(state, settings.output_dir)
        state["output_path"] = path
        return state
