import argparse
import pathlib
from typing import Any, Dict, List

from backend.services import parser as parser_service
from backend.services import graph as graph_service


def _explain_stmt(stmt: Dict[str, Any], indent: int = 0) -> List[Dict[str, Any]]:
    line = stmt.get("line")
    kind = stmt.get("kind")
    rows: List[Dict[str, Any]] = []

    def add(text: str, extra_indent: int = 0):
        rows.append({"line": line, "indent": indent + extra_indent, "text": text})

    if kind == "FunctionDef":
        name = stmt.get("name"); args = stmt.get("args", [])
        add(f"Function '{name}' takes parameters {args} and contains:")
        for child in stmt.get("body", []):
            rows.extend(_explain_stmt(child, indent + 1))

    elif kind == "If":
        test = stmt.get("test")
        is_elif = stmt.get("elif", False)

        if is_elif:
            # Elif is a sibling of If: same indent
            add(f"Elif ({test}):")  # indent stays as-is
        else:
            add(f"Checks condition ({test}). If true:")  # top-level If

        # then-body
        for child in stmt.get("body", []):
            rows.extend(_explain_stmt(child, indent + 1))

        orelse = stmt.get("orelse", [])

        if is_elif:
            # This If-node is an elif; if it has an orelse, that's the trailing else of the chain
            if orelse:
                rows.append({"line": line, "indent": indent, "text": "Else:"})
                for child in orelse:
                    rows.extend(_explain_stmt(child, indent + 1))
        else:
            # top-level If: if orelse starts with an elif, render that elif at SAME indent (not +1)
            if (
                len(orelse) == 1
                and isinstance(orelse[0], dict)
                and orelse[0].get("elif")
            ):
                # render the elif sibling aligned with the If
                rows.extend(_explain_stmt(orelse[0], indent))   # <-- key change
            elif orelse:
                # plain else
                rows.append({"line": line, "indent": indent, "text": "Else:"})
                for child in orelse:
                    rows.extend(_explain_stmt(child, indent + 1))



    elif kind == "For":
        add(f"Loops with variable '{stmt.get('target')}' over ({stmt.get('iter')}):")
        for child in stmt.get("body", []):
            rows.extend(_explain_stmt(child, indent + 1))

    elif kind == "While":
        add(f"While condition ({stmt.get('test')}) holds:")
        for child in stmt.get("body", []):
            rows.extend(_explain_stmt(child, indent + 1))

    elif kind == "Assign":
        add(f"Assigns {stmt.get('value')} to {stmt.get('targets',[])}.")

    elif kind == "AugAssign":
        symbol = {"Add": "+=", "Sub": "-=", "Mult": "*=", "Div": "/="}.get(stmt.get("op"), "+=")
        add(f"Updates {stmt.get('target')} with {symbol} {stmt.get('value')}.")

    elif kind == "Return":
        add(f"Returns {stmt.get('value')}.")

    else:
        add(stmt.get("summary", "statement"))

    return rows

def explain_ir(ir: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for item in ir.get("body", []):
        rows.extend(_explain_stmt(item, 0))
    return rows if rows else [{"line": None, "indent": 0, "text": "No executable statements found."}]   

def main(argv=None):
    ap = argparse.ArgumentParser(description="CodeLensAI Explainer CLI")
    ap.add_argument("file", help="Path to a Python file")
    ap.add_argument("--explain", action="store_true", help="Print explanation")
    ap.add_argument("--mermaid", action="store_true", help="Print Mermaid flowchart")  # 👈 added
    args = ap.parse_args(argv)

    code = pathlib.Path(args.file).read_text(encoding="utf-8")
    ir = parser_service.parse_python_to_ir(code)

    if args.explain:
        print("\n=== Explanation ===")
        print(explain_ir(ir))

    if args.mermaid:
        from backend.services import graph as graph_service
        print("\n=== Mermaid (flowchart) ===")
        print(graph_service.ir_to_mermaid(ir))

    if not (args.explain or args.mermaid):
        print("Tip: use --explain and/or --mermaid.")


if __name__ == "__main__":
    raise SystemExit(main())
