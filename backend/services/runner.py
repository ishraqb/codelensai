# backend/services/runner.py
from __future__ import annotations
import subprocess
import sys
import tempfile
from typing import Dict

PYTHON_BIN = sys.executable  # use venv python

def run_python(code: str, timeout_sec: int = 3, postlude: str = "") -> Dict[str, str | int]:
    """
    Run user code with an optional 'postlude' appended (e.g., print(two_sum(...))).
    """
    full_code = code.rstrip()
    if postlude.strip():
        full_code += "\n\n" + postlude.strip() + "\n"

    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(full_code)
        f.flush()
        path = f.name

    try:
        proc = subprocess.run(
            [PYTHON_BIN, path],
            capture_output=True,
            text=True,
            timeout=timeout_sec,
        )
        return {
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "exit_code": proc.returncode,
        }
    except subprocess.TimeoutExpired as e:
        return {
            "stdout": e.stdout or "",
            "stderr": (e.stderr or "") + "\n[Timeout] Execution exceeded limit.",
            "exit_code": 124,
        }
    except Exception as e:
        return {
            "stdout": "",
            "stderr": f"[Runner error] {e}",
            "exit_code": 1,
        }

