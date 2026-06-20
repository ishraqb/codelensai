"""Python source -> intermediate representation (IR).

We lean on the standard-library `ast` module so the parse is accurate and
dependency-free (important: this runs inside a Vercel serverless function).
The IR is a plain dict tree that both the explainer and the flowchart builder
consume, which keeps those two consumers decoupled from Python's AST internals.
"""

from __future__ import annotations

import ast
from typing import Any, Dict, List


def _unparse(node: ast.AST | None) -> str:
    """Render an AST node back to source text, with a tiny fallback for very
    old runtimes that lack `ast.unparse`."""
    if node is None:
        return "None"
    if hasattr(ast, "unparse"):
        try:
            return ast.unparse(node)
        except Exception:
            pass
    # Minimal fallback for the handful of node types we care about.
    if hasattr(node, "id"):
        return getattr(node, "id")
    if hasattr(node, "attr"):
        return f"{_unparse(getattr(node, 'value', None))}.{node.attr}"
    return node.__class__.__name__


def _summary(node: ast.AST) -> str:
    """A short human label used as a flowchart node caption."""
    if isinstance(node, ast.FunctionDef):
        params = ", ".join(a.arg for a in node.args.args)
        return f"def {node.name}({params})"
    if isinstance(node, ast.For):
        return "for-loop"
    if isinstance(node, ast.While):
        return "while-loop"
    if isinstance(node, ast.If):
        return "if-statement"
    if isinstance(node, ast.Return):
        return "return"
    if isinstance(node, ast.Assign):
        return "assign " + ", ".join(_unparse(t) for t in node.targets)
    if isinstance(node, ast.AugAssign):
        return f"aug-assign ({type(node.op).__name__})"
    return node.__class__.__name__


def _walk_block(stmts: List[ast.stmt]) -> List[Dict[str, Any]]:
    """Translate a list of statements into IR entries, preserving line numbers
    and the structure we need for explanations and diagrams."""
    items: List[Dict[str, Any]] = []

    for s in stmts:
        entry: Dict[str, Any] = {"kind": s.__class__.__name__, "summary": _summary(s)}
        if hasattr(s, "lineno"):
            entry["line"] = s.lineno

        if isinstance(s, ast.FunctionDef):
            entry["name"] = s.name
            entry["args"] = [a.arg for a in s.args.args]
            entry["body"] = _walk_block(s.body)
            if s.decorator_list:
                entry["decorators"] = [_unparse(d) for d in s.decorator_list]

        elif isinstance(s, ast.If):
            entry["test"] = _unparse(s.test)
            entry["body"] = _walk_block(s.body)
            # Python models `elif` as a nested If inside `orelse`; flag it so the
            # explainer can phrase it as "otherwise, if ..." instead of nesting.
            entry["orelse"] = []
            if s.orelse:
                if len(s.orelse) == 1 and isinstance(s.orelse[0], ast.If):
                    nested = s.orelse[0]
                    entry["orelse"].append({
                        "kind": "If",
                        "summary": "if-statement",
                        "line": getattr(nested, "lineno", None),
                        "test": _unparse(nested.test),
                        "body": _walk_block(nested.body),
                        "orelse": _walk_block(nested.orelse),
                        "elif": True,
                    })
                else:
                    entry["orelse"] = _walk_block(s.orelse)

        elif isinstance(s, ast.For):
            entry["target"] = _unparse(s.target)
            entry["iter"] = _unparse(s.iter)
            entry["body"] = _walk_block(s.body)
            entry["orelse"] = _walk_block(s.orelse)

        elif isinstance(s, ast.While):
            entry["test"] = _unparse(s.test)
            entry["body"] = _walk_block(s.body)
            entry["orelse"] = _walk_block(s.orelse)

        elif isinstance(s, ast.Try):
            entry["body"] = _walk_block(s.body)
            entry["handlers"] = [{
                "kind": "ExceptHandler",
                "line": getattr(h, "lineno", None),
                "type": _unparse(h.type) if getattr(h, "type", None) else None,
                "name": h.name if isinstance(h.name, str) else None,
                "body": _walk_block(h.body),
            } for h in s.handlers]
            entry["orelse"] = _walk_block(s.orelse)
            entry["finalbody"] = _walk_block(s.finalbody)

        elif isinstance(s, ast.With):
            entry["items"] = [{
                "context_expr": _unparse(i.context_expr),
                "optional_vars": _unparse(i.optional_vars) if i.optional_vars else None,
            } for i in s.items]
            entry["body"] = _walk_block(s.body)

        elif isinstance(s, ast.Assign):
            entry["targets"] = [_unparse(t) for t in s.targets]
            entry["value"] = _unparse(s.value)

        elif isinstance(s, ast.AnnAssign):
            entry["target"] = _unparse(s.target)
            entry["annotation"] = _unparse(s.annotation)
            entry["value"] = _unparse(s.value) if s.value else None

        elif isinstance(s, ast.AugAssign):
            entry["target"] = _unparse(s.target)
            entry["op"] = type(s.op).__name__
            entry["value"] = _unparse(s.value)

        elif isinstance(s, ast.Return):
            entry["value"] = _unparse(s.value) if s.value else None

        elif isinstance(s, (ast.Break, ast.Continue, ast.Pass)):
            pass

        elif isinstance(s, ast.Expr):
            # A bare expression statement is most often a call (e.g. print(x)).
            if isinstance(s.value, ast.Call):
                call = s.value
                entry["kind"] = "Call"
                entry["func"] = _unparse(call.func)
                entry["summary"] = f"call {entry['func']}"
                entry["args"] = [_unparse(a) for a in call.args]
                if call.keywords:
                    entry["keywords"] = [
                        {"arg": kw.arg, "value": _unparse(kw.value)} for kw in call.keywords
                    ]
            else:
                entry["expr"] = _unparse(s.value)

        elif isinstance(s, ast.Import):
            entry["names"] = [{"name": n.name, "asname": n.asname} for n in s.names]

        elif isinstance(s, ast.ImportFrom):
            entry["module"] = s.module
            entry["level"] = s.level
            entry["names"] = [{"name": n.name, "asname": n.asname} for n in s.names]

        else:
            try:
                entry["raw"] = _unparse(s)
            except Exception:
                entry["raw"] = entry["kind"]

        items.append(entry)

    return items


def parse_python_to_ir(code: str) -> Dict[str, Any]:
    """Parse Python source into the CodeLensAI IR."""
    tree = ast.parse(code)
    return {"kind": "Module", "body": _walk_block(tree.body)}
