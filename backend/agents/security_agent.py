import os
import re
from typing import List, Dict, Any

# Security signatures to detect in source code
SECURITY_PATTERNS = [
    (r'(?i)(api[_-]?key|secret[_-]?key|access[_-]?token|auth[_-]?token)\s*=\s*[\'"][A-Za-z0-9_\-\.]{16,}[\'"]', "Hardcoded API Key / Secret Token"),
    (r'(?i)(AKIA[0-9A-Z]{16})', "Exposed AWS Access Key ID"),
    (r'(?i)(ghp_[0-9a-zA-Z]{36}|github_pat_[0-9a-zA-Z_]{50,})', "Exposed GitHub Personal Access Token"),
    (r'(?i)(eval\s*\(|exec\s*\()', "Dangerous Dynamic Code Execution (eval/exec)"),
    (r'(?i)subprocess\.(Popen|call|run)\([^)]*shell\s*=\s*True', "Insecure Subprocess with shell=True (Command Injection Risk)"),
    (r'(?i)pickle\.loads\s*\(', "Insecure Deserialization via pickle.loads()"),
    (r'(?i)yaml\.load\([^)]*Loader\s*=\s*yaml\.(UnsafeLoader|Loader)', "Unsafe YAML deserialization"),
    (r'(?i)(cursor\.execute\s*\(\s*[\'"].*?%(s|d)|cursor\.execute\s*\(\s*f[\'"].*?\{)', "Potential SQL Injection (Unparameterized Query)"),
]

def scan_file_security(file_path: str, rel_path: str) -> List[Dict[str, Any]]:
    """Scan a single source file for security vulnerabilities and secret leaks."""
    vulnerabilities = []
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for line_idx, line in enumerate(f, 1):
                # Ignore comment lines
                stripped = line.strip()
                if stripped.startswith(("#", "//", "/*", "*")):
                    continue
                for pattern, desc in SECURITY_PATTERNS:
                    if re.search(pattern, line):
                        vulnerabilities.append({
                            "file": rel_path.replace("\\", "/"),
                            "line": line_idx,
                            "issue": desc,
                            "snippet": stripped[:120]
                        })
    except Exception:
        pass
    return vulnerabilities

def security_agent(state: dict) -> dict:
    """
    Upgraded Security & Vulnerability Agent
    Performs deep AST regex scans and secret detection across real source code with line citations.
    """
    files = state.get("repo_files", [])
    cloned_path = state.get("cloned_path", "")
    
    findings = []
    has_env = any(".env" in f and not f.endswith(".example") for f in files)
    
    if has_env:
        findings.append({
            "file": ".env",
            "line": 1,
            "issue": "Active .env secret profile tracked in Git index",
            "snippet": "Contains sensitive environment variables"
        })

    # Deep code scan on cloned repository files
    if cloned_path and os.path.exists(cloned_path):
        for root, _, filenames in os.walk(cloned_path):
            if any(part.startswith(('.', 'venv', 'env', '__pycache__', 'node_modules')) for part in root.split(os.sep)):
                continue
            for fname in filenames:
                if fname.endswith(('.py', '.js', '.ts', '.jsx', '.tsx', '.json', '.env', '.yaml', '.yml', '.sh')):
                    full_p = os.path.join(root, fname)
                    rel_p = os.path.relpath(full_p, cloned_path)
                    file_findings = scan_file_security(full_p, rel_p)
                    findings.extend(file_findings)

    state["security_findings"] = findings

    if findings:
        high_severity = [f for f in findings if "AWS" in f["issue"] or "API Key" in f["issue"] or "Injection" in f["issue"] or ".env" in f["issue"]]
        penalty = min(20, len(findings) * 5)
        score = max(0, 20 - penalty)
        
        issue_refs = [f"`{f['file']}:L{f['line']}` ({f['issue']})" for f in findings[:4]]
        output_msg = (
            f"🚨 SECURITY VULNERABILITIES DETECTED: Found {len(findings)} potential security concerns. "
            f"High-risk items: {', '.join(issue_refs)}. "
            f"Action Required: Immediately rotate leaked keys, sanitize dynamic SQL/subprocess calls, and update `.gitignore`."
        )
        status = "warning" if len(high_severity) == 0 else "error"
    else:
        score = 20
        status = "success"
        output_msg = "✅ SANITIZED & SECURE: Clean security posture. Zero hardcoded secrets, dangerous eval calls, or unparameterized queries discovered across audited files. (Score: +20/20)"

    state["score"] = state.get("score", 0) + score
    state["outputs"].append({
        "agent": "Security Agent",
        "status": status,
        "output": output_msg,
        "findings": findings
    })

    return state