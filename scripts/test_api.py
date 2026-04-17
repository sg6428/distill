#!/usr/bin/env python3
"""Call a running distill API: health check and optional full summarize run.

Uses only the Python standard library (no httpx required on the runner).

Usage:
  API_BASE=http://127.0.0.1:8000 python3 scripts/test_api.py
  python3 scripts/test_api.py --base-url http://localhost:8000 --skip-summarize
  python3 scripts/test_api.py --pdf-path /path/to/paper.pdf
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request


def _request_json(
    method: str,
    url: str,
    *,
    body: dict | None = None,
    timeout: float,
) -> tuple[int, dict | list | str | None]:
    data = None
    headers = {"Accept": "application/json"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            status = resp.status
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        status = exc.code
        try:
            parsed: dict | list | str | None = json.loads(raw) if raw else None
        except json.JSONDecodeError:
            parsed = raw
        return status, parsed

    if not raw.strip():
        return status, None
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        parsed = raw
    return status, parsed


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-test the distill FastAPI service.")
    parser.add_argument(
        "--base-url",
        default=os.environ.get("API_BASE", "http://127.0.0.1:8000").rstrip("/"),
        help="API root (default: API_BASE env or http://127.0.0.1:8000)",
    )
    parser.add_argument(
        "--paper-url",
        default="https://arxiv.org/pdf/1706.03762.pdf",
        help="URL for POST /summarize (ignored if --skip-summarize)",
    )
    parser.add_argument("--pdf-path", default=None, help="Local PDF path for POST /summarize")
    parser.add_argument(
        "--skip-summarize",
        action="store_true",
        help="Only GET /health (no POST /summarize)",
    )
    parser.add_argument("--health-timeout", type=float, default=15.0)
    parser.add_argument("--summarize-timeout", type=float, default=300.0)
    args = parser.parse_args()

    base = args.base_url
    print(f"Base URL: {base}")

    try:
        status, data = _request_json("GET", f"{base}/health", timeout=args.health_timeout)
    except OSError as exc:
        print(f"FAIL /health (connection): {exc}", file=sys.stderr)
        return 1

    if status != 200:
        print(f"FAIL /health: HTTP {status} body={data!r}", file=sys.stderr)
        return 1
    if not isinstance(data, dict) or data.get("status") != "ok":
        print(f"FAIL /health: unexpected JSON {data!r}", file=sys.stderr)
        return 1
    print("OK /health:", data)

    if args.skip_summarize:
        return 0

    body: dict[str, str | None] = {}
    if args.pdf_path:
        body["pdf_path"] = args.pdf_path
    elif args.paper_url:
        body["paper_url"] = args.paper_url
    else:
        print("FAIL: need --paper-url or --pdf-path", file=sys.stderr)
        return 1

    print("POST /summarize", body)
    try:
        status, out = _request_json(
            "POST",
            f"{base}/summarize",
            body=body,
            timeout=args.summarize_timeout,
        )
    except OSError as exc:
        print(f"FAIL /summarize (connection): {exc}", file=sys.stderr)
        return 1

    if status != 200:
        print(f"FAIL /summarize: HTTP {status} body={out!r}", file=sys.stderr)
        return 1
    if not isinstance(out, dict):
        print(f"FAIL /summarize: expected JSON object, got {out!r}", file=sys.stderr)
        return 1

    path = out.get("output_path")
    if not path:
        print(f"FAIL /summarize: no output_path in {out!r}", file=sys.stderr)
        return 1
    print("OK /summarize:", out)
    print("Open or inspect:", path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
