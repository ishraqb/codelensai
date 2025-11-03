import re
from typing import Any, Dict, List, Optional


def _clean(s: Optional[str]) -> str:
    return (s or "").strip()


def _append_stmt(stack: List[Dict[str, Any]], stmt: Dict[str, Any]) -> None:
    stack[-1]["body"].append(stmt)


def parse_jsts_to_ir(code: str) -> Dict[str, Any]:
    """Very lightweight JS/TS parser to IR using regex + brace stacking.
    Handles function/if/else/for/while/return/assign/augassign.
    """
    lines = code.splitlines()
    root: Dict[str, Any] = {"kind": "Module", "body": []}
    # Each stack frame: {kind: 'Block', body: list, pending_else: Optional[If]}
    stack: List[Dict[str, Any]] = [{"kind": "Block", "body": []}]

    # Simple state to support attaching else after closing an if-body
    last_if_for_else: Optional[Dict[str, Any]] = None

    func_re = re.compile(r"^\s*(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_$][\w$]*)\s*\(([^)]*)\)\s*\{\s*$")
    arrow_re = re.compile(r"^\s*const\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s+)?\(([^)]*)\)\s*=>\s*\{\s*$")
    if_re = re.compile(r"^\s*if\s*\((.*)\)\s*\{\s*$")
    else_re = re.compile(r"^\s*else\s*\{\s*$")
    for_of_re = re.compile(r"^\s*for\s*\(\s*(?:const|let|var)\s+([^\s;]+)\s+of\s+(.*)\)\s*\{\s*$")
    for_in_re = re.compile(r"^\s*for\s*\(\s*(?:const|let|var)\s+([^\s;]+)\s+in\s+(.*)\)\s*\{\s*$")
    for_c_re = re.compile(r"^\s*for\s*\((.*);(.*);(.*)\)\s*\{\s*$")
    while_re = re.compile(r"^\s*while\s*\((.*)\)\s*\{\s*$")
    ret_re = re.compile(r"^\s*return(?:\s+(.*?))?;\s*$")
    aug_re = re.compile(r"^\s*([A-Za-z_$][\w$\.\[\]]*)\s*(\+=|-=|\*=|/=|%=|\^=|\|=|&=|<<=|>>=)\s*(.*);\s*$")
    assign_re = re.compile(r"^\s*(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(.*);\s*$|^\s*([A-Za-z_$][\w$\.\[\]]*)\s*=\s*(.*);\s*$")

    for idx, raw in enumerate(lines, start=1):
        line = raw.rstrip()
        # Block openers
        m = func_re.match(line) or arrow_re.match(line)
        if m:
            name = _clean(m.group(1))
            args = [a.strip() for a in _clean(m.group(2)).split(',') if a.strip()]
            fn: Dict[str, Any] = {
                "kind": "FunctionDef",
                "summary": f"function {name}({', '.join(args)})",
                "line": idx,
                "name": name,
                "args": args,
                "body": [],
            }
            _append_stmt(stack, fn)
            stack.append({"kind": "Block", "body": fn["body"]})
            last_if_for_else = None
            continue

        m = if_re.match(line)
        if m:
            test = _clean(m.group(1))
            node: Dict[str, Any] = {
                "kind": "If",
                "summary": "if-statement",
                "line": idx,
                "test": test,
                "body": [],
                "orelse": [],
            }
            _append_stmt(stack, node)
            stack.append({"kind": "Block", "body": node["body"]})
            last_if_for_else = node
            continue

        if else_re.match(line):
            # else must attach to the most recent If without orelse
            if last_if_for_else is not None:
                # Start collecting else body into a fresh block hooked to orelse
                else_body: List[Dict[str, Any]] = []
                last_if_for_else["orelse"] = else_body
                stack.append({"kind": "Block", "body": else_body})
                # do not clear last_if_for_else yet; closing brace will end
                continue

        m = for_of_re.match(line) or for_in_re.match(line)
        if m:
            target = _clean(m.group(1))
            iter_expr = _clean(m.group(2))
            node = {
                "kind": "For",
                "summary": "for-loop",
                "line": idx,
                "target": target,
                "iter": iter_expr,
                "body": [],
                "orelse": [],
            }
            _append_stmt(stack, node)
            stack.append({"kind": "Block", "body": node["body"]})
            last_if_for_else = None
            continue

        m = for_c_re.match(line)
        if m:
            cond = _clean(m.group(2))
            node = {
                "kind": "For",
                "summary": f"for ({_clean(m.group(1))}; {cond}; {_clean(m.group(3))})",
                "line": idx,
                "target": "",
                "iter": cond or "(cond)",
                "body": [],
                "orelse": [],
            }
            _append_stmt(stack, node)
            stack.append({"kind": "Block", "body": node["body"]})
            last_if_for_else = None
            continue

        m = while_re.match(line)
        if m:
            test = _clean(m.group(1))
            node = {
                "kind": "While",
                "summary": "while-loop",
                "line": idx,
                "test": test,
                "body": [],
                "orelse": [],
            }
            _append_stmt(stack, node)
            stack.append({"kind": "Block", "body": node["body"]})
            last_if_for_else = None
            continue

        # Block closer
        if line.strip().endswith('}'):
            if len(stack) > 1:
                stack.pop()
            # after closing any block, else should not attach further
            last_if_for_else = None
            continue

        m = ret_re.match(line)
        if m:
            value = _clean(m.group(1)) if m.group(1) is not None else None
            _append_stmt(stack, {"kind": "Return", "summary": "return", "line": idx, "value": value})
            last_if_for_else = None
            continue

        m = aug_re.match(line)
        if m:
            _append_stmt(stack, {
                "kind": "AugAssign",
                "summary": "aug-assign",
                "line": idx,
                "target": _clean(m.group(1)),
                "op": {"+=":"Add","-=":"Sub","*=":"Mult","/=":"Div","%=":"Mod","^=":"BitXor","|=":"BitOr","&=":"BitAnd","<<=":"LShift",">> =":"RShift"}.get(m.group(2), m.group(2)),
                "value": _clean(m.group(3)),
            })
            last_if_for_else = None
            continue

        m = assign_re.match(line)
        if m:
            name = m.group(1) or m.group(3)
            val  = m.group(2) or m.group(4)
            _append_stmt(stack, {"kind": "Assign", "summary": f"assign {name}", "line": idx, "targets": [ _clean(name) ], "value": _clean(val)})
            last_if_for_else = None
            continue

        # Bare call like console.log(x);
        if re.match(r"^\s*[A-Za-z_$][\w$\.]*\s*\(.*\)\s*;\s*$", line):
            _append_stmt(stack, {"kind": "Call", "summary": "call", "line": idx})
            last_if_for_else = None
            continue

        # ignore other lines

    # move built body to root
    root["body"] = stack[0]["body"]
    return root


