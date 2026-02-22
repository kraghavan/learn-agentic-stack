# 🔍 Code Review Pipeline

> **Project 3.2** from the Agentic AI Learning Pathway
> Three-agent system with parallel execution

## Overview

A multi-agent code review system that mimics how a real code review works:

1. **Analyzer** - Reviews code quality and logic
2. **Security Scanner** - Finds vulnerabilities
3. **Review Writer** - Synthesizes into actionable review

**New concept:** Parallel execution! Analyzer and Security run simultaneously.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                   CODE REVIEW PIPELINE                          │
│                                                                 │
│   Code Input                                                    │
│       │                                                         │
│       ├──────────────┬──────────────┐                          │
│       │              │              │  (parallel)               │
│       ▼              ▼              │                          │
│  ┌─────────┐    ┌─────────┐        │                          │
│  │🔬Analyzer│    │🛡️Security│        │                          │
│  │         │    │ Scanner │        │                          │
│  │- Logic  │    │- CVEs   │        │                          │
│  │- Smells │    │- Secrets│        │                          │
│  │- Quality│    │- Vulns  │        │                          │
│  └────┬────┘    └────┬────┘        │                          │
│       │              │              │                          │
│       └──────┬───────┘              │                          │
│              │ (handoffs)           │                          │
│              ▼                      │                          │
│       ┌─────────────┐               │                          │
│       │ ✍️ Review    │               │                          │
│       │   Writer    │               │                          │
│       │             │               │                          │
│       │- Synthesize │               │                          │
│       │- Comments   │               │                          │
│       │- Actions    │               │                          │
│       └──────┬──────┘               │                          │
│              │                      │                          │
│              ▼                      │                          │
│       📝 Final Review               │                          │
└─────────────────────────────────────────────────────────────────┘
```

## Features

- [x] Three specialized agents
- [x] Parallel execution (Analyzer + Security)
- [x] Structured JSON handoffs
- [x] Inline code comments
- [x] Security vulnerability detection (CWE references)
- [x] Severity scoring
- [x] Action items generation
- [x] Sample vulnerable code included

## Quick Start

### Step 1: Create Project Structure

```bash
cd ~/learn-agentic-stack/claude-code-labs/02-agent-handshakes
mkdir -p code-review
cd code-review
```

### Step 2: Copy Files

```
code-review/
├── review_orchestrator.py   → review_orchestrator.py
├── review_app.py            → review_app.py
├── requirements.txt         ← review_requirements.txt
├── Dockerfile               ← review_Dockerfile
├── docker-compose.yml       ← review_docker_compose.yml
└── README.md
```

### Step 3: Run Locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export ANTHROPIC_API_KEY="your-key"
streamlit run review_app.py
```

### Step 4: Or Use Docker

```bash
export ANTHROPIC_API_KEY="your-key"
docker-compose up --build
```

Open http://localhost:8501

---

## Sample Code Included

Click "📋 Load Sample" to test with intentionally vulnerable code:

```python
API_KEY = "sk-1234567890abcdef"  # Hardcoded secret!

def get_user(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"  # SQL injection!
    cursor.execute(query)

def save_file(filename, content):
    path = "/uploads/" + filename  # Path traversal risk!
    with open(path, 'w') as f:
        f.write(content)
```

The pipeline will catch:
- 🔴 SQL injection (CWE-89)
- 🔴 Hardcoded credentials (CWE-798)
- 🟠 Path traversal (CWE-22)
- 🟡 Code complexity issues

---

## Agent Details

### 🔬 Code Analyzer

**Purpose:** Code quality and logic analysis

**Outputs:**
```json
{
  "logic_issues": [{"line": 10, "severity": "high", "issue": "..."}],
  "code_smells": [...],
  "best_practices": [...],
  "complexity_score": 6,
  "maintainability_score": 7
}
```

### 🛡️ Security Scanner

**Purpose:** Vulnerability detection

