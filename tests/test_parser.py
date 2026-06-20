"""Tests for the deterministic core (parser, explainer, graph, complexity).

These avoid the network entirely, so they're fast and reliable. Run them with
`python tests/test_parser.py` or `pytest`.
"""

import os
import sys

# Make the serverless `_lib` package importable from the repo root.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "api"))

from _lib import explainer, graph, parser, parser_js  # noqa: E402
from _lib.ai import estimate_complexity  # noqa: E402

TWO_SUM = """def two_sum(nums, target):
    seen = {}
    for i, x in enumerate(nums):
        if target - x in seen:
            return [seen[target - x], i]
        seen[x] = i
    return []"""


def test_python_parses_into_function_ir():
    ir = parser.parse_python_to_ir(TWO_SUM)
    assert ir["kind"] == "Module"
    fn = ir["body"][0]
    assert fn["kind"] == "FunctionDef"
    assert fn["name"] == "two_sum"
    assert fn["args"] == ["nums", "target"]


def test_explainer_describes_every_construct():
    ir = parser.parse_python_to_ir(TWO_SUM)
    text = " ".join(s["text"] for s in explainer.explain_ir(ir))
    assert "Define a function two_sum" in text
    assert "Loop over nums" in text
    assert "Return" in text


def test_graph_is_valid_mermaid_without_duplicate_edges():
    ir = parser.parse_python_to_ir(TWO_SUM)
    diagram = graph.ir_to_mermaid(ir)
    assert diagram.startswith("flowchart TD")
    edges = [ln for ln in diagram.splitlines() if "-->" in ln]
    assert len(edges) == len(set(edges)), "flowchart should not repeat edges"


def test_complexity_heuristic_scales_with_nesting():
    assert estimate_complexity(parser.parse_python_to_ir(TWO_SUM)).startswith("O(n)")
    nested = "def f(a):\n  for i in a:\n    for j in a:\n      print(i, j)"
    assert estimate_complexity(parser.parse_python_to_ir(nested)).startswith("O(n^2)")
    flat = "def f(a):\n  return a + 1"
    assert estimate_complexity(parser.parse_python_to_ir(flat)).startswith("O(1)")


def test_javascript_parser_handles_loops_and_returns():
    js = "function f(n) {\n  for (let i = 0; i < n; i++) {\n    console.log(i);\n  }\n  return n;\n}"
    ir = parser_js.parse_jsts_to_ir(js)
    fn = ir["body"][0]
    assert fn["kind"] == "FunctionDef" and fn["name"] == "f"
    kinds = [c["kind"] for c in fn["body"]]
    assert "For" in kinds and "Return" in kinds


if __name__ == "__main__":
    failures = 0
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"PASS {name}")
            except AssertionError as exc:
                failures += 1
                print(f"FAIL {name}: {exc}")
    sys.exit(1 if failures else 0)
