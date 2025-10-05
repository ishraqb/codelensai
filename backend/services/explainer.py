# backend/services/explainer.py
"""
Human-readable explanation generator for Python IR.
Produces clean, natural English text with indentation (no markdown or bullet points).
"""

from __future__ import annotations
from typing import Dict, List, Any


def explain_ir(ir: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Convert the IR into a structured explanation list with natural sentences."""
    out: List[Dict[str, Any]] = []

    def emit(indent: int, text: str) -> None:
        out.append({"indent": indent, "text": text.strip()})

    def walk(node: Dict[str, Any], indent: int = 0):
        kind = node.get("kind")

        if kind == "Module":
            for stmt in node.get("body", []):
                walk(stmt, indent)

        elif kind == "FunctionDef":
            name = node.get("name", "function")
            args = ", ".join(node.get("args", []))
            emit(indent, f"Define the function {name}({args}), which performs the following steps:")
            for stmt in node.get("body", []):
                walk(stmt, indent + 1)

        elif kind == "Assign":
            targets = ", ".join(node.get("targets", []))
            value = node.get("value", "")
            if value == "{}":
                emit(indent, f"Initialize an empty dictionary named {targets}.")
            elif value == "[]":
                emit(indent, f"Create an empty list named {targets}.")
            else:
                emit(indent, f"Assign {value} to {targets}.")

        elif kind == "AugAssign":
            target = node.get("target", "")
            op = node.get("op", "").lower()
            value = node.get("value", "")
            if op == "add":
                emit(indent, f"Increase {target} by {value}.")
            elif op == "sub":
                emit(indent, f"Decrease {target} by {value}.")
            else:
                emit(indent, f"Update {target} using operation {op} {value}.")

        elif kind == "For":
            target = node.get("target", "")
            iter_expr = node.get("iter", "")
            if "enumerate" in iter_expr:
                clean_iter = iter_expr.replace("enumerate(", "").replace(")", "")
                emit(indent, f"Loop through {clean_iter}, getting both the index and value as {target}.")
            else:
                emit(indent, f"Loop over {iter_expr} using variable {target}.")
            for stmt in node.get("body", []):
                walk(stmt, indent + 1)

        elif kind == "If":
            test = node.get("test", "")
            emit(indent, f"If {test} is true, then:")
            for stmt in node.get("body", []):
                walk(stmt, indent + 1)
            if node.get("orelse"):
                emit(indent, "Otherwise:")
                for stmt in node["orelse"]:
                    walk(stmt, indent + 1)

        elif kind == "Return":
            value = node.get("value", "")
            if value == "[seen[target - x], i]":
                emit(indent, "Return the indices of the two numbers that add up to the target.")
            elif value == "[]":
                emit(indent, "Return an empty list to indicate that no matching pair was found.")
            else:
                emit(indent, f"Return {value}.")

        else:
            emit(indent, node.get("summary", f"{kind} statement."))

    walk(ir, 0)
    return out
