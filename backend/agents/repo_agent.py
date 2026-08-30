import httpx
import re
import time
from core.config import GITHUB_TOKEN

REPO_CACHE = {}
CACHE_TTL = 600

async def repo_agent(state: dict) -> dict:
    repo_url = state.get("repo_url", "")
    if not repo_url:
        state["outputs"].append({
            "agent": "Repo Agent",
            "status": "error",
            "output": "❌ CRITICAL: No repository URL provided. (Score: +0/20) -> Action Required: Provide a valid public GitHub repository link."
        })
        return state

    match = re.search(r"github\.com/([^/]+)/([^/]+)", repo_url)
    if not match:
        state["outputs"].append({
            "agent": "Repo Agent",
            "status": "error",
            "output": "❌ INVALID: Improper GitHub URL structure format. (Score: +0/20) -> Action Required: Check your repository string format."
        })
        return state
        
    owner, repo = match.groups()
    repo = repo.replace(".git", "")
    cache_key = f"{owner}/{repo}".lower()

    current_time = time.time()
    if cache_key in REPO_CACHE:
        cached_data, timestamp = REPO_CACHE[cache_key]
        if current_time - timestamp < CACHE_TTL:
            state["repo_files"] = cached_data
            state["outputs"].append({
                "agent": "Repo Agent",
                "status": "success",
                "output": f"✅ SUCCESS: Codebase pulled from production cache layer. (Score: +20/20) -> Mapped {len(cached_data)} structural files instantly."
            })
            state["score"] = state.get("score", 0) + 20
            return state

    headers = {"Accept": "application/vnd.github.v3+json", "User-Agent": "AIRepoAnalyzer-Agent"}
    if GITHUB_TOKEN and len(GITHUB_TOKEN) > 10:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

    api_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/main?recursive=1"
    timeout_config = httpx.Timeout(25.0, connect=5.0, read=25.0)

    try:
        async with httpx.AsyncClient(timeout=timeout_config) as client:
            response = await client.get(api_url, headers=headers, follow_redirects=True)
            
            # If 401 Unauthorized (invalid token), retry without Authorization header
            if response.status_code == 401:
                unauth_headers = {"Accept": "application/vnd.github.v3+json", "User-Agent": "AIRepoAnalyzer-Agent"}
                response = await client.get(api_url, headers=unauth_headers, follow_redirects=True)

            # Fallback to master branch
            if response.status_code == 404:
                api_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/master?recursive=1"
                response = await client.get(api_url, headers=headers, follow_redirects=True)
                if response.status_code == 401:
                    unauth_headers = {"Accept": "application/vnd.github.v3+json", "User-Agent": "AIRepoAnalyzer-Agent"}
                    response = await client.get(api_url, headers=unauth_headers, follow_redirects=True)

            if response.status_code == 200:
                data = response.json()
                is_truncated = data.get("truncated", False)
                file_paths = [item["path"] for item in data.get("tree", []) if item["type"] == "blob"]
                
                REPO_CACHE[cache_key] = (file_paths, current_time)
                state["repo_files"] = file_paths
                
                if is_truncated:
                    output_msg = f"⚠️ SUCCESS (Truncated Payload): Massive repo detected. Mapped {len(file_paths)} core structural files for validation. (Score: +20/20)"
                else:
                    output_msg = f"✅ SUCCESS: Codebase reached and cataloged. (Score: +20/20) -> Found {len(file_paths)} structural files."
                
                state["outputs"].append({"agent": "Repo Agent", "status": "success", "output": output_msg})
                state["score"] = state.get("score", 0) + 20
            
            elif response.status_code in (403, 429):
                state["outputs"].append({
                    "agent": "Repo Agent",
                    "status": "warning",
                    "output": f"⚠️ GitHub Rate Limit reached ({response.status_code}). Local clone engine will proceed with direct file exploration. (Score: +15/20)"
                })
                state["score"] = state.get("score", 0) + 15
            else:
                state["outputs"].append({
                    "agent": "Repo Agent",
                    "status": "error",
                    "output": f"❌ FAILED: API connection rejected [Status Code {response.status_code}]. (Score: +0/20)"
                })
                
    except Exception as e:
        state["outputs"].append({
            "agent": "Repo Agent",
            "status": "warning",
            "output": f"⚠️ Network note: {str(e)}. Proceeding with direct local clone."
        })

    return state