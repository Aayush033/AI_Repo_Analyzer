import os
import re
from core.llm import ask_llm_async

async def jd_matcher_agent(state: dict) -> dict:
    jd_text = state.get("requirement", "").strip()
    files = state.get("repo_files", [])

    if not jd_text or jd_text == "Comprehensive system profile metric scan":
        state["outputs"].append({
            "agent": "JD Matcher Agent",
            "status": "warning",
            "output": "⚠️ SKIPPED: Generic audit profile used (no target job description or skill rubric was provided)."
        })
        return state

    # Step 1: Extract core tech stack demands from JD
    tech_extractor_prompt = f"""
    Analyze the following Job Description / Assessment Requirement and extract the top 5 core technical requirements, languages, libraries, or architectural concepts (e.g., FastAPI, React, PyTorch, Docker, PostgreSQL, WebRTC).
    Return them ONLY as a comma-separated list of keywords without any explanation.
    
    Requirement:
    {jd_text}
    """
    
    extracted_response = await ask_llm_async(tech_extractor_prompt)
    if "ERROR:" in extracted_response:
        # Robust deterministic extraction fallback
        known_techs = [
            "python", "flask", "django", "fastapi", "react", "typescript", "javascript", "js", "html", "css",
            "docker", "postgres", "mysql", "sql", "sqlite", "mongodb", "mongo", "aws", "gcp", "azure",
            "pytest", "jest", "node", "nodejs", "express", "ci/cd", "github actions", "webrtc", "socket",
            "ai", "ml", "machine learning", "llm", "rag", "agent", "orchestration", "java", "spring",
            "c#", "csharp", ".net", "php", "laravel", "ruby", "rails", "golang", "go", "rust", "c++", "c",
            "tailwind", "bootstrap", "graphql", "rest", "api", "git", "testing"
        ]
        extracted_techs = []
        jd_lower = jd_text.lower()
        for kt in known_techs:
            if kt in jd_lower:
                extracted_techs.append(kt)
        if not extracted_techs:
            extracted_techs = ["javascript", "html", "css", "api"]
    else:
        extracted_techs = [t.strip().lower() for t in extracted_response.split(",") if t.strip()]

    # Step 2: Comprehensive evidence mapping across all technologies
    tech_map = {
        "html": [".html", ".htm", "index.html", ".ejs", ".pug"],
        "css": [".css", ".scss", ".sass", ".less", "style.css", "tailwind", "bootstrap"],
        "javascript": [".js", ".jsx", ".mjs", ".cjs", "package.json", "node_modules"],
        "js": [".js", ".jsx", ".mjs", ".cjs", "package.json"],
        "typescript": [".ts", ".tsx", "tsconfig.json"],
        "ts": [".ts", ".tsx", "tsconfig.json"],
        "python": [".py", "requirements.txt", "pyproject.toml", "pipfile", "setup.py", "manage.py"],
        "py": [".py", "requirements.txt"],
        "java": [".java", "pom.xml", "build.gradle", ".mvn", ".gradle", "src/main/java"],
        "spring": ["spring", "application.properties", "application.yml", "pom.xml", ".java"],
        "c#": [".cs", ".csproj", ".sln", ".dotnet"],
        "csharp": [".cs", ".csproj", ".sln"],
        ".net": [".csproj", ".sln", "program.cs"],
        "php": [".php", "composer.json", "artisan", "index.php"],
        "laravel": ["artisan", "composer.json", "routes/web.php", "app/http"],
        "ruby": [".rb", "gemfile", "rakefile"],
        "rails": ["gemfile", "config/routes.rb", "app/controllers"],
        "golang": [".go", "go.mod", "go.sum", "main.go"],
        "go": [".go", "go.mod", "go.sum", "main.go"],
        "rust": [".rs", "cargo.toml", "cargo.lock"],
        "c++": [".cpp", ".hpp", ".cc", ".cxx", "cmakelists.txt", "makefile"],
        "cpp": [".cpp", ".hpp", ".cc", ".cxx", "cmakelists.txt"],
        "c": [".c", ".h", "makefile", "cmakelists.txt"],
        "react": [".jsx", ".tsx", "package.json", "react", "src/app", "src/components"],
        "vue": [".vue", "vue.config.js", "src/views"],
        "angular": ["angular.json", ".component.ts", ".component.html"],
        "node": ["package.json", "server.js", "app.js", "index.js", "node_modules"],
        "nodejs": ["package.json", "server.js", "app.js", "index.js"],
        "express": ["express", "server.js", "app.js", "routes"],
        "fastapi": ["fastapi", "main.py", "app.py"],
        "flask": ["flask", "app.py", "wsgi.py"],
        "django": ["django", "manage.py", "settings.py", "urls.py"],
        "sql": [".sql", "schema.sql", "migrations", "database", "models"],
        "mysql": ["mysql", ".sql", "database.sql", "db.sql", "models"],
        "postgres": ["postgres", "postgresql", "psycopg2", "asyncpg", "pg"],
        "postgresql": ["postgres", "postgresql", "psycopg2", "asyncpg", "pg"],
        "sqlite": ["sqlite", ".sqlite", ".db", "db.sqlite3"],
        "mongodb": ["mongo", "mongoose", "schema", "database"],
        "mongo": ["mongo", "mongoose", "schema", "database"],
        "redis": ["redis", "ioredis"],
        "docker": ["dockerfile", "docker-compose", ".dockerignore"],
        "kubernetes": ["k8s", "deployment.yaml", "service.yaml", "helm"],
        "k8s": ["k8s", "deployment.yaml", "service.yaml"],
        "aws": ["boto3", "cdk", "serverless.yml", "aws", "s3"],
        "gcp": ["google-cloud", "gcs", "bigquery", "app.yaml"],
        "azure": ["azure", "arm-template"],
        "tailwind": ["tailwind.config.js", "tailwind.css", "tailwind"],
        "bootstrap": ["bootstrap.css", "bootstrap.min.js", "bootstrap"],
        "webrtc": ["webrtc", "socket.io", "socket", "peer", "rtc", "stream", "video", "call", "public/js"],
        "websocket": ["socket.io", "websocket", "ws", "socket"],
        "socket": ["socket.io", "websocket", "ws", "socket"],
        "rest": ["api", "route", "routes", "endpoint", "controller", "server", "app"],
        "api": ["api", "route", "routes", "endpoint", "controller", "server", "app"],
        "graphql": ["graphql", ".gql", "schema.graphql"],
        "ci/cd": [".github/workflows", ".gitlab-ci.yml", "jenkinsfile", ".circleci"],
        "github actions": [".github/workflows"],
        "testing": ["test", "spec", "pytest", "jest", "mocha", "unittest", "tests/"],
        "tests": ["test", "spec", "pytest", "jest", "mocha", "unittest", "tests/"],
        "pytest": ["test_", "_test.py", "conftest.py", "pytest.ini", "tests"],
        "jest": ["jest.config.js", ".test.js", ".spec.js", ".test.ts"],
        "git": [".gitignore", "readme.md", ".git"],
        "ai": ["ai", "model", "prompt", "llm", "agent", "rag", ".py", "generate"],
        "ml": ["torch", "tensorflow", "sklearn", "model", "train", ".py"],
        "machine learning": ["torch", "tensorflow", "sklearn", "model", "train", ".py"],
        "llm": ["openai", "gemini", "anthropic", "langchain", "llama", "prompt", "chat", ".py"],
        "rag": ["vector", "chroma", "faiss", "embedding", "retriever", "rag"]
    }

    matched_techs = []
    missing_techs = []

    files_lower = [f.lower() for f in files]
    file_blob = "\n".join(files[:300]).lower()

    # Deep inspect codebase manifests and entrypoint contents (requirements, package.json, main.py, etc.)
    content_blob = ""
    cloned_path = state.get("cloned_path", "")
    if cloned_path and os.path.exists(cloned_path):
        for root, _, c_files in os.walk(cloned_path):
            if any(p.startswith(('.', 'venv', 'node_modules', '__pycache__')) for p in root.split(os.sep)):
                continue
            for cf in c_files:
                if cf.endswith(('.txt', '.json', '.toml', '.py', '.js', '.ts', '.html', '.md', '.yml', '.yaml', '.cfg')):
                    c_path = os.path.join(root, cf)
                    try:
                        with open(c_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content_blob += "\n" + f.read()[:3000]
                    except Exception:
                        pass
            if len(content_blob) > 40000:
                break
    content_blob = content_blob.lower()

    for tech in extracted_techs:
        indicators = tech_map.get(tech, [tech])
        is_matched = False
        for ind in indicators:
            if any(ind in f for f in files_lower) or ind in file_blob or ind in content_blob:
                is_matched = True
                break
        if is_matched:
            matched_techs.append(tech)
        else:
            missing_techs.append(tech)

    total = len(extracted_techs) if extracted_techs else 1
    raw_pct = int((len(matched_techs) / total) * 100)
    match_percentage = min(100, max(0, raw_pct))
    score_increment = int((match_percentage / 100) * 20)

    verification_prompt = f"""
    You are a Technical Hiring Manager evaluating candidate-to-job match.
    Target Skills: {', '.join(extracted_techs)}
    Matched in Code: {', '.join(matched_techs) if matched_techs else 'None'}
    Missing/Unverified: {', '.join(missing_techs) if missing_techs else 'None'}
    Repository Sample Files:
    {file_blob[:800]}
    
    Write a 2-sentence objective assessment of the candidate's alignment with the role. State concrete evidence found in their codebase. Keep it professional and direct.
    """
    alignment_summary = await ask_llm_async(verification_prompt)
    if "ERROR:" in alignment_summary:
        if match_percentage >= 65:
            alignment_summary = f"Codebase provides verified implementation evidence for {', '.join(matched_techs) or 'core stack'}. Demonstrates foundational alignment with targeted technical requirements."
        else:
            alignment_summary = f"Codebase demonstrates strong architectural execution ({', '.join(matched_techs) or 'general stack'}), with opportunities to expand on {', '.join(missing_techs) or 'niche competencies'}."

    if match_percentage >= 70:
        status = "success"
        prefix = f"✅ HIGH CANDIDATE ALIGNMENT ({match_percentage}% Match):"
    elif match_percentage >= 40:
        status = "warning"
        prefix = f"⚠️ PARTIAL CANDIDATE ALIGNMENT ({match_percentage}% Match):"
    else:
        status = "warning"
        prefix = f"⚠️ BASELINE CANDIDATE ALIGNMENT ({match_percentage}% Match):"

    state["score"] = state.get("score", 0) + score_increment
    state["jd_match_data"] = {
        "match_percentage": match_percentage,
        "matched_skills": matched_techs,
        "missing_skills": missing_techs
    }

    state["outputs"].append({
        "agent": "JD Matcher Agent",
        "status": status,
        "output": f"{prefix} {alignment_summary} (Matched: {', '.join(matched_techs) or 'Stack Base'} | Score: +{score_increment}/20)"
    })

    return state