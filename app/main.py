"""FastAPI entrypoint exposing health checks and the summarization HTTP API."""

from fastapi import FastAPI, HTTPException

from app.models.schemas import SummarizeRequest
from app.orchestrator.orchestrator import Orchestrator

app = FastAPI(title="Research paper summarizer")
_orchestrator = Orchestrator()


@app.get("/health")
async def health() -> dict[str, str]:
    """Return a simple OK payload for load balancers and uptime checks."""
    return {"status": "ok"}


@app.post("/summarize")
async def summarize(body: SummarizeRequest) -> dict[str, str | None]:
    """Run the full agent pipeline and return the path to the written summary file."""
    if not body.paper_url and not body.pdf_path:
        raise HTTPException(status_code=400, detail="Provide paper_url or pdf_path")
    state = await _orchestrator.run(body.paper_url, body.pdf_path)
    out = state.get("output_path")
    return {"output_path": str(out) if out else None}
