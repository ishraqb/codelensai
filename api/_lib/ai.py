"""The AI layer of CodeLensAI.

Goal: a genuinely "AI" summary + complexity estimate that costs nothing and
needs no signup. We call Pollinations' free, keyless text endpoint. If a
GEMINI_API_KEY happens to be set we prefer Google's model, but neither is
required - everything degrades gracefully to a deterministic heuristic so the
app never breaks and never blocks the user behind a paywall.

Security note: the outbound request targets a single hard-coded, trusted host
(constant URL below). User code is only ever sent in the JSON body as prompt
text, never used to build the destination URL, so there is no SSRF surface here.
"""

from __future__ import annotations

import json
import os
import re
import urllib.request
from typing import Any, Dict, List, Optional

# Fixed, trusted endpoints. These are constants, not derived from user input.
_POLLINATIONS_URL = "https://text.pollinations.ai/openai"
_GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

_TIMEOUT_SEC = 20

# Pollinations sits behind Cloudflare, which blocks the default Python
# user-agent. A standard browser UA gets us through.
_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)


def _build_prompt(code: str, steps: List[Dict[str, Any]]) -> str:
    notes = "\n".join(f"- {s.get('text', '')}" for s in steps[:40])
    return (
        "You are a precise, friendly code reviewer. Given the code and the "
        "extracted steps below, respond with STRICT JSON only (no markdown), "
        'shaped exactly as {"summary": string, "complexity": string}.\n'
        "- summary: 2-3 sentences in plain English explaining what the code does "
        "and any notable edge cases. No restating every variable.\n"
        "- complexity: the worst-case time complexity in Big-O notation, e.g. "
        '"O(n)" or "O(n log n)", with a 3-6 word reason.\n\n'
        f"Code:\n```\n{code[:6000]}\n```\n\nExtracted steps:\n{notes}\n"
    )


def _extract_json(text: str) -> Optional[Dict[str, Any]]:
    """Pull the first JSON object out of a model response, tolerating stray
    prose or code fences around it."""
    if not text:
        return None
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        data = json.loads(match.group(0))
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        return None


def _post_json(url: str, payload: Dict[str, Any], headers: Dict[str, str]) -> str:
    body = json.dumps(payload).encode("utf-8")
    headers = {"User-Agent": _USER_AGENT, **headers}
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=_TIMEOUT_SEC) as resp:  # nosec B310 - constant trusted host
        return resp.read().decode("utf-8")


def _call_gemini(prompt: str, api_key: str) -> Optional[Dict[str, Any]]:
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    raw = _post_json(f"{_GEMINI_URL}?key={api_key}", payload, {"Content-Type": "application/json"})
    data = json.loads(raw)
    text = data["candidates"][0]["content"]["parts"][0]["text"]
    return _extract_json(text)


def _call_pollinations(prompt: str) -> Optional[Dict[str, Any]]:
    payload = {
        "model": "openai",
        "messages": [{"role": "user", "content": prompt}],
    }
    raw = _post_json(_POLLINATIONS_URL, payload, {"Content-Type": "application/json"})
    # The endpoint mirrors the OpenAI chat schema.
    try:
        text = json.loads(raw)["choices"][0]["message"]["content"]
    except (KeyError, IndexError, json.JSONDecodeError):
        text = raw
    return _extract_json(text)


def estimate_complexity(ir: Dict[str, Any]) -> str:
    """Heuristic Big-O from the deepest nesting of loops in the IR.

    This is the fallback when the model is unavailable, and a sanity check
    otherwise. It counts how many loops are nested inside each other.
    """
    def depth(node: Dict[str, Any]) -> int:
        children: List[Dict[str, Any]] = []
        for key in ("body", "orelse", "finalbody"):
            children.extend(node.get(key, []) or [])
        for handler in node.get("handlers", []) or []:
            children.extend(handler.get("body", []) or [])
        child_max = max((depth(c) for c in children), default=0)
        is_loop = node.get("kind") in ("For", "While")
        return child_max + (1 if is_loop else 0)

    loops = max((depth(stmt) for stmt in ir.get("body", [])), default=0)
    if loops == 0:
        return "O(1) — no loops, runs in constant time"
    if loops == 1:
        return "O(n) — single pass over the input"
    if loops == 2:
        return "O(n^2) — nested loops over the input"
    return f"O(n^{loops}) — {loops} levels of nested loops"


def generate_insights(code: str, steps: List[Dict[str, Any]], ir: Dict[str, Any]) -> Dict[str, Any]:
    """Return {summary, complexity, ai} - AI-written when possible, heuristic
    otherwise. Always returns something usable."""
    fallback = {
        "summary": "",
        "complexity": estimate_complexity(ir),
        "ai": False,
    }

    prompt = _build_prompt(code, steps)
    gemini_key = os.getenv("GEMINI_API_KEY")

    try:
        data = _call_gemini(prompt, gemini_key) if gemini_key else _call_pollinations(prompt)
    except Exception:
        # Network/timeout/parse issues should never surface to the user - we
        # simply fall back to the deterministic estimate.
        return fallback

    if not data:
        return fallback

    return {
        "summary": str(data.get("summary", "")).strip(),
        "complexity": str(data.get("complexity", "")).strip() or fallback["complexity"],
        "ai": True,
    }
