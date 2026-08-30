# AWS AI Security Shield Architecture Documentation

## System Topology & Security Architecture

The AWS AI Security Shield is an enterprise security gateway designed to protect generative AI applications against OWASP LLM Top 10 vulnerabilities. Built on AWS serverless primitives, it intercepts, inspects, and sanitizes both incoming prompts and outgoing LLM completions.

```mermaid
flowchart TD
    Client[User / Application Client] -->|HTTP POST Payload| APIGW[AWS API Gateway HTTP API]
    APIGW -->|Trigger| Lambda[AWS Lambda Security Proxy Handler]
    
    subgraph SecurityShield[AWS AI Security Shield Core Engine]
        Lambda -->|Step 1: Check LLM01| InjectionDetector[Prompt Injection Detector]
        Lambda -->|Step 2: Check LLM06| Redactor[Zero-Trust PII & Secret Redactor]
        Lambda -->|Step 3: Check LLM02| Sandbox[Ephemeral Code Sandbox Engine]
    end

    subgraph AWSBedrock[AWS Cloud Security Layer]
        Lambda -->|Step 4: Evaluate Policy| Guardrails[AWS Bedrock Guardrails]
    end

    subgraph Observability[Audit & Compliance]
        Lambda -->|Security Audit Logs| CloudWatch[AWS CloudWatch Log Group]
    end

    InjectionDetector -->|If Flagged| Block403[Return 403 Forbidden Response]
    Guardrails -->|If Intervened| BlockPolicy[Return 403 Policy Blocked Response]
    Redactor -->|Sanitized Text| LLM[Downstream Bedrock / Model Endpoint]
    Sandbox -->|Isolated Exec Output| Client
```

---

## Network & Inspection Flow Sequence Diagram

The sequence diagram below details the multi-layered evaluation pipeline for an incoming prompt payload:

```mermaid
sequenceDiagram
    autonumber
    actor User as Client Application
    participant APIGW as API Gateway
    participant Lambda as Lambda Security Handler
    participant Middleware as OWASP Security Engine
    participant Bedrock as AWS Bedrock Guardrails
    participant CW as CloudWatch Audit Logs

    User->>APIGW: POST /shield/inspect { prompt }
    APIGW->>Lambda: Invoke Event Bridge
    
    Lambda->>Middleware: 1. Prompt Injection Scan (Jailbreak / System Prompt Leak)
    alt Injection Detected
        Middleware-->>Lambda: Flagged (Risk Score >= 0.5)
        Lambda->>CW: Log Security Event (TYPE: PROMPT_INJECTION)
        Lambda-->>User: HTTP 403 Forbidden (Injection Attack Blocked)
    else Clean Prompt
        Middleware-->>Lambda: Passed Scan
    end

    Lambda->>Middleware: 2. Edge PII & Secret Redaction (AWS Keys, SSN, JWT)
    Middleware-->>Lambda: Sanitized Prompt Text ([REDACTED_AWS_KEY])

    Lambda->>Bedrock: 3. ApplyGuardrail API Call (Content & Topic Policy)
    alt Policy Violation
        Bedrock-->>Lambda: GUARDRAIL_INTERVENED
        Lambda->>CW: Log Security Event (TYPE: GUARDRAIL_VIOLATION)
        Lambda-->>User: HTTP 403 Forbidden (Policy Violation)
    else Policy Compliant
        Bedrock-->>Lambda: Policy Compliant (NONE)
    end

    Lambda->>CW: Log Audit Metadata (Duration, Redaction Count, Risk Score)
    Lambda-->>User: HTTP 200 OK (Sanitized Payload Ready for LLM)
```

---

## Ephemeral Code Execution Sandbox Architecture (OWASP LLM02 Defense)

When an AI model generates Python code snippets (e.g. data analysis or calculations), executing them directly on production application servers risks remote code execution (RCE) attacks or AWS IMDS metadata exfiltration (`169.254.169.254`).

```mermaid
flowchart LR
    AICode[AI Generated Code Snippet] --> AST[1. AST Static Audit]
    AST -->|Forbidden Imports / IMDS Found| Blocked[BLOCKED: Security Sandbox Violation]
    AST -->|Passed AST Audit| Scope[2. Restricted Builtin Scope]
    Scope --> ExecutionThread[3. Isolated Thread Exec w/ 2.0s Timeout]
    ExecutionThread -->|Timeout Exceeded or Exception| Terminated[KILLED: Hard CPU Limit]
    ExecutionThread -->|Successful Run| Output[4. Capture Stdout / Wipe Environment]
```

### 4-Stage Ephemeral Sandbox Pipeline:
1. **AST Static Code Audit**: Python's `ast` module parses code into an Abstract Syntax Tree before running. Blocks forbidden builtins (`eval`, `exec`, `open`, `__import__`) and system calls (`os.system`, `subprocess`).
2. **Restricted Builtin Scope**: Strips dangerous builtins from runtime memory (`exec(code, {'__builtins__': None})`).
3. **Hard CPU Execution Limit (2.0s)**: Worker thread enforces a 2-second timeout, killing infinite loops (`while True:`).
4. **Stateless Cleanup**: Captures `stdout`/`stderr` into temporary memory buffers (`io.StringIO`), returns the response, and immediately destroys the thread context.

---

## Component Details

### 1. API Gateway HTTP API
Provides edge-rate limiting, CORS configuration, and SSL termination with low overhead.

### 2. Lambda Proxy Handler
Executes lightweight Python security middleware in under 15ms per request.

### 3. Bedrock Guardrails Policy
Managed cloud-native policy layer enforcing topic exclusion, hate/insult/violence filters, and automated PII anonymization.

### 4. Ephemeral Sandbox Engine
Isolates AI-generated code execution inside restricted scopes without system call access or AWS IMDS metadata reachability.

---

## Security Shield Visual Interface Screenshots

| Vulnerability & Defense Domain | Interactive Web UI Result |
| :--- | :--- |
| **OWASP LLM01: Prompt Injection (Blocked)** | ![Prompt Injection Blocked](./assets/ui_prompt_injection_blocked.png) |
| **OWASP LLM01: Safe Prompt (Passed)** | ![Prompt Injection Passed](./assets/ui_prompt_injection_passed.png) |
| **OWASP LLM06: Zero-Trust Secret Redaction** | ![PII Secret Redaction](./assets/ui_pii_secret_redaction.png) |
| **OWASP LLM02: Malicious OS Code Exec (Blocked)** | ![Code Execution Blocked](./assets/ui_sandbox_execution_blocked.png) |
| **OWASP LLM02: Safe Math Execution (Passed)** | ![Code Execution Passed](./assets/ui_sandbox_execution_passed.png) |
| **AWS Bedrock Guardrails Policy Intervened** | ![Bedrock Policy Intervened](./assets/ui_bedrock_guardrail_policy.png) |
| **AWS Bedrock Console Guardrail Test** | ![AWS Bedrock Console Test](./assets/aws_bedrock_console_guardrail_test.png) |

