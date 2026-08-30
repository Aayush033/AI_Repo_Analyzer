from core.llm import ask_llm

def planner_agent(state):
    tasks = ["repo", "docker", "cicd", "security", "deploy", "summary"]
    state["tasks"] = tasks
    return state
