"""A lightweight JavaScript / TypeScript parser.

There's no JS AST library in the Python standard library, and we want to stay
dependency-free for serverless. So this is a deliberately small line-based
parser: it recognises the common control-flow constructs (functions, if/else,
loops, returns, assignments) via regex and a brace stack. It won't handle every
exotic syntax, but it's plenty for the "explain the shape of this code" use case.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional


def _clean(s: Optional[str]) -> str:
    return (s or "").strip()


def _append(stack: List[Dict[str, Any]], stmt: Dict[str, Any]) -> None:
    stack[-1]["body"].append(stmt)


_FUNC = re.compile(r"^\s*(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_$][\w$]*)\s*\(([^)]*)\)\s*\{\s*$")
_ARROW = re.compile(r"^\s*(?:export\s+)?const\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s+)?\(([^)]*)\)\s*=>\s*\{\s*$")
_IF = re.compile(r"^\s*(?:\}\s*)?(?:else\s+)?if\s*\((.*)\)\s*\{\s*$")
_ELSE = re.compile(r"^\s*(?:\}\s*)?else\s*\{\s*$")
_FOR_OF_IN = re.compile(r"^\s*for\s*\(\s*(?:const|let|var)\s+([^\s;]+)\s+(of|in)\s+(.*)\)\s*\{\s*$")
_FOR_C = re.compile(r"^\s*for\s*\((.*);(.*);(.*)\)\s*\{\s*$")
_WHILE = re.compile(r"^\s*while\s*\((.*)\)\s*\{\s*$")
_RET = re.compile(r"^\s*return(?:\s+(.*?))?;?\s*$")
_AUG = re.compile(r"^\s*([A-Za-z_$][\w$.\[\]]*)\s*(\+=|-=|\*=|/=|%=|\^=|\|=|&=|<<=|>>=)\s*(.*);?\s*$")
_ASSIGN = re.compile(r"^\s*(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(.*?);?\s*$|^\s*([A-Za-z_$][\w$.\[\]]*)\s*=\s*(.*?);?\s*$")
_CALL = re.compile(r"^\s*([A-Za-z_$][\w$.]*)\s*\(.*\)\s*;?\s*$")

_AUG_OPS = {
    "+=": "Add", "-=": "Sub", "*=": "Mult", "/=": "Div", "%=": "Mod",
    "^=": "BitXor", "|=": "BitOr", "&=": "BitAnd", "<<=": "LShift", ">>=": "RShift",
}


def parse_jsts_to_ir(code: str) -> Dict[str, Any]:
    """Parse JS/TS source into the CodeLensAI IR (best effort)."""
    root: Dict[str, Any] = {"kind": "Module", "body": []}
    stack: List[Dict[str, Any]] = [{"kind": "Block", "body": root["body"]}]
    # Tracks the most recent `if` so a following `else` can be attached to it.
    last_if: Optional[Dict[str, Any]] = None

    for idx, raw in enumerate(code.splitlines(), start=1):
        line = raw.rstrip()
        if not line.strip():
            continue

        # A line that only closes a block pops the stack.
        if line.strip() == "}":
            if len(stack) > 1:
                stack.pop()
            last_if = None
            continue

        m = _FUNC.match(line) or _ARROW.match(line)
        if m:
            args = [a.strip() for a in _clean(m.group(2)).split(",") if a.strip()]
            fn = {
                "kind": "FunctionDef",
                "summary": f"function {_clean(m.group(1))}({', '.join(args)})",
                "line": idx,
                "name": _clean(m.group(1)),
                "args": args,
                "body": [],
            }
            _append(stack, fn)
            stack.append({"kind": "Block", "body": fn["body"]})
            last_if = None
            continue

        m = _IF.match(line)
        if m:
            # A leading `}` means this is an `} else if {` continuation.
            if line.strip().startswith("}") and len(stack) > 1:
                stack.pop()
            node = {"kind": "If", "summary": "if-statement", "line": idx,
                    "test": _clean(m.group(1)), "body": [], "orelse": []}
            _append(stack, node)
            stack.append({"kind": "Block", "body": node["body"]})
            last_if = node
            continue

        if _ELSE.match(line):
            if line.strip().startswith("}") and len(stack) > 1:
                stack.pop()
            if last_if is not None:
                else_body: List[Dict[str, Any]] = []
                last_if["orelse"] = else_body
                stack.append({"kind": "Block", "body": else_body})
            continue

        m = _FOR_OF_IN.match(line)
        if m:
            node = {"kind": "For", "summary": "for-loop", "line": idx,
                    "target": _clean(m.group(1)), "iter": _clean(m.group(3)),
                    "body": [], "orelse": []}
            _append(stack, node)
            stack.append({"kind": "Block", "body": node["body"]})
            last_if = None
            continue

        m = _FOR_C.match(line)
        if m:
            cond = _clean(m.group(2))
            node = {"kind": "For", "summary": "for-loop", "line": idx,
                    "target": "", "iter": cond or "(condition)", "body": [], "orelse": []}
            _append(stack, node)
            stack.append({"kind": "Block", "body": node["body"]})
            last_if = None
            continue

        m = _WHILE.match(line)
        if m:
            node = {"kind": "While", "summary": "while-loop", "line": idx,
                    "test": _clean(m.group(1)), "body": [], "orelse": []}
            _append(stack, node)
            stack.append({"kind": "Block", "body": node["body"]})
            last_if = None
            continue

        m = _RET.match(line)
        if m:
            _append(stack, {"kind": "Return", "summary": "return", "line": idx,
                            "value": _clean(m.group(1)) if m.group(1) else None})
            last_if = None
            continue

        m = _AUG.match(line)
        if m:
            _append(stack, {"kind": "AugAssign", "summary": "aug-assign", "line": idx,
                            "target": _clean(m.group(1)),
                            "op": _AUG_OPS.get(m.group(2), m.group(2)),
                            "value": _clean(m.group(3))})
            last_if = None
            continue

        m = _ASSIGN.match(line)
        if m:
            name = m.group(1) or m.group(3)
            value = m.group(2) or m.group(4)
            _append(stack, {"kind": "Assign", "summary": f"assign {name}", "line": idx,
                            "targets": [_clean(name)], "value": _clean(value)})
            last_if = None
            continue

        m = _CALL.match(line)
        if m:
            _append(stack, {"kind": "Call", "summary": f"call {_clean(m.group(1))}",
                            "line": idx, "func": _clean(m.group(1))})
            last_if = None
            continue

        # Anything else (comments, declarations we don't model) is ignored.

    return root
