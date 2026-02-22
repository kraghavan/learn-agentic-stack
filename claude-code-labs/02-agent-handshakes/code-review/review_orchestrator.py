"""
Code Review Pipeline - Project 3.2
Three-agent system: Analyzer → Security Scanner → Review Writer
"""

import json
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor

from anthropic import Anthropic

claude = Anthropic()


# ============== HANDOFF SCHEMAS ==============

@dataclass
class AnalyzerFindings:
    """Output from Code Analyzer → other agents"""
    file_name: str
    language: str
    summary: str
    logic_issues: list[dict]  # {"line": int, "severity": str, "issue": str, "suggestion": str}
    code_smells: list[dict]
    best_practices: list[dict]
    complexity_score: int  # 1-10
    maintainability_score: int  # 1-10
    
    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)


@dataclass 
class SecurityFindings:
    """Output from Security Scanner → Review Writer"""
    vulnerabilities: list[dict]  # {"line": int, "severity": str, "cwe": str, "issue": str, "fix": str}
    sensitive_data: list[dict]  # {"line": int, "type": str, "issue": str}
    dependency_issues: list[str]
    security_score: int  # 1-10
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    
    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)


@dataclass
class CodeReview:
    """Final output from Review Writer"""
    summary: str
    overall_score: int  # 1-10
    recommendation: str  # "approve", "request_changes", "needs_discussion"
    inline_comments: list[dict]  # {"line": int, "type": str, "comment": str}
    action_items: list[str]
    positive_feedback: list[str]
    full_review: str  # Markdown formatted review
    
    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)


# ============== AGENT 1: CODE ANALYZER ==============

ANALYZER_SYSTEM = """You are a Code Analyzer Agent specialized in reviewing code quality and logic.

Your job is to:
1. Understand the code's purpose and structure
2. Identify logic issues and bugs
3. Spot code smells and anti-patterns
4. Evaluate complexity and maintainability
5. Suggest improvements

OUTPUT FORMAT:
Respond with ONLY a JSON object (no markdown, no explanation):
{
    "file_name": "filename.py",
    "language": "python",
    "summary": "Brief description of what the code does",
    "logic_issues": [
        {"line": 10, "severity": "high", "issue": "Potential null reference", "suggestion": "Add null check"}
    ],
    "code_smells": [
        {"line": 25, "severity": "medium", "issue": "Function too long", "suggestion": "Extract into smaller functions"}
    ],
    "best_practices": [
        {"line": 5, "severity": "low", "issue": "Magic number", "suggestion": "Use named constant"}
    ],
    "complexity_score": 6,
    "maintainability_score": 7
}

Severity levels: "critical", "high", "medium", "low", "info"
Scores are 1-10 (10 = best)"""


def run_analyzer(code: str, file_name: str = "code.py") -> tuple[AnalyzerFindings, dict]:
    """Run the Code Analyzer Agent."""
    
    prompt = f"""Analyze this code for quality and logic issues:

**File:** {file_name}

```
{code}
```

Provide a thorough code quality analysis."""

    response = claude.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        system=ANALYZER_SYSTEM,
        messages=[{"role": "user", "content": prompt}]
    )
    
    content = response.content[0].text
    
    try:
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        
        data = json.loads(content.strip())
        findings = AnalyzerFindings(**data)
    except (json.JSONDecodeError, TypeError) as e:
        findings = AnalyzerFindings(
            file_name=file_name,
            language="unknown",
            summary="Analysis parsing failed",
            logic_issues=[],
            code_smells=[],
            best_practices=[],
            complexity_score=5,
            maintainability_score=5
        )
    
    metadata = {
        "agent": "analyzer",
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
    }
    
    return findings, metadata


# ============== AGENT 2: SECURITY SCANNER ==============

SECURITY_SYSTEM = """You are a Security Scanner Agent specialized in finding vulnerabilities in code.

Your job is to:
1. Identify security vulnerabilities (injection, XSS, etc.)
2. Find sensitive data exposure (hardcoded secrets, PII)
3. Check for insecure patterns
4. Reference CWE/OWASP where applicable
5. Provide remediation guidance

OUTPUT FORMAT:
Respond with ONLY a JSON object (no markdown, no explanation):
{
    "vulnerabilities": [
        {"line": 15, "severity": "critical", "cwe": "CWE-89", "issue": "SQL Injection", "fix": "Use parameterized queries"}
    ],
    "sensitive_data": [
        {"line": 3, "type": "api_key", "issue": "Hardcoded API key found"}
    ],
    "dependency_issues": ["Outdated library X has known CVE"],
    "security_score": 4,
    "critical_count": 1,
    "high_count": 2,
    "medium_count": 1,
    "low_count": 3
}

Severity levels: "critical", "high", "medium", "low", "info"
Security score is 1-10 (10 = most secure)

Common issues to look for:
- SQL/NoSQL injection
- XSS vulnerabilities
- Command injection
- Path traversal
- Hardcoded credentials
- Insecure deserialization
- Missing input validation
- Weak cryptography"""


def run_security_scanner(code: str, file_name: str = "code.py") -> tuple[SecurityFindings, dict]:
    """Run the Security Scanner Agent."""
    
    prompt = f"""Scan this code for security vulnerabilities:

**File:** {file_name}

```
{code}
```

Identify all security issues, referencing CWE IDs where applicable."""

    response = claude.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        system=SECURITY_SYSTEM,
        messages=[{"role": "user", "content": prompt}]
    )
    
    content = response.content[0].text
    
    try:
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        
        data = json.loads(content.strip())
        findings = SecurityFindings(**data)
    except (json.JSONDecodeError, TypeError) as e:
        findings = SecurityFindings(
            vulnerabilities=[],
            sensitive_data=[],
            dependency_issues=[],
            security_score=5,
            critical_count=0,
            high_count=0,
            medium_count=0,
            low_count=0
        )
    
    metadata = {
        "agent": "security",
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
    }
    
    return findings, metadata


# ============== AGENT 3: REVIEW WRITER ==============

REVIEWER_SYSTEM = """You are a Code Review Writer Agent that synthesizes findings into a comprehensive review.

You receive:
1. Code analysis findings (logic, quality)
2. Security scan findings (vulnerabilities)

Your job is to:
1. Synthesize all findings into a coherent review
2. Prioritize issues by severity and impact
3. Write actionable inline comments
4. Provide clear recommendations
5. Include positive feedback where appropriate

OUTPUT FORMAT:
Respond with ONLY a JSON object (no markdown, no explanation):
{
    "summary": "Brief overall assessment of the code",
    "overall_score": 7,
    "recommendation": "request_changes",
    "inline_comments": [
        {"line": 10, "type": "issue", "comment": "Consider adding error handling here"},
        {"line": 25, "type": "security", "comment": "⚠️ SQL injection risk - use parameterized queries"},
        {"line": 5, "type": "suggestion", "comment": "Nice use of descriptive variable names! 👍"}
    ],
    "action_items": [
        "Fix critical SQL injection on line 25",
        "Add input validation for user data",
        "Consider extracting helper functions"
    ],
    "positive_feedback": [
        "Good code organization",
        "Clear function naming"
    ],
    "full_review": "## Code Review\\n\\n### Summary\\n...full markdown review..."
}

Recommendation options: "approve", "request_changes", "needs_discussion"
Comment types: "issue", "security", "suggestion", "praise", "question"
Overall score is 1-10 (10 = excellent)"""


def run_reviewer(
    code: str,
    analyzer_findings: AnalyzerFindings,
    security_findings: SecurityFindings,
    file_name: str = "code.py"
) -> tuple[CodeReview, dict]:
    """Run the Review Writer Agent."""
    
    prompt = f"""Write a comprehensive code review based on these findings:

## Code Being Reviewed
**File:** {file_name}
```
{code}
```

## Analysis Findings
{analyzer_findings.to_json()}

## Security Findings
{security_findings.to_json()}

Synthesize these into a helpful, actionable code review."""

    response = claude.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=3000,
        system=REVIEWER_SYSTEM,
        messages=[{"role": "user", "content": prompt}]
    )
    
    content = response.content[0].text
    
    try:
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        
        data = json.loads(content.strip())
        review = CodeReview(**data)
    except (json.JSONDecodeError, TypeError) as e:
        review = CodeReview(
            summary="Review generation failed",
            overall_score=5,
            recommendation="needs_discussion",
            inline_comments=[],
            action_items=[],
            positive_feedback=[],
            full_review=content
        )
    
    metadata = {
        "agent": "reviewer",
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
    }
    
    return review, metadata


# ============== ORCHESTRATOR ==============

