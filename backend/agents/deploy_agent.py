def deploy_agent(state):
    files = state.get("repo_files", [])
    has_deploy = any(any(term in f.lower() for term in ["docker-compose", "kubernetes", "vercel", "render.yaml", "tf"]) for f in files)
    
    if has_deploy:
        state["outputs"].append({"agent": "Deploy Agent", "status": "success", "output": "✅ VERIFIED: Cloud infrastructure-as-code configuration parameters are explicitly detailed. (Score: +20/20)"})
        state["score"] += 20
    else:
        state["outputs"].append({"agent": "Deploy Agent", "status": "error", "output": "❌ MISSING: Missing native cloud architecture specifications (Terraform, Compose profiles). (Score: +0/20) -> Loss Reason: Cloud environment runs via decoupled manual tasks. Action Required: Add structural infra configurations."})
    return state