"""Fetch papers from URL or local PDF and normalize into structured text."""

import io
import re
from typing import Any

import httpx
from pypdf import PdfReader

from app.agents.base import Agent
from app.models.schemas import FigureRef, ParsedPaper


class IngestionAgent(Agent):
    """Downloads or reads PDFs/HTML and produces `ParsedPaper` on `state['parsed']`."""

    name = "ingestion"

    async def run(self, state: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        """Populate `state['parsed']` from `paper_url` or `pdf_path` in state/kwargs."""
        url = kwargs.get("paper_url") or state.get("paper_url")
        path = kwargs.get("pdf_path") or state.get("pdf_path")
        if url:
            parsed = await self._from_url(str(url))
        elif path:
            parsed = self._from_pdf_path(path)
        else:
            raise ValueError("Need paper_url or pdf_path")
        state["parsed"] = parsed
        return state

    async def _from_url(self, url: str) -> ParsedPaper:
        """GET the URL and branch on PDF vs HTML parsing."""
        async with httpx.AsyncClient(follow_redirects=True, timeout=120.0) as client:
            r = await client.get(url)
            r.raise_for_status()
            content_type = (r.headers.get("content-type") or "").lower()
            if "pdf" in content_type or url.lower().endswith(".pdf"):
                return self._parse_pdf_bytes(r.content, source_url=url)
            return self._parse_html(r.text, source_url=url)

    def _from_pdf_path(self, path: str) -> ParsedPaper:
        """Read a local PDF file and parse it like a downloaded PDF."""
        with open(path, "rb") as f:
            return self._parse_pdf_bytes(f.read(), source_url=path)

    def _parse_pdf_bytes(self, data: bytes, source_url: str | None) -> ParsedPaper:
        """Extract page text, naive figure/table mentions, and section splits."""
        reader = PdfReader(io.BytesIO(data))
        parts: list[str] = []
        figures: list[FigureRef] = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            parts.append(text)
            for m in re.finditer(r"(Figure|Fig\.|Table)\s*\d+", text, re.I):
                figures.append(FigureRef(page=i + 1, label=m.group(0)))
        full = "\n\n".join(parts)
        sections = self._heuristic_sections(full)
        return ParsedPaper(
            title=reader.metadata.title if reader.metadata else None,
            raw_text=full,
            sections=sections,
            figures=figures,
            source_url=source_url,
        )

    def _heuristic_sections(self, text: str) -> list[dict[str, Any]]:
        """Split full text on common section headings; fallback to a single body block."""
        sections: list[dict[str, Any]] = []
        pattern = re.compile(
            r"^(Abstract|Introduction|Related Work|Background|Method|Methods|"
            r"Experiments|Results|Discussion|Conclusion|References)\b",
            re.MULTILINE | re.IGNORECASE,
        )
        matches = list(pattern.finditer(text))
        for i, m in enumerate(matches):
            start = m.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            name = m.group(1).strip()
            sections.append({"name": name, "body": text[start:end].strip()})
        if not sections:
            sections.append({"name": "body", "body": text})
        return sections

    def _parse_html(self, html: str, source_url: str | None) -> ParsedPaper:
        """Strip tags/scripts and run the same section heuristics on visible text."""
        text = re.sub(r"<script[^>]*>[\s\S]*?</script>", " ", html, flags=re.I)
        text = re.sub(r"<style[^>]*>[\s\S]*?</style>", " ", text, flags=re.I)
        text = re.sub(r"<[^>]+>", "\n", text)
        text = re.sub(r"\s+", " ", text).strip()
        title_m = re.search(r"<title[^>]*>([^<]+)</title>", html, re.I)
        return ParsedPaper(
            title=title_m.group(1).strip() if title_m else None,
            raw_text=text,
            sections=self._heuristic_sections(text),
            figures=[],
            source_url=source_url,
        )