**Outputs:**
```json
{
  "vulnerabilities": [
    {"line": 15, "severity": "critical", "cwe": "CWE-89", "issue": "SQL Injection"}
  ],
  "sensitive_data": [{"line": 3, "type": "api_key", "issue": "Hardcoded key"}],
  "security_score": 4,
  "critical_count": 1,
  "high_count": 2
}
```

### ✍️ Review Writer

**Purpose:** Synthesize findings into actionable review

**Receives:** Both Analyzer and Security outputs

**Outputs:**
```json
{
  "summary": "Code has critical security issues...",
  "overall_score": 4,
  "recommendation": "request_changes",
  "inline_comments": [
    {"line": 15, "type": "security", "comment": "⚠️ SQL injection - use parameterized queries"}
  ],
  "action_items": ["Fix SQL injection", "Remove hardcoded key"],
  "positive_feedback": ["Good function naming"]
}
```

---

## Parallel Execution

```python
# Sequential (slower):
analyzer_result = run_analyzer(code)      # 2s
security_result = run_security(code)      # 2s
review = run_reviewer(analyzer_result, security_result)  # 2s
# Total: 6s

# Parallel (faster):
with ThreadPoolExecutor(max_workers=2) as executor:
    analyzer_future = executor.submit(run_analyzer, code)    # 2s ─┐
    security_future = executor.submit(run_security, code)    # 2s ─┤ parallel
    analyzer_result = analyzer_future.result()               #     │
    security_result = security_future.result()               #   ──┘
review = run_reviewer(analyzer_result, security_result)      # 2s
# Total: 4s (saved 2s!)
```

### When Can Agents Run in Parallel?

✅ **Yes** - When they don't depend on each other's output
- Analyzer doesn't need Security results
- Security doesn't need Analyzer results
- Both only need the original code

❌ **No** - When one needs another's output
- Reviewer needs BOTH Analyzer and Security results
- Must wait for both to complete

---

## UI Features

### Pipeline Visualization
```
📄 Code  →  🔬 Analyzer  →  🛡️ Security  →  ✍️ Reviewer
   ✓           ✓              ⏳
```

### Tabs
- **Full Review** - Markdown formatted review
- **Inline Comments** - Code with line-by-line comments
- **Analysis** - Detailed quality findings
- **Security** - Vulnerability details with CWE
- **Metrics** - Token usage and timing

---

## Learning Outcomes

- ✅ Multi-agent with 3+ agents
- ✅ Parallel vs sequential execution
- ✅ Multiple handoff patterns (fan-in)
- ✅ Code analysis prompts
- ✅ Security scanning patterns
- ✅ CWE/OWASP references

---

## Key Patterns

### Fan-Out, Fan-In Pattern

```
        ┌─── Agent A ───┐
Input ──┤               ├──▶ Agent C ──▶ Output
        └─── Agent B ───┘

- Input goes to A and B (fan-out)
- C waits for both (fan-in)
```

### Parallel Execution

```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=2) as executor:
    future_a = executor.submit(agent_a, input)
    future_b = executor.submit(agent_b, input)
    
    result_a = future_a.result()
    result_b = future_b.result()

# Both ran simultaneously!
result_c = agent_c(result_a, result_b)
```

---

## Extending the Project

Ideas for enhancement:

1. **Add Style Checker** - Formatting, linting suggestions
2. **Add Test Generator** - Suggest unit tests
3. **GitHub Integration** - Fetch PRs directly
4. **Batch Processing** - Review multiple files
5. **Learning Loop** - Remember project-specific patterns

---

## Comparison: 2 vs 3 Agents

| Project 3.1 | Project 3.2 |
|-------------|-------------|
| 2 agents | 3 agents |
| Sequential only | Parallel possible |
| Linear pipeline | Fan-out/fan-in |
| Research → Write | Analyze ⟨+⟩ Security → Review |

---

*Part of [learn-agentic-stack](https://github.com/kraghavan/learn-agentic-stack)*