def run_review_pipeline(
    code: str,
    file_name: str = "code.py",
    parallel: bool = True,
    on_stage_complete: callable = None
) -> dict:
    """
    Run the full code review pipeline.
    
    Args:
        code: The code to review
        file_name: Name of the file
        parallel: Run Analyzer and Security in parallel
        on_stage_complete: Callback after each stage
    
    Returns:
        {
            "analyzer_findings": AnalyzerFindings,
            "security_findings": SecurityFindings,
            "review": CodeReview,
            "metadata": {...}
        }
    """
    result = {
        "code": code,
        "file_name": file_name,
        "stages": [],
        "metadata": {
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "parallel_execution": parallel,
        }
    }
    
    # Stage 1 & 2: Analyzer and Security Scanner (can run in parallel)
    if parallel:
        with ThreadPoolExecutor(max_workers=2) as executor:
            analyzer_future = executor.submit(run_analyzer, code, file_name)
            security_future = executor.submit(run_security_scanner, code, file_name)
            
            analyzer_findings, analyzer_meta = analyzer_future.result()
            security_findings, security_meta = security_future.result()
    else:
        analyzer_findings, analyzer_meta = run_analyzer(code, file_name)
        if on_stage_complete:
            on_stage_complete("analyzer", analyzer_findings)
        
        security_findings, security_meta = run_security_scanner(code, file_name)
        if on_stage_complete:
            on_stage_complete("security", security_findings)
    
    result["analyzer_findings"] = analyzer_findings
    result["security_findings"] = security_findings
    result["stages"].extend([
        {"agent": "analyzer", "status": "complete", "metadata": analyzer_meta},
        {"agent": "security", "status": "complete", "metadata": security_meta},
    ])
    result["metadata"]["total_input_tokens"] += analyzer_meta["input_tokens"] + security_meta["input_tokens"]
    result["metadata"]["total_output_tokens"] += analyzer_meta["output_tokens"] + security_meta["output_tokens"]
    
    if on_stage_complete and parallel:
        on_stage_complete("analyzer", analyzer_findings)
        on_stage_complete("security", security_findings)
    
    # Stage 3: Review Writer (needs both previous outputs)
    review, reviewer_meta = run_reviewer(code, analyzer_findings, security_findings, file_name)
    
    result["review"] = review
    result["stages"].append({"agent": "reviewer", "status": "complete", "metadata": reviewer_meta})
    result["metadata"]["total_input_tokens"] += reviewer_meta["input_tokens"]
    result["metadata"]["total_output_tokens"] += reviewer_meta["output_tokens"]
    
    if on_stage_complete:
        on_stage_complete("reviewer", review)
    
    return result


# ============== SAMPLE CODE FOR TESTING ==============

SAMPLE_CODE = '''
import sqlite3
import os

API_KEY = "sk-1234567890abcdef"  # TODO: move to env

def get_user(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    query = f"SELECT * FROM users WHERE id = {user_id}"  # SQL injection!
    cursor.execute(query)
    return cursor.fetchone()

def process_data(data):
    result = []
    for i in range(len(data)):
        for j in range(len(data[i])):
            if data[i][j] > 0:
                result.append(data[i][j] * 2)
            else:
                result.append(0)
    return result

def save_file(filename, content):
    path = "/uploads/" + filename  # Path traversal risk
    with open(path, 'w') as f:
        f.write(content)
    return True

class UserManager:
    def __init__(self):
        self.users = []
        
    def add_user(self, name, email, password):
        # Storing plain text password!
        self.users.append({
            'name': name,
            'email': email, 
            'password': password
        })
'''


if __name__ == "__main__":
    # Test
    print("Running code review pipeline...")
    result = run_review_pipeline(SAMPLE_CODE, "example.py", parallel=True)
    
    print("\n=== ANALYZER FINDINGS ===")
    print(f"Complexity: {result['analyzer_findings'].complexity_score}/10")
    print(f"Issues found: {len(result['analyzer_findings'].logic_issues)}")
    
    print("\n=== SECURITY FINDINGS ===")
    print(f"Security score: {result['security_findings'].security_score}/10")
    print(f"Critical: {result['security_findings'].critical_count}")
    
    print("\n=== FINAL REVIEW ===")
    print(f"Recommendation: {result['review'].recommendation}")
    print(f"Overall score: {result['review'].overall_score}/10")
    
    print("\n=== FULL REVIEW ===")
    print(result['review'].full_review)
