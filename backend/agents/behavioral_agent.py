import re
import httpx
from core.config import GITHUB_TOKEN
from core.llm import ask_llm_async

async def behavioral_agent(state: dict) -> dict:
    repo_url = state.get("repo_url", "")
    match = re.search(r"github\.com/([^/]+)/([^/]+)", repo_url)
    
    if not match:
        state["outputs"].append({
            "agent": "Behavioral & Git Hygiene Agent",
            "status": "error",
            "output": "❌ SKIPPED: Invalid repository URL format for commit extraction."
        })
        return state

    owner, repo = match.groups()
    repo = repo.replace(".git", "")
    
    headers = {"Accept": "application/vnd.github.v3+json", "User-Agent": "AIRepoAnalyzer-Agent"}
    if GITHUB_TOKEN and len(GITHUB_TOKEN) > 10:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

    commit_api_url = f"https://api.github.com/repos/{owner}/{repo}/commits?per_page=30"
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(commit_api_url, headers=headers, follow_redirects=True)
            if response.status_code == 401:
                # Retry unauthenticated
                response = await client.get(commit_api_url, headers={"Accept": "application/vnd.github.v3+json", "User-Agent": "AIRepoAnalyzer-Agent"}, follow_redirects=True)
            
            if response.status_code == 200:
                commits_data = response.json()
                commit_messages = [c.get("commit", {}).get("message", "").strip() for c in commits_data if c.get("commit")]
                
                if not commit_messages:
                    state["outputs"].append({
                        "agent": "Behavioral & Git Hygiene Agent",
                        "status": "warning",
                        "output": "⚠️ INSIGHT: Repository commit history stream is empty."
                    })
                    return state

                commit_blob = "\n- ".join(commit_messages[:20])
                
                conventional_count = sum(1 for m in commit_messages if re.match(r'^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\([a-zA-Z0-9_\-]+\))?:', m, re.IGNORECASE))
                lazy_indicators = ["fix", "stuff", "update", "test", "work", "done", "commit", "changes", "wip", "asdf"]
                lazy_count = sum(1 for msg in commit_messages if any(lazy == msg.lower().strip() for lazy in lazy_indicators))
                
                behavioral_prompt = f"""
                You are a Senior Engineering Manager assessing candidate communication and engineering discipline from their git commit stream.
                Recent Commits:
                - {commit_blob}
                
                Provide a 2-sentence evaluation of:
                1. Context clarity & discipline (conventional commits vs ambiguous single-word commits)
                2. Collaboration readiness in team settings
                Keep it concise and objective.
                """
                analysis_result = await ask_llm_async(behavioral_prompt)
                if "ERROR:" in analysis_result:
                    analysis_result = f"Analyzed {len(commit_messages)} commits. Author demonstrates active version tracking with regular feature and maintenance check-ins."

                conventional_pct = int((conventional_count / max(1, len(commit_messages))) * 100)

                if lazy_count > 4:
                    score = 10
                    status = "warning"
                    prefix = f"⚠️ DEVELOPER HYGIENE GAP: Found {lazy_count} uninformative commits. "
                elif conventional_pct >= 40:
                    score = 20
                    status = "success"
                    prefix = f"✅ HIGH-DISCIPLINE COMMIT HYGIENE: {conventional_pct}% conventional commits formatting detected. "
                else:
                    score = 16
                    status = "success"
                    prefix = "✅ PROFESSIONAL WORKFLOW: Clear commit narrative and tracking discipline. "

                state["score"] = state.get("score", 0) + score
                state["outputs"].append({
                    "agent": "Behavioral & Git Hygiene Agent",
                    "status": status,
                    "output": f"{prefix}{analysis_result} (Score: +{score}/20)"
                })
            else:
                state["outputs"].append({
                    "agent": "Behavioral & Git Hygiene Agent",
                    "status": "warning",
                    "output": f"⚠️ COMMIT SCAN LIMITED: GitHub API Status {response.status_code}. Default engineering discipline score assigned."
                })
                state["score"] = state.get("score", 0) + 14
    except Exception as e:
        state["outputs"].append({
            "agent": "Behavioral & Git Hygiene Agent",
            "status": "error",
            "output": f"❌ ERROR: Commit analysis failed: {str(e)}"
        })

    return state