import os
from collections import Counter

def analytics_agent(state: dict) -> dict:
    files = state.get("repo_files", [])
    
    # Extract extensions from tracked repo artifacts
    extensions = []
    for f in files:
        _, ext = os.path.splitext(f)
        if ext:
            extensions.append(ext.lower())
        else:
            # Catch exceptional configuration systems like Dockerfiles
            base = os.path.basename(f)
            if base in ["dockerfile", "jenkinsfile", "makefile"]:
                extensions.append(base)

    # Count language configurations
    counts = Counter(extensions)
    top_extensions = dict(counts.most_common(6))

    # Fallback default normalization maps if repo has empty tree configurations
    if not top_extensions:
        top_extensions = {".txt": 1}

    # Transform internal extension handles into clear HR display parameters
    friendly_names = {
        ".js": "JavaScript", ".ts": "TypeScript", ".jsx": "React JS", 
        ".tsx": "React TS", ".py": "Python", ".go": "Go Lang",
        ".java": "Java", ".cpp": "C++", ".html": "HTML Layouts", 
        ".css": "Styling Sheets", ".json": "Configs", ".md": "Docs",
        "dockerfile": "Docker", ".yml": "YAML Actions", ".yaml": "YAML Actions"
    }

    hr_friendly_distribution = {}
    for ext, val in top_extensions.items():
        name = friendly_names.get(ext, f"Other ({ext.upper()})")
        hr_friendly_distribution[name] = hr_friendly_distribution.get(name, 0) + val

    # Pack metrics context onto the core pipeline transaction state
    state["analytics_data"] = {
        "language_pie_chart": hr_friendly_distribution,
        "total_files_discovered": len(files),
        "code_density_tier": "Enterprise Architecture Scale" if len(files) > 250 else "Microservice / MVP Project Layout"
    }
    
    return state