import pytest
from src.sandbox.code_execution_engine import CodeSandboxEngine


@pytest.fixture
def sandbox():
    return CodeSandboxEngine(timeout_seconds=2.0)


def test_safe_math_execution(sandbox):
    code = "numbers = [1, 2, 3, 4, 5]\nprint('Sum:', sum(numbers))"
    res = sandbox.execute_code(code)
    assert res["status"] == "SUCCESS"
    assert res["success"] is True
    assert "Sum: 15" in res["stdout"]
    assert len(res["security_violations"]) == 0


def test_forbidden_os_import_blocked(sandbox):
    code = "import os\nos.system('ls -la')"
    res = sandbox.execute_code(code)
    assert res["status"] == "BLOCKED"
    assert res["success"] is False
    assert len(res["security_violations"]) > 0


def test_forbidden_eval_exec_blocked(sandbox):
    code = "eval('__import__(\"os\").system(\"whoami\")')"
    res = sandbox.execute_code(code)
    assert res["status"] == "BLOCKED"
    assert res["success"] is False


def test_imds_metadata_blocked(sandbox):
    code = "url = 'http://169.254.169.254/latest/meta-data/'"
    res = sandbox.execute_code(code)
    assert res["status"] == "BLOCKED"
    assert res["success"] is False
