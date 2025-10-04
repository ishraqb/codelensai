import ast
from typing import Any, Dict, List

def _unparse(node):
    """Safely convert an AST node back to source text (fallback if ast.unparse missing)."""
    try:
        import ast
        if hasattr(ast, "unparse"):
            return ast.unparse(node)
    except Exception:
        pass
    # very small fallback for common primitives
    if node is None:
        return "None"
    if hasattr(node, "id"):           # Name
        return getattr(node, "id")
    if hasattr(node, "attr"):         # Attribute
        base = _unparse(getattr(node, "value", None))
        return f"{base}.{node.attr}"
    if hasattr(node, "n"):            # Num (py<3.8)
        return str(getattr(node, "n"))
    if hasattr(node, "s"):            # Str (py<3.8)
        return repr(getattr(node, "s"))
    return node.__class__.__name__

def _node_summary(node: ast.AST) -> str:
    """Return a short string summary for a given AST node."""
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
        targets = [ast.unparse(t) for t in node.targets]
        return "assign " + ", ".join(targets)
    if isinstance(node, ast.Call):
        return f"call {ast.unparse(node.func)}"
    if isinstance(node, ast.AugAssign):
        op = type(node.op).__name__
        return f"aug-assign ({op})"
    return node.__class__.__name__

def _walk_block(stmts: List[ast.stmt]) -> List[Dict[str, Any]]:
    """
    Convert a list of AST statements into our IR.
    Adds:
      - line numbers (entry['line'])
      - richer coverage: AugAssign, AnnAssign, Expr/Call, With, Try/Except/Finally, Import, ImportFrom
      - 'elif' detection for If nodes (entry['elif'] = True)
    """
    items: List[Dict[str, Any]] = []

    for s in stmts:
        kind = s.__class__.__name__
        entry: Dict[str, Any] = {
            "kind": kind,
            "summary": _node_summary(s),
        }
        if hasattr(s, "lineno"):
            entry["line"] = s.lineno

        # --- Functions ---
        if isinstance(s, ast.FunctionDef):
            entry["name"] = s.name
            entry["args"] = [a.arg for a in s.args.args]
            # defaults/kwonly/varargs optional: add later if needed
            entry["body"] = _walk_block(s.body)
            # decorators (optional metadata)
            if s.decorator_list:
                entry["decorators"] = [_unparse(d) for d in s.decorator_list]

        # --- If / Elif / Else ---
        elif isinstance(s, ast.If):
            entry["test"] = _unparse(s.test)
            entry["body"] = _walk_block(s.body)

            # Detect `elif`: Python represents `elif` as an If inside `orelse`.
            entry["orelse"] = []
            if s.orelse:
                # if the first orelse stmt is also an If, mark it as elif
                if len(s.orelse) == 1 and isinstance(s.orelse[0], ast.If):
                    elif_if = s.orelse[0]
                    elif_entry = {
                        "kind": "If",
                        "summary": "if-statement",
                        "line": getattr(elif_if, "lineno", None),
                        "test": _unparse(elif_if.test),
                        "body": _walk_block(elif_if.body),
                        "orelse": _walk_block(elif_if.orelse),
                        "elif": True,  # <--- mark this branch as elif
                    }
                    entry["orelse"].append(elif_entry)
                else:
                    entry["orelse"] = _walk_block(s.orelse)

        # --- For / AsyncFor ---
        elif isinstance(s, ast.For):
            entry["target"] = _unparse(s.target)
            entry["iter"]   = _unparse(s.iter)
            entry["body"]   = _walk_block(s.body)
            entry["orelse"] = _walk_block(s.orelse)

        # --- While ---
        elif isinstance(s, ast.While):
            entry["test"]   = _unparse(s.test)
            entry["body"]   = _walk_block(s.body)
            entry["orelse"] = _walk_block(s.orelse)

        # --- Try / Except / Else / Finally ---
        elif isinstance(s, ast.Try):
            entry["body"] = _walk_block(s.body)
            # except handlers
            handlers = []
            for h in s.handlers:
                h_entry = {
                    "kind": "ExceptHandler",
                    "line": getattr(h, "lineno", None),
                    "type": _unparse(h.type) if getattr(h, "type", None) else None,
                    "name": h.name if isinstance(h.name, str) else None,
                    "body": _walk_block(h.body),
                }
                handlers.append(h_entry)
            entry["handlers"] = handlers
            # else / finally
            entry["orelse"]  = _walk_block(s.orelse)
            entry["finalbody"] = _walk_block(s.finalbody)

        # --- With / AsyncWith ---
        elif isinstance(s, ast.With):
            entry["items"] = [{
                "context_expr": _unparse(i.context_expr),
                "optional_vars": _unparse(i.optional_vars) if i.optional_vars else None
            } for i in s.items]
            entry["body"] = _walk_block(s.body)

        # --- Assignments ---
        elif isinstance(s, ast.Assign):
            entry["targets"] = [_unparse(t) for t in s.targets]
            entry["value"]   = _unparse(s.value)

        elif isinstance(s, ast.AnnAssign):
            entry["target"] = _unparse(s.target)
            entry["annotation"] = _unparse(s.annotation)
            entry["value"] = _unparse(s.value) if s.value else None
            entry["simple"] = s.simple  # 1 means simple name

        elif isinstance(s, ast.AugAssign):
            entry["target"] = _unparse(s.target)
            entry["op"]     = type(s.op).__name__   # e.g., Add, Sub, Mult
            entry["value"]  = _unparse(s.value)

        # --- Returns / Control flow ---
        elif isinstance(s, ast.Return):
            entry["value"] = _unparse(s.value) if s.value else None

        elif isinstance(s, ast.Break):
            pass  # no extra fields

        elif isinstance(s, ast.Continue):
            pass  # no extra fields

        elif isinstance(s, ast.Pass):
            pass

        # --- Expressions (calls, literals, etc.) ---
        elif isinstance(s, ast.Expr):
            # common case: a bare function call like `print(x)`
            if isinstance(s.value, ast.Call):
                call = s.value
                entry["kind"] = "Call"
                entry["summary"] = f"call {_unparse(call.func)}"
                entry["func"] = _unparse(call.func)
                entry["args"] = [_unparse(a) for a in call.args]
                # keywords: {"kw": "arg=value"}
                if call.keywords:
                    entry["keywords"] = [
                        {"arg": kw.arg, "value": _unparse(kw.value)}
                        for kw in call.keywords
                    ]
            else:
                # some other expression (string literal docstring at top-level, etc.)
                entry["expr"] = _unparse(s.value)

        # --- Imports ---
        elif isinstance(s, ast.Import):
            entry["names"] = [{"name": n.name, "asname": n.asname} for n in s.names]

        elif isinstance(s, ast.ImportFrom):
            entry["module"] = s.module
            entry["level"]  = s.level  # relative import level (0 means absolute)
            entry["names"]  = [{"name": n.name, "asname": n.asname} for n in s.names]

        # --- Fallback for unhandled nodes (rare) ---
        else:
            # Keep generic entry with summary/kind/line; optionally stash raw repr
            try:
                entry["raw"] = _unparse(s)
            except Exception:
                entry["raw"] = kind

        items.append(entry)

    return items


def parse_python_to_ir(code: str) -> Dict[str, Any]:
    """Parse Python code into our custom IR (Intermediate Representation)."""
    tree = ast.parse(code)
    return {"kind": "Module", "body": _walk_block(tree.body)}
