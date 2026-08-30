def cicd_agent(state):
    files = state.get("repo_files", [])
    has_workflows = any(".github/workflows" in f for f in files)
    
    if has_workflows:
        state["outputs"].append({"agent": "CI/CD Agent", "status": "success", "output": "✅ VERIFIED: Active GitHub Actions automated pipeline engine layout detected. (Score: +20/20)"})
        state["score"] += 20
    else:
        state["outputs"].append({"agent": "CI/CD Agent", "status": "error", "output": "❌ MISSING: Automation integration templates are absent. (Score: +0/20) -> Loss Reason: Code base lacks active build regression paths. Action Required: Configure automation steps under `.github/workflows/`."})

    return state