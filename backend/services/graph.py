# backend/services/graph.py
from typing import Any, Dict, List, Tuple


def ir_to_mermaid(ir: Dict[str, Any]) -> str:
    """
    Convert our IR (from parser.parse_python_to_ir) into a Mermaid flowchart.

    Supported IR 'kind' values:
      - FunctionDef { name, args, body }
      - If { test, body, orelse [, elif=True] }   # elif appears as an If in orelse with 'elif': True
      - For { target, iter, body, orelse }
      - While { test, body, orelse }
      - Assign { targets: [..], value }
      - AugAssign { target, op, value }
      - Return { value }
      - (fallback) any node with 'summary'

    Design:
      - Conditions are diamonds.
      - Each function body is wrapped in a subgraph.
      - No cross-linking between top-level functions.
      - A single merge node is used per if/elif/else chain.
    """
    lines: List[str] = ["flowchart TD"]
    counter = {"n": 0}

    def _nid(prefix: str = "n") -> str:
        counter["n"] += 1
        return f"{prefix}{counter['n']}"

    def _sanitize(label: str) -> str:
        # keep mermaid happy
        return (
            str(label)
            .replace('"', '\\"')
            .replace("[", "(")
            .replace("]", ")")
            .replace("{", "(")
            .replace("}", ")")
        )

    def add_node(label: str, shape: str = "rect") -> str:
        node = _nid()
        safe = _sanitize(label)
        if shape == "diamond":
            lines.append(f'  {node}{{"{safe}"}}')
        else:
            lines.append(f'  {node}["{safe}"]')
        return node

    def add_edge(a: str, b: str, lbl: str = "") -> None:
        lines.append(f"  {a} --|{lbl}|--> {b}" if lbl else f"  {a} --> {b}")

    def walk_block(stmts: List[Dict[str, Any]], *, top_level: bool = False) -> Tuple[str, str]:
        """
        Returns (first_node_id, last_node_id) for the emitted chunk.
        If top_level=True, we do not chain siblings when both are FunctionDef.
        """
        first = last = None
        prev: str | None = None

        for s in stmts:
            k = s.get("kind")
            node: str | None = None

            # -------- Function --------
            if k == "FunctionDef":
                header = add_node(f"def {s.get('name')}({', '.join(s.get('args', []))})")
                body_first, body_last = walk_block(s.get("body", []), top_level=False)
                if body_first:
                    lines.append(f"  subgraph {s.get('name')}_body")
                    add_edge(header, body_first)
                    lines.append("  end")
                    node = body_last or body_first
                else:
                    node = header

                # do NOT chain top-level functions together
                if not top_level and prev:
                    add_edge(prev, node)
                first = first or node
                prev = None  # break the chain at top level between functions
                last = node
                continue

            # -------- If / Elif / Else (single merge) --------
            if k == "If":
                cond = add_node(f"If {s.get('test')}", shape="diamond")
                then_first, then_last = walk_block(s.get("body", []))
                merge = add_node("merge")

                if then_first:
                    add_edge(cond, then_first, "true")
                if then_last:
                    add_edge(then_last, merge)

                # orelse might begin with an elif If-node marked by 'elif': True
                else_nodes = s.get("orelse", [])
                elif_chain = (
                    len(else_nodes) == 1
                    and isinstance(else_nodes[0], dict)
                    and else_nodes[0].get("kind") == "If"
                    and else_nodes[0].get("elif")
                )

                if elif_chain:
                    el = else_nodes[0]
                    elif_cond = add_node(f"Elif {el.get('test')}", shape="diamond")
                    add_edge(cond, elif_cond, "false")
                    e_then_first, e_then_last = walk_block(el.get("body", []))
                    if e_then_first:
                        add_edge(elif_cond, e_then_first, "true")
                    if e_then_last:
                        add_edge(e_then_last, merge)

                    # possible trailing else of that elif
                    trailing = el.get("orelse", [])
                    if trailing:
                        t_first, t_last = walk_block(trailing)
                        if t_first:
                            add_edge(elif_cond, t_first, "false")
                        if t_last:
                            add_edge(t_last, merge)
                else:
                    # plain else block
                    e_first, e_last = walk_block(else_nodes)
                    if e_first:
                        add_edge(cond, e_first, "false")
                    if e_last:
                        add_edge(e_last, merge)

                node = merge

            # -------- For --------
            elif k == "For":
                head = add_node(f"For {s.get('target')} in {s.get('iter')}", shape="diamond")
                b_first, b_last = walk_block(s.get("body", []))
                if b_first:
                    add_edge(head, b_first, "yes")
                    add_edge(b_last or b_first, head)  # loop back
                after = add_node("after for")
                add_edge(head, after, "no")
                node = after

            # -------- While --------
            elif k == "While":
                head = add_node(f"While {s.get('test')}", shape="diamond")
                b_first, b_last = walk_block(s.get("body", []))
                if b_first:
                    add_edge(head, b_first, "yes")
                    add_edge(b_last or b_first, head)  # loop back
                after = add_node("after while")
                add_edge(head, after, "no")
                node = after

            # -------- Assign / AugAssign / Return --------
            elif k == "Assign":
                node = add_node(f"Assign {s.get('targets', [])} = {s.get('value')}")
            elif k == "AugAssign":
                node = add_node(f"{s.get('target')} {s.get('op','Add')}= {s.get('value')}")
            elif k == "Return":
                node = add_node(f"Return {s.get('value')}")

            # -------- Fallback --------
            else:
                node = add_node(s.get("summary", k))

            # normal chaining (except between top-level functions handled above)
            if prev:
                add_edge(prev, node)
            first = first or node
            prev = last = node

        return first or "", last or ""

    # kick off at module level
    walk_block(ir.get("body", []), top_level=True)
    return "\n".join(lines)
