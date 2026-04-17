# distill

**distill** is a small **agentic research paper summarizer**: it ingests a paper (URL or PDF), gathers light web context, drafts a **conceptual** summary (problem, method, results, limitations, simplified terms), has a review pass that can trigger revision, then writes a **plain-text report** under `outputs/`.

## How it works

1. **Ingestion** — Fetch PDF/HTML or read a local PDF; extract text, rough sections, and figure/table mentions.
2. **ReAct research** — Seed key phrases, run a short observe/search loop (stub-friendly hooks for real search + LLM reasoning).
3. **Summarization** — Build a structured summary (currently placeholder text with LLM hooks).
4. **Reflection** — Check for empty sections and optionally send notes back for another summarization round.
5. **Orchestrator** — Runs the above in order and saves the final `.txt` file.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- Health: `GET /health`
- Summarize: `POST /summarize` with JSON `{"paper_url": "https://..."}` and/or `{"pdf_path": "/path/to/file.pdf"}`  
  Response includes `output_path` to the generated summary.

Copy `.env.example` to `.env` if you want to tune paths and limits (`OUTPUT_DIR`, `MAX_REACT_STEPS`, `MAX_REVISION_ROUNDS`, optional LLM settings).

## Testing

With the API running (`uvicorn` locally or `docker compose` on port 8000), you can smoke-test it in two ways.

### Script (`scripts/test_api.py`)

Uses only the Python standard library (no extra packages for the client).

```bash
# Fast: GET /health only
python3 scripts/test_api.py --skip-summarize

# Full pipeline: default public PDF URL (can take several minutes)
python3 scripts/test_api.py

# Another host or port
API_BASE=http://127.0.0.1:8080 python3 scripts/test_api.py --skip-summarize
# or
python3 scripts/test_api.py --base-url http://127.0.0.1:8080 --paper-url "https://arxiv.org/pdf/XXXX.XXXXX.pdf"

# Local PDF — path must be readable by the API process (e.g. absolute path on the server host)
python3 scripts/test_api.py --pdf-path /absolute/path/to/paper.pdf
```

Optional flags: `--health-timeout`, `--summarize-timeout` (defaults 15s and 300s). On success, the script prints `output_path` from `POST /summarize`.

### curl

```bash
curl -sS http://127.0.0.1:8000/health

curl -sS -X POST http://127.0.0.1:8000/summarize \
  -H 'Content-Type: application/json' \
  -d '{"paper_url":"https://arxiv.org/pdf/1706.03762.pdf"}'
```

## Docker

```bash
docker compose up --build
```

Summaries are written under `./outputs` (mounted in `docker-compose.yml`).

## Stack

Python 3.11+, FastAPI, Uvicorn, Pydantic, httpx, pypdf.
