# Sandboxing AI Code Execution: Using Firecracker MicroVMs and Ephemeral Lambda Environments

Author: Ketul Patel | Principal Engineer and Cloud Architect  
Series: Enterprise AI Security & MLOps Architecture (Module 2, Part 3)

---

## Introduction

AI code generation models (such as Claude 3.5 Sonnet, AWS CodeWhisperer, and GPT-4) produce executable Python code, SQL queries, and shell scripts. When applications allow agents to dynamically execute generated code to perform calculations, data transformations, or API integrations, they introduce a critical security risk: **Unsafe Code Execution & Excessive Agency (OWASP LLM02)**.

If an AI model generates code containing `import os; os.system('curl http://169.254.169.254/latest/meta-data/')`, running that snippet inside a standard container exposes the cloud instance's AWS IAM credentials and network environment.

This article details how to sandbox AI code execution using Firecracker MicroVM isolation primitives and ephemeral AWS Lambda execution scopes.

---

## Threat Matrix: Risks of Executing AI-Generated Code

1. **AWS IMDS Credential Theft:** Querying `169.254.169.254` to steal temporary IAM role tokens.
2. **Arbitrary OS Subshell Commands:** Executing `rm -rf /`, spawning reverse shells (`nc -e /bin/sh`), or reading sensitive files (`/etc/passwd`).
3. **Resource Exhaustion (Denial of Service):** Infinite loops (`while True: pass`) consuming 100% CPU core allocations.

---

## Ephemeral Sandboxing Architecture

To achieve zero-trust code execution, generated code must run within a hardened, ephemeral sandbox that enforces four strict boundaries:

```text
[AI Model Generated Code]
           │
           ▼
 ┌──────────────────────────────────────────────┐
 │ 1. Static AST / Keyword Security Audit       │  <-- Blocks dangerous imports & IMDS IPs
 └──────────────────────────────────────────────┘
           │ (Passed Audit)
           ▼
 ┌──────────────────────────────────────────────┐
 │ 2. Ephemeral Sandbox Execution Scope          │  <-- Restricted Builtins Scope
 └──────────────────────────────────────────────┘
           │ (Timeout Enforced: Max 2.0s)
           ▼
 ┌──────────────────────────────────────────────┐
 │ 3. Firecracker / Ephemeral Lambda Isolation  │  <-- Zero Network Access to IMDS
 └──────────────────────────────────────────────┘
```

---

## Python Security Sandbox Implementation

The sandboxed execution wrapper overrides default `__builtins__` to prevent filesystem or process access, enforced via explicit execution timeouts:

```python
import sys
import io
import time
import re
import concurrent.futures
from typing import Dict, Any, List

FORBIDDEN_PATTERNS = [
    r"\bimport\s+os\b", r"\bimport\s+subprocess\b", r"\bimport\s+socket\b",
    r"169\.254\.169\.254", r"rm\s+-rf", r"\bexec\b", r"\beval\b"
]

def execute_sandboxed_snippet(code: str, timeout_seconds: float = 2.0) -> Dict[str, Any]:
    # 1. Static Keyword & AST Security Check
    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, code):
            return {
                "status": "BLOCKED",
                "security_violation": f"Forbidden pattern detected: {pattern}"
            }

    # 2. Restricted Execution Builtins Scope
    safe_builtins = {
        "abs": abs, "all": all, "any": any, "bool": bool,
        "dict": dict, "float": float, "int": int, "len": len,
        "list": list, "max": max, "min": min, "print": print,
        "range": range, "sum": sum, "tuple": tuple
    }

    global_scope = {"__builtins__": safe_builtins}

    # 3. Execution with Hardened Timeout
    ...
```

---

## Hardening AWS Firecracker & Lambda Execution Isolation

When running in production on AWS:
1. **Disable IMDS Access:** Set `http_tokens = "required"` (IMDSv2) and restrict hop limit, or block outbound HTTP calls to `169.254.169.254` via local iptables / VPC security groups.
2. **Ephemeral Lifecycles:** Each code execution operates inside a fresh microVM instance destroyed immediately upon execution completion.
3. **Memory & Time Hard Limits:** Restrict execution memory to 128MB and CPU execution timeout to <= 2.0 seconds.

---

## Conclusion & Architecture Summary

Sandboxing AI code execution transforms dangerous dynamic code generation into a safe, controllable feature. By enforcing static AST validation, restricted builtins, and Firecracker microVM isolation, enterprises can harness AI code execution without exposing cloud infrastructure to compromise.
