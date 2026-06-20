"""IR -> Mermaid flowchart.

Walking a statement returns a `(head, tail)` pair: the first node the caller
should point at, and the last node that flows onward. Blocks are stitched by
connecting each statement's tail to the next statement's head, so decisions
(if / loops) fan out with labelled edges and rejoin cleanly without the
duplicate edges you'd get from naively chaining every node.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

_AUG_SYMBOL = {
    "add": "+=", "sub": "-=", "mult": "*=", "div": "/=", "truediv": "/=",
    "floordiv": "//=", "mod": "%=", "pow": "**=", "bitand": "&=", "bitor": "|=",
    "bitxor": "^=", "lshift": "<<=", "rshift": ">>=",
}

# A node walker yields the entry node id and the exit node id of a statement.
Span = Tuple[str, str]


def _clean(value: Any) -> str:
    """Make a label safe for Mermaid: single line, no double quotes."""
    if value is None:
        return ""
    return str(value).replace("\n", " ").replace("\r", " ").replace('"', "'").strip()


class _Builder:
    def __init__(self) -> None:
        self.lines: List[str] = ["flowchart TD"]
        self._n = 0

    def _id(self) -> str:
        self._n += 1
        return f"N{self._n}"

    def rect(self, label: str) -> str:
        nid = self._id()
        self.lines.append(f'{nid}["{_clean(label)}"]')
        return nid

    def diamond(self, label: str) -> str:
        nid = self._id()
        self.lines.append(f'{nid}{{"{_clean(label)}"}}')
        return nid

    def edge(self, a: str, b: str, label: Optional[str] = None) -> None:
        self.lines.append(f"{a} -->|{_clean(label)}| {b}" if label else f"{a} --> {b}")


def ir_to_mermaid(ir: Dict[str, Any]) -> str:
    b = _Builder()

    def walk_block(children: List[Dict[str, Any]]) -> Optional[Span]:
        """Wire a list of statements in sequence and return the block's span."""
        head: Optional[str] = None
        tail: Optional[str] = None
        for child in children or []:
            span = walk(child)
            if span is None:
                continue
            if head is None:
                head = span[0]
            else:
                b.edge(tail, span[0])  # type: ignore[arg-type]
            tail = span[1]
        return (head, tail) if head is not None else None

    def walk(stmt: Dict[str, Any]) -> Optional[Span]:
        kind = stmt.get("kind")
        summary = stmt.get("summary") or kind or "stmt"

        if kind == "FunctionDef":
            head = b.rect(summary)
            body = walk_block(stmt.get("body", []))
            if body:
                b.edge(head, body[0])
                return (head, body[1])
            return (head, head)

        if kind == "If":
            test = b.diamond(f"{_clean(stmt.get('test'))}?")
            exit_id = b.rect("continue")
            then_span = walk_block(stmt.get("body", []))
            if then_span:
                b.edge(test, then_span[0], "yes")
                b.edge(then_span[1], exit_id)
            else:
                b.edge(test, exit_id, "yes")
            else_span = walk_block(stmt.get("orelse", []))
            if else_span:
                b.edge(test, else_span[0], "no")
                b.edge(else_span[1], exit_id)
            else:
                b.edge(test, exit_id, "no")
            return (test, exit_id)

        if kind in ("For", "While"):
            label = (f"for {_clean(stmt.get('target'))} in {_clean(stmt.get('iter'))}?"
                     if kind == "For" else f"{_clean(stmt.get('test'))}?")
            dec = b.diamond(label)
            body = walk_block(stmt.get("body", []))
            if body:
                b.edge(dec, body[0], "loop")
                b.edge(body[1], dec)  # back-edge to re-check the condition
            exit_id = b.rect("done")
            b.edge(dec, exit_id, "exit")
            return (dec, exit_id)

        if kind == "Assign":
            targets = stmt.get("targets")
            value = stmt.get("value")
            if targets is not None and value is not None:
                nid = b.rect(f"{', '.join(map(_clean, targets))} = {_clean(value)}")
            else:
                nid = b.rect(summary)
            return (nid, nid)

        if kind == "AugAssign":
            sym = _AUG_SYMBOL.get((stmt.get("op") or "").lower(), "=")
            nid = b.rect(f"{_clean(stmt.get('target'))} {sym} {_clean(stmt.get('value'))}")
            return (nid, nid)

        if kind == "Return":
            value = stmt.get("value")
            nid = b.rect(f"return {_clean(value)}" if value is not None else "return")
            return (nid, nid)

        nid = b.rect(_clean(summary))
        return (nid, nid)

    tail: Optional[str] = None
    for top in ir.get("body", []):
        span = walk(top)
        if span is None:
            continue
        if tail:
            b.edge(tail, span[0])
        tail = span[1]

    return "\n".join(b.lines)
