def docker_agent(state):
    files = state.get("repo_files", [])
    has_docker = any("Dockerfile" in f for f in files)
    
    if has_docker:
        state["outputs"].append({"agent": "Docker Agent", "status": "success", "output": "✅ VERIFIED: Standard production Dockerfile configuration discovered. (Score: +20/20)"})
        state["score"] += 20
    else:
        state["outputs"].append({"agent": "Docker Agent", "status": "error", "output": "❌ MISSING: No Dockerfile found in code tree layouts. (Score: +0/20) -> Loss Reason: Environment containerization strategy is absent. Action Required: Inject a robust Dockerfile configuration."})

    return state