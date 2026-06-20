"""Turn the IR into plain-English, line-by-line steps.

This is the deterministic backbone of the explanation: it never calls out to a
model, so it always works (even offline) and always matches the actual code.
The AI layer in `ai.py` builds a higher-level narrative on top of these steps.
"""

from __future__ import annotations

from typing import Any, Dict, List

# Map AST/IR operator class names to their natural-language verb.
_AUG_VERB = {"add": "Increase", "sub": "Decrease", "mult": "Multiply", "div": "Divide"}


def explain_ir(ir: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Return a flat list of `{indent, line, text}` steps describing the code."""
    out: List[Dict[str, Any]] = []

    def emit(indent: int, node: Dict[str, Any], text: str) -> None:
        out.append({"indent": indent, "line": node.get("line"), "text": text.strip()})

    def walk(node: Dict[str, Any], indent: int = 0) -> None:
        kind = node.get("kind")

        if kind == "Module":
            for stmt in node.get("body", []):
                walk(stmt, indent)

        elif kind == "FunctionDef":
            args = ", ".join(node.get("args", []))
            emit(indent, node, f"Define a function {node.get('name', 'fn')}({args}) that does the following:")
            for stmt in node.get("body", []):
                walk(stmt, indent + 1)

        elif kind == "Assign":
            targets = ", ".join(node.get("targets", []))
            value = node.get("value", "")
            if value in ("{}", "dict()"):
                emit(indent, node, f"Start an empty dictionary called {targets}.")
            elif value in ("[]", "list()"):
                emit(indent, node, f"Start an empty list called {targets}.")
            elif value in ("0", "set()", "()"):
                emit(indent, node, f"Initialize {targets} to {value}.")
            else:
                emit(indent, node, f"Set {targets} to {value}.")

        elif kind == "AnnAssign":
            target = node.get("target", "")
            value = node.get("value")
            if value:
                emit(indent, node, f"Set {target} to {value}.")
            else:
                emit(indent, node, f"Declare {target} (type {node.get('annotation', '')}).")

        elif kind == "AugAssign":
            verb = _AUG_VERB.get((node.get("op") or "").lower())
            if verb:
                emit(indent, node, f"{verb} {node.get('target', '')} by {node.get('value', '')}.")
            else:
                emit(indent, node, f"Update {node.get('target', '')} with {node.get('value', '')}.")

        elif kind == "For":
            target = node.get("target", "item")
            it = node.get("iter", "")
            if "enumerate" in it:
                inner = it.replace("enumerate(", "").rstrip(")")
                emit(indent, node, f"Loop over {inner}, tracking both index and value as {target}.")
            elif target and it:
                emit(indent, node, f"Loop over {it} with {target}.")
            elif it:
                # C-style loop (no loop variable): `it` holds the continue condition.
                emit(indent, node, f"Loop while {it} stays true.")
            else:
                emit(indent, node, "Loop while the condition holds.")
            for stmt in node.get("body", []):
                walk(stmt, indent + 1)

        elif kind == "While":
            emit(indent, node, f"Keep looping while {node.get('test', '')} is true:")
            for stmt in node.get("body", []):
                walk(stmt, indent + 1)

        elif kind == "If":
            prefix = "Otherwise, if" if node.get("elif") else "If"
            emit(indent, node, f"{prefix} {node.get('test', '')}:")
            for stmt in node.get("body", []):
                walk(stmt, indent + 1)
            orelse = node.get("orelse") or []
            if orelse:
                # An `elif` chain is a single nested If; render it inline.
                if len(orelse) == 1 and orelse[0].get("kind") == "If":
                    walk(orelse[0], indent)
                else:
                    emit(indent, node, "Otherwise:")
                    for stmt in orelse:
                        walk(stmt, indent + 1)

        elif kind == "Return":
            value = node.get("value")
            emit(indent, node, f"Return {value}." if value else "Return from the function.")

        elif kind == "Call":
            func = node.get("func", "a function")
            args = ", ".join(node.get("args", [])) if node.get("args") else ""
            emit(indent, node, f"Call {func}({args})." if args else f"Call {func}().")

        elif kind == "Try":
            emit(indent, node, "Try the following, watching for errors:")
            for stmt in node.get("body", []):
                walk(stmt, indent + 1)
            for handler in node.get("handlers", []):
                exc = handler.get("type") or "an error"
                emit(indent, node, f"If {exc} occurs, handle it:")
                for stmt in handler.get("body", []):
                    walk(stmt, indent + 1)
            if node.get("finalbody"):
                emit(indent, node, "Finally, always run:")
                for stmt in node.get("finalbody", []):
                    walk(stmt, indent + 1)

        elif kind == "With":
            ctx = ", ".join(i.get("context_expr", "") for i in node.get("items", []))
            emit(indent, node, f"Use {ctx} as a managed resource:")
            for stmt in node.get("body", []):
                walk(stmt, indent + 1)

        elif kind in ("Import", "ImportFrom"):
            names = ", ".join(n.get("name", "") for n in node.get("names", []))
            module = node.get("module")
            emit(indent, node, f"Import {names} from {module}." if module else f"Import {names}.")

        elif kind == "Break":
            emit(indent, node, "Break out of the loop.")
        elif kind == "Continue":
            emit(indent, node, "Skip to the next loop iteration.")
        elif kind == "Pass":
            emit(indent, node, "Do nothing here (placeholder).")
        else:
            emit(indent, node, node.get("summary", f"{kind} statement."))

    walk(ir, 0)
    return out
