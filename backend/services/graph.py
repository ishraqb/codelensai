# backend/services/graph.py

from __future__ import annotations
from typing import Any, Dict, List

"""
IR → Mermaid flowchart generator

Expected IR (shape your parser already returns), e.g.
{
  "kind": "Module",
  "body": [
    {
      "kind": "FunctionDef",
      "summary": "def two_sum(nums, target)",
      "line": 1,
      "name": "two_sum",
      "args": ["nums", "target"],
      "body": [
        {"kind": "Assign", "summary": "assign seen", ...},
        {"kind": "For", "summary": "for-loop", "target": "(i, x)", "iter": "enumerate(nums)", "body": [...]},
        {"kind": "Return", "summary": "return", "value": "[]"}
      ]
    }
  ]
}
"""

# ---------------- utils ---------------- #

def _clean(s: Any) -> str:
    """Make labels Mermaid-safe: no newlines, no double-quotes."""
    if s is None:
        return ""
    s = str(s)
    s = s.replace("\n", " ").replace("\r", " ")
    s = s.replace('"', "'")
    return s.strip()


class _Builder:
    """Small helper to construct Mermaid lines + unique node ids."""
    def __init__(self) -> None:
        self.lines: List[str] = ["flowchart TD"]
        self._i = 0

    def new_id(self, prefix: str = "N") -> str:
        self._i += 1
        return f"{prefix}{self._i}"

    def rect(self, label: str) -> str:
        nid = self.new_id()
        self.lines.append(f'{nid}["{_clean(label)}"]')
        return nid

    def diamond(self, label: str) -> str:
        nid = self.new_id()
        self.lines.append(f'{nid}{{"{_clean(label)}"}}')
        return nid

    def connect(self, a: str, b: str, label: str | None = None) -> None:
        if label:
            self.lines.append(f'{a} --|{_clean(label)}|--> {b}')
        else:
            self.lines.append(f"{a} --> {b}")

    def chain(self, nodes: List[str]) -> None:
        for u, v in zip(nodes, nodes[1:]):
            self.connect(u, v)


# --------------- main API --------------- #

def ir_to_mermaid(ir: Dict[str, Any]) -> str:
    """
    Convert CodeLensAI IR to a Mermaid flowchart string.
    """
    b = _Builder()

    def walk(stmt: Dict[str, Any]) -> List[str]:
        """
        Walk a single statement and return a *sequence* of visible node ids
        representing its entry→...→exit path. The last id is considered the "tail".
        """
        kind = stmt.get("kind")
        summary = stmt.get("summary") or kind or "stmt"

        # ---- Structured statements ----

        if kind == "FunctionDef":
            head = b.rect(summary)
            body_ids: List[str] = []
            for child in stmt.get("body", []):
                body_ids.extend(walk(child))
            seq = [head] + body_ids if body_ids else [head]
            b.chain(seq)
            return seq

        if kind == "If":
            # decision
            test = b.diamond(f"{_clean(stmt.get('test'))} ?")
            # then-branch
            then_ids: List[str] = []
            for child in stmt.get("body", []):
                then_ids.extend(walk(child))
            # exit join
            exit_id = b.rect("next")
            if then_ids:
                b.connect(test, then_ids[0], "true")
                b.chain(then_ids)
                b.connect(then_ids[-1], exit_id)
            # false to exit
            b.connect(test, exit_id, "false")
            return [test, exit_id]

        if kind == "For":
            # for-loop as decision with loop body + back-edge + exit
            target = _clean(stmt.get("target"))
            iter_ = _clean(stmt.get("iter"))
            dec = b.diamond(f"for {target} in {iter_} ?")
            body_ids: List[str] = []
            for child in stmt.get("body", []):
                body_ids.extend(walk(child))
            if body_ids:
                b.connect(dec, body_ids[0], "yes")
                b.chain(body_ids)
                b.connect(body_ids[-1], dec)  # back-edge
            exit_id = b.rect("after for")
            b.connect(dec, exit_id, "no")
            return [dec, exit_id]

        if kind == "While":
            # while-loop decision, body, back-edge, exit
            dec = b.diamond(f"{_clean(stmt.get('test'))} ?")
            body_ids: List[str] = []
            for child in stmt.get("body", []):
                body_ids.extend(walk(child))
            if body_ids:
                b.connect(dec, body_ids[0], "true")
                b.chain(body_ids)
                b.connect(body_ids[-1], dec)  # loop back
            exit_id = b.rect("after while")
            b.connect(dec, exit_id, "false")
            return [dec, exit_id]

        # ---- Simple statements ----

        if kind == "Assign":
            # e.g., "assign seen" or pretty-print targets/value if present
            lbl = summary
            targets = stmt.get("targets")
            value = stmt.get("value")
            if targets is not None and value is not None:
                lbl = f"assign {', '.join(map(_clean, targets))} = { _clean(value) }"
            return [b.rect(lbl)]

        if kind == "AugAssign":
            # e.g., "i += 1"
            target = _clean(stmt.get("target"))
            op = _clean(stmt.get("op") or "")
            value = _clean(stmt.get("value"))
            # Map common ops: Add/Sub/Mult/Div/Mod/FloorDiv/Pow/BitAnd/BitOr/BitXor/LShift/RShift
            op_map = {
                "add": "+",
                "sub": "-",
                "mult": "*",
                "div": "/",
                "truediv": "/",
                "floordiv": "//",
                "mod": "%",
                "pow": "**",
                "lshift": "<<",
                "rshift": ">>",
                "bitand": "&",
                "bitor": "|",
                "bitxor": "^",
            }
            sym = op_map.get(op.lower(), op.lower())
            lbl = f"{target} {sym}+= {value}" if sym in {"+","-","*","/","//","%","**","<<",">>","&","|","^"} else f"{target} {op and op.lower()}= {value}"
            # Fix spacing for standard ops
            for k, v in op_map.items():
                lbl = lbl.replace(f" {v}+=", f" {v}=")
            return [b.rect(lbl)]

        if kind == "Return":
            val = stmt.get("value")
            lbl = f"return { _clean(val) }" if val is not None else "return"
            return [b.rect(lbl)]

        # Fallback: generic rectangle
        return [b.rect(summary)]

    # Top level — stitch sequentially
    last_tail: str | None = None
    for top in ir.get("body", []):
        seq = walk(top)
        if last_tail:
            b.connect(last_tail, seq[0])
        last_tail = seq[-1] if seq else last_tail

    return "\n".join(b.lines)
