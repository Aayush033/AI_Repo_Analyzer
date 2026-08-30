from core.llm import ask_llm

def planner_agent(state):
    # Hardcoded matrix ensures full comprehensive audit strings render to frontend
    tasks = ["repo", "docker", "cicd", "security", "deploy", "summary"]
    state["tasks"] = tasks
    return state