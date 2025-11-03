import os
from typing import List, Dict, Any

try:
    from openai import OpenAI  # optional
except Exception:  # pragma: no cover - optional dependency may be absent
    OpenAI = None  # type: ignore

_client = None

def _get_client():
    global _client
    if _client is None:
        if OpenAI is None:
            raise RuntimeError("OpenAI client not available. Install 'openai' and set OPENAI_API_KEY.")
        _client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _client

def enhance_explanation(code: str, rows: List[Dict[str, Any]]) -> str:
    """
    Turn structured explanation rows into a concise, resume-friendly narrative.
    """
    bullet_lines = []
    for r in rows or []:
        line = f"L{r.get('line','?')}: {r.get('text','')}"
        bullet_lines.append(line)
    bullets = "\n".join(f"- {b}" for b in bullet_lines)

    prompt = f"""You are a senior code reviewer.
Summarize the following code explanation for a portfolio app in 4-8 crisp bullets.
Avoid restating variable names unless necessary, and highlight complexity/loops/edge cases.

Code:
```\n{code}\n```

Structured notes:
{bullets}
"""

    client = _get_client()
    # gpt-4o-mini is a good fast default; change if you prefer
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    return resp.choices[0].message.content.strip()
