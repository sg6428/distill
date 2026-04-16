"""ReAct-style research: propose concepts, query the web, collect contextual notes."""

import re
from typing import Any

import httpx

from app.agents.base import Agent
from app.config import settings
from app.models.schemas import ParsedPaper, ResearchNotes


class ReActResearchAgent(Agent):
    """Builds `ResearchNotes` from parsed text plus lightweight web observations."""

    name = "react_research"

    async def run(self, state: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        """Attach `state['research']` using the parsed paper body."""
        parsed: ParsedPaper = state["parsed"]
        notes = await self._react_loop(parsed)
        state["research"] = notes
        return state

    async def _react_loop(self, paper: ParsedPaper) -> ResearchNotes:
        """Iterate thought/action/search steps capped by `max_react_steps`."""
        concepts = self._seed_concepts(paper.raw_text)
        queue = list(concepts)
        bullets: list[str] = []
        novelty = ""
        known = ""
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            for step in range(settings.max_react_steps):
                if not queue:
                    break
                q = queue.pop(0)
                obs = await self._search_snippet(client, q)
                bullets.append(f"{q}: {obs[:400]}")
                if step == 0:
                    novelty = "Contrast claims in abstract vs. retrieved snippets (LLM hook)."
                    known = "Mark concepts that appear in generic tutorials (LLM hook)."
        return ResearchNotes(
            key_concepts=concepts,
            web_context_bullets=bullets,
            novelty_notes=novelty,
            well_known_notes=known,
        )

    def _seed_concepts(self, text: str, max_terms: int = 12) -> list[str]:
        """Heuristically pick capitalized phrases from an early text window."""
        candidates = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2}\b", text[:8000])
        seen: set[str] = set()
        out: list[str] = []
        for c in candidates:
            if c not in seen and len(c) > 3:
                seen.add(c)
                out.append(c)
            if len(out) >= max_terms:
                break
        if not out:
            out = ["machine learning", "evaluation"]
        return out

    async def _search_snippet(self, client: httpx.AsyncClient, query: str) -> str:
        """Fetch a compact HTML result page and normalize whitespace (best-effort)."""
        try:
            r = await client.get(
                "https://lite.duckduckgo.com/lite/",
                params={"q": query},
                headers={"User-Agent": "research-summarizer/0.1"},
            )
            r.raise_for_status()
            return re.sub(r"\s+", " ", r.text)[:2000]
        except Exception as exc:  # noqa: BLE001
            return f"(search failed: {exc})"
