"""Vercel serverless function: POST /api/explain.

Takes { code, language } and returns the structured explanation, an AI summary
+ complexity estimate, and a Mermaid flowchart. Implemented with only the
standard library so cold starts stay fast and there are no install steps.
"""

from __future__ import annotations

import json
import os
import sys
from http.server import BaseHTTPRequestHandler

# Make the sibling `_lib` package importable regardless of Vercel's CWD.
sys.path.insert(0, os.path.dirname(__file__))

from _lib import ai, explainer, graph, parser, parser_js  # noqa: E402

MAX_CODE_BYTES = 100_000  # ~100 KB guards against oversized payloads.


def _build_response(code: str, language: str) -> dict:
    lang = (language or "python").lower()
    if lang == "python":
        ir = parser.parse_python_to_ir(code)
    elif lang in ("javascript", "typescript"):
        ir = parser_js.parse_jsts_to_ir(code)
    else:
        raise ValueError(f"Unsupported language: {language}")

    steps = explainer.explain_ir(ir)

    diagram = ""
    try:
        diagram = graph.ir_to_mermaid(ir)
    except Exception:
        # A flowchart failure shouldn't sink the whole explanation.
        diagram = ""

    insights = ai.generate_insights(code, steps, ir)

    return {
        "language": lang,
        "summary": insights["summary"],
        "complexity": insights["complexity"],
        "ai": insights["ai"],
        "steps": steps,
        "diagram": diagram,
    }


class handler(BaseHTTPRequestHandler):
    def _send(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:  # noqa: N802 - required handler name
        self._send(204, {})

    def do_POST(self) -> None:  # noqa: N802 - required handler name
        try:
            length = int(self.headers.get("Content-Length", 0))
        except (TypeError, ValueError):
            length = 0

        if length <= 0 or length > MAX_CODE_BYTES:
            # Generic client-facing message; no internal details leaked.
            self._send(400, {"error": "Request body missing or too large."})
            return

        try:
            data = json.loads(self.rfile.read(length).decode("utf-8"))
            code = data.get("code", "")
            language = data.get("language", "python")
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._send(400, {"error": "Invalid JSON body."})
            return

        if not isinstance(code, str) or not code.strip():
            self._send(400, {"error": "No code provided."})
            return

        try:
            self._send(200, _build_response(code, language))
        except SyntaxError as exc:
            # Surface only the line/offset, not internal tracebacks.
            self._send(200, {"error": f"Could not parse the code: {exc.msg}"})
        except ValueError as exc:
            self._send(400, {"error": str(exc)})
        except Exception:
            # Avoid leaking implementation details to the client.
            self._send(500, {"error": "Something went wrong while analyzing the code."})
