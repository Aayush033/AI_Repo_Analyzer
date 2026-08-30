import sys
import asyncio
import time
import shutil
import os

# Ensure UTF-8 output on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from agents.planner import planner_agent
from agents.repo_agent import repo_agent
from agents.runtime_agent import runtime_agent
from agents.ast_agent import ast_agent
from agents.security_agent import security_agent
from agents.jd_matcher_agent import jd_matcher_agent
from agents.behavioral_agent import behavioral_agent
from agents.analytics_agent import analytics_agent
from agents.docker_agent import docker_agent
from agents.cicd_agent import cicd_agent
from agents.deploy_agent import deploy_agent
from agents.verification_agent import verification_agent
from agents.summary_agent import summary_agent

from core.metrics import timer_start, timer_end
from core.memory import remember

async def run_workflow(requirement: str, repo_url: str, ws) -> dict:
    """
    Multi-Agent Orchestrator Pipeline
    Coordinates specialized tool agents, runs deterministic static & runtime checks,
    executes verification loop, and returns the complete executive audit deliverable.
    """
    print(f"\n--- 🚀 [ORCHESTRATOR] Starting Multi-Agent Audit Pipeline for {repo_url} ---")
    start = timer_start()

    state = {
        "requirement": requirement,
        "repo_url": repo_url,
        "tasks": [],
        "outputs": [],
        "score": 0,
        "repo_files": [],
        "cloned_path": "",
        "analytics_data": {},
        "security_findings": [],
        "ast_metrics": {},
        "verification_data": {},
        "executive_report": "",
        "mermaid_diagram": ""
    }

    try:
        await ws.send_json({"type": "log", "msg": "🚀 Orchestrator: Initializing agentic audit workflow..."})
    except Exception:
        pass

    # Step 1: Planner Agent
    try:
        state = planner_agent(state)
    except Exception:
        pass

    pipeline_agents = [
        ("repo", "Repository Explorer Agent", repo_agent, True),
        ("runtime", "Live Sandbox & Runtime Agent", runtime_agent, True),
        ("ast", "AST & Complexity Tool Agent", ast_agent, False),
        ("security", "Security & Vulnerability Agent", security_agent, False),
        ("jd_match", "Job & Rubric Matcher Agent", jd_matcher_agent, True),
        ("behavioral", "Behavioral & Git Hygiene Agent", behavioral_agent, True),
        ("analytics", "Code Analytics Agent", analytics_agent, False),
        ("docker", "Dockerization Agent", docker_agent, False),
        ("cicd", "CI/CD Pipeline Agent", cicd_agent, False),
        ("deploy", "Infrastructure & Deployment Agent", deploy_agent, False),
        ("verification", "Anti-Hallucination Verification Agent", verification_agent, False),
        ("summary", "Executive Report Synthesizer", summary_agent, True),
    ]

    try:
        for task_id, task_name, agent_func, is_async in pipeline_agents:
            try:
                await ws.send_json({"type": "log", "msg": f"🤖 [{task_name}]: Executing..."})
                
                if is_async:
                    if task_id == "runtime":
                        state = await agent_func(state, ws)
                    else:
                        state = await agent_func(state)
                else:
                    state = agent_func(state)
                    
                await ws.send_json({"type": "log", "msg": f"✅ [{task_name}]: Complete."})
            except Exception as e:
                print(f"[ORCHESTRATOR FAULT] Error in {task_name}: {e}")
                await ws.send_json({"type": "log", "msg": f"⚠️ [{task_name}] Encountered issue: {str(e)}"})
                state["outputs"].append({
                    "agent": task_name,
                    "status": "warning",
                    "output": f"Sub-agent warning: {str(e)}"
                })
            
            await asyncio.sleep(0.05)

    finally:
        # Secure cleanup: Remove temporary sandbox directory
        cloned_p = state.get("cloned_path", "")
        if cloned_p and os.path.exists(cloned_p):
            shutil.rmtree(cloned_p, ignore_errors=True)

    runtime_seconds = timer_end(start)
    try:
        remember("last_run", repo_url)
    except Exception:
        pass

    print(f"--- 🏁 [ORCHESTRATOR] Audit Complete. Score: {state.get('score', 0)}/100 | Runtime: {runtime_seconds}s ---")

    return {
        "tasks": [t[0] for t in pipeline_agents],
        "score": state.get("score", 0),
        "runtime": runtime_seconds,
        "results": state.get("outputs", []),
        "analytics_data": state.get("analytics_data", {}),
        "security_findings": state.get("security_findings", []),
        "ast_metrics": state.get("ast_metrics", {}),
        "verification_data": state.get("verification_data", {}),
        "jd_match_data": state.get("jd_match_data", {}),
        "executive_report": state.get("executive_report", ""),
        "mermaid_diagram": state.get("mermaid_diagram", "")
    }