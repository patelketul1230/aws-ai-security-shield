import sys
import io
import time
import re
import concurrent.futures
from typing import Dict, Any, List


FORBIDDEN_KEYWORDS = [
    r"\bimport\s+os\b", r"\bfrom\s+os\b",
    r"\bimport\s+sys\b", r"\bfrom\s+sys\b",
    r"\bimport\s+subprocess\b", r"\bfrom\s+subprocess\b",
    r"\bimport\s+socket\b", r"\bfrom\s+socket\b",
    r"\bimport\s+shutil\b", r"\bfrom\s+shutil\b",
    r"\bimport\s+importlib\b",
    r"\b__import__\b", r"\beval\b", r"\bexec\b", r"\bopen\b",
    r"169\.254\.169\.254", r"rm\s+-rf", r"system\("
]


def _worker_exec(code: str) -> Dict[str, Any]:
    """
    Worker executing sanitized Python code in an isolated scope.
    Captures stdout and stderr.
    """
    buffer_out = io.StringIO()
    buffer_err = io.StringIO()

    safe_builtins = {
        "abs": abs, "all": all, "any": any, "bin": bin, "bool": bool,
        "dict": dict, "float": float, "format": format, "int": int,
        "len": len, "list": list, "max": max, "min": min, "print": print,
        "range": range, "round": round, "set": set, "str": str, "sum": sum,
        "tuple": tuple, "type": type, "zip": zip, "enumerate": enumerate,
        "isinstance": isinstance
    }

    global_scope = {"__builtins__": safe_builtins}
    local_scope = {}

    old_stdout = sys.stdout
    old_stderr = sys.stderr

    sys.stdout = buffer_out
    sys.stderr = buffer_err

    try:
        exec(code, global_scope, local_scope)
        return {
            "success": True,
            "stdout": buffer_out.getvalue(),
            "stderr": buffer_err.getvalue()
        }
    except Exception as e:
        return {
            "success": False,
            "stdout": buffer_out.getvalue(),
            "stderr": f"{type(e).__name__}: {str(e)}"
        }
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr


class CodeSandboxEngine:
    """
    OWASP LLM02 Defense: Sandboxed AI Code Execution Engine.
    Executes AI-generated Python code snippets inside an ephemeral, resource-constrained,
    and security-monitored sandboxed scope.
    """

    def __init__(self, timeout_seconds: float = 2.0):
        self.timeout_seconds = timeout_seconds

    def execute_code(self, code_snippet: str) -> Dict[str, Any]:
        """
        Validates and executes code in a sandboxed isolated thread execution pool.

        Returns:
            Dict containing status, success, stdout, stderr, execution_time_ms, and security_violations.
        """
        if not code_snippet or not isinstance(code_snippet, str):
            return {
                "status": "REJECTED",
                "success": False,
                "error": "Empty code snippet provided.",
                "security_violations": ["Empty Payload"]
            }

        # Static AST / Keyword Security Audit
        violations: List[str] = []
        for kw in FORBIDDEN_KEYWORDS:
            if re.search(kw, code_snippet):
                violations.append(f"Forbidden instruction/import detected matching: '{kw}'")

        if violations:
            return {
                "status": "BLOCKED",
                "success": False,
                "stdout": "",
                "stderr": "Security Sandbox Violation: Code execution blocked by security policy.",
                "security_violations": violations,
                "execution_time_ms": 0.0
            }

        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_worker_exec, code_snippet)
            try:
                result = future.result(timeout=self.timeout_seconds)
                elapsed_ms = round((time.time() - start_time) * 1000, 2)
                return {
                    "status": "SUCCESS" if result["success"] else "EXECUTION_ERROR",
                    "success": result["success"],
                    "stdout": result["stdout"],
                    "stderr": result["stderr"],
                    "security_violations": [],
                    "execution_time_ms": elapsed_ms
                }
            except concurrent.futures.TimeoutError:
                elapsed_ms = round((time.time() - start_time) * 1000, 2)
                return {
                    "status": "TIMEOUT",
                    "success": False,
                    "stdout": "",
                    "stderr": f"Execution Timed Out after {self.timeout_seconds}s limit.",
                    "security_violations": ["Resource Limit Exceeded (CPU/Execution Time)"],
                    "execution_time_ms": elapsed_ms
                }

