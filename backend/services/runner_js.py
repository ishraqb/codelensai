from __future__ import annotations
import os
import shutil
import subprocess
import sys
import tempfile
from typing import Dict


def _run_cmd(cmd: list[str], timeout_sec: int) -> Dict[str, str | int]:
    try:
        proc = subprocess.run(
            cmd,
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


def run_javascript(code: str, timeout_sec: int = 3, postlude: str = "") -> Dict[str, str | int]:
    node = shutil.which("node")
    if not node:
        return {"stdout": "", "stderr": "Node.js not found in PATH.", "exit_code": 127}

    full_code = code.rstrip()
    if postlude.strip():
        full_code += "\n\n" + postlude.strip() + "\n"

    path = None
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
            f.write(full_code)
            f.flush()
            path = f.name
        return _run_cmd([node, path], timeout_sec)
    finally:
        if path and os.path.exists(path):
            try:
                os.unlink(path)
            except Exception:
                pass


def run_typescript(code: str, timeout_sec: int = 3, postlude: str = "") -> Dict[str, str | int]:
    tsnode = shutil.which("ts-node") or shutil.which("tsx")
    if not tsnode:
        return {
            "stdout": "",
            "stderr": "TypeScript execution requires 'ts-node' or 'tsx' installed globally.",
            "exit_code": 127,
        }

    full_code = code.rstrip()
    if postlude.strip():
        full_code += "\n\n" + postlude.strip() + "\n"

    path = None
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".ts", delete=False) as f:
            f.write(full_code)
            f.flush()
            path = f.name
        return _run_cmd([tsnode, path], timeout_sec)
    finally:
        if path and os.path.exists(path):
            try:
                os.unlink(path)
            except Exception:
                pass


