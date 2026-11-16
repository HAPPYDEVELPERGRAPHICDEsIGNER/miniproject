"""
SmartEdu AI-Powered Smart Learning and Coding Platform.
Full-stack production FastAPI application connecting students and teachers with:
- Role-based Authentication (Student / Teacher / Admin)
- Syllabus-wise Learning (Subject -> Unit -> Chapter -> Topic -> Notes)
- Personal Multi-Language Coding Platform with real Judge0 execution
- AI Pedagogical Socratic Tutor & Multi-Dimensional Weakness Detection
- Quizzes, Timed Assessments & Assignments
- Scikit-Learn Regression Analysis & 10 Chart.js Performance Visualizations
- In-App Notifications & Teacher Analytics
- Preserves full backward compatibility with legacy Copilot API tools.
"""
import os
import sys
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, Query, status, Depends
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Ensure project directory is in python path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Configuration and Database
from config import settings
from database.engine import engine, SessionLocal
from database.seed_data import init_database_tables, seed_initial_data
from database.db import init_db as init_legacy_db, get_db_path

# Modular API Routers
from routes.auth_routes import router as auth_router
from routes.academic_routes import router as academic_router
from routes.coding_routes import router as coding_router
from routes.ai_routes import router as ai_router
from routes.assessment_routes import router as assessment_router
from routes.analytics_routes import router as analytics_router
from routes.notification_routes import router as notification_router

# Legacy service imports for backward compatibility
from services import ai_service, testing_service, code_reviewer, github_service
from database.models import (
    save_task, get_tasks, get_task_by_id, delete_task, clear_all_tasks, get_dashboard_stats
)

# Logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("smartedu")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initializes database tables, seeding, and graceful shutdown."""
    logger.info("Initializing SmartEdu Relational Database tables...")
    init_database_tables()
    with SessionLocal() as session:
        seed_initial_data(session)
    logger.info("Initializing legacy database for backward compatibility...")
    init_legacy_db()
    logger.info("SmartEdu Platform is ready and operational.")
    yield
    logger.info("Shutting down SmartEdu Platform.")

app = FastAPI(
    title="SmartEdu AI Learning & Coding Platform",
    description="College-Level AI-Powered Learning Platform with Multi-Language Code Execution, Socratic AI Tutor, and Scikit-Learn Regression Analytics.",
    version="2.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static and Templates
static_path = BASE_DIR / "static"
static_path.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

templates_path = BASE_DIR / "templates"
templates_path.mkdir(parents=True, exist_ok=True)

# Register Platform Routers
app.include_router(auth_router)
app.include_router(academic_router)
app.include_router(coding_router)
app.include_router(ai_router)
app.include_router(assessment_router)
app.include_router(analytics_router)
app.include_router(notification_router)

# ==============================================================================
# Single Page Application Frontend Route
# ==============================================================================

@app.get("/", response_class=FileResponse)
async def serve_home():
    """Serves the complete SmartEdu Single-Page Application."""
    index_file = templates_path / "index.html"
    return FileResponse(str(index_file))

# ==============================================================================
# Health and Diagnostics API
# ==============================================================================

@app.get("/api/health")
async def health_check():
    """Returns application status, configured AI engine, and database path."""
    ai_info = ai_service.get_ai_provider_info()
    is_ai = ai_info["configured"]
    return {
        "status": "online",
        "mode": "LIVE AI" if is_ai else "DEMO MODE",
        "app_name": "AI Software Engineering Copilot & SmartEdu Platform",
        "version": "2.0.0",
        "ai_configured": is_ai,
        "ai_engine": ai_info,
        "database_file": str(get_db_path()),
        "isolated_sandbox_available": True,
        "execution_enabled": True,
        "github_token_configured": bool(os.getenv("GITHUB_TOKEN")),
        "integrations": settings.get_public_integrations_status()
    }

# ==============================================================================
# Legacy Copilot API Routes (Preserved for full backward compatibility)
# ==============================================================================

class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=4, max_length=5000)
    language: str = Field(..., pattern="^(Python|C\\+\\+|Java|JavaScript)$")
    style: Optional[str] = "standard"

class TestSuiteRequest(BaseModel):
    code: str = Field(..., min_length=2, max_length=30000)

class TestRunRequest(BaseModel):
    code: str = Field(..., min_length=2, max_length=30000)
    test_code: Optional[str] = Field(None, max_length=30000)
    allow_execution: Optional[bool] = True

class CodeReviewRequest(BaseModel):
    code: str = Field(..., min_length=2, max_length=40000)
    language: str = Field(..., pattern="^(Python|C\\+\\+|Java|JavaScript)$")

class GitHubInspectRequest(BaseModel):
    url: str = Field(..., min_length=10, max_length=300)

class GitHubFileRequest(BaseModel):
    url: str = Field(..., min_length=10, max_length=300)
    path: str = Field(..., min_length=1, max_length=500)

@app.get("/api/dashboard")
async def get_dashboard():
    """Computes and returns real workspace metrics and recent activity from SQLite."""
    try:
        stats = get_dashboard_stats()
        return stats
    except Exception as e:
        logger.error("Error retrieving dashboard stats: %s", e)
        raise HTTPException(status_code=500, detail="Failed to load dashboard metrics.")

@app.post("/api/generate")
async def generate_code_endpoint(body: GenerateRequest):
    try:
        result = await ai_service.generate_code(body.prompt, body.language, body.style or "standard")
        title = f"{body.language} Code Generation"
        task = save_task(
            module="generate",
            title=title,
            description=body.prompt,
            language=body.language,
            input_data={"prompt": body.prompt, "language": body.language, "style": body.style},
            result=result
        )
        return {**result, "task_id": task["id"]}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.exception("Code generation failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

@app.post("/api/test/generate-tests")
async def generate_tests_endpoint(body: TestSuiteRequest):
    try:
        res = testing_service.generate_test_suite(body.code)
        if not res["success"]:
            raise HTTPException(status_code=400, detail=res["error"])
        return res
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to synthesize test suite: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to generate tests: {str(e)}")

@app.post("/api/test/run")
async def run_tests_endpoint(body: TestRunRequest):
    try:
        result = testing_service.run_tests_isolated(
            code=body.code,
            test_code=body.test_code,
            allow_execution=body.allow_execution if body.allow_execution is not None else True
        )
        task = save_task(
            module="test",
            title="Automated Test Execution",
            description=body.code[:150],
            language="Python",
            input_data={"code": body.code, "test_code": body.test_code},
            result=result,
            status="success" if result.get("failed", 0) == 0 else "warning"
        )
        return {**result, "task_id": task["id"]}
    except Exception as e:
        logger.exception("Automated testing run error: %s", e)
        raise HTTPException(status_code=500, detail=f"Test runner error: {str(e)}")

@app.post("/api/test")
async def test_endpoint_alias(body: TestRunRequest):
    return await run_tests_endpoint(body)

@app.post("/api/review")
async def review_code_endpoint(body: CodeReviewRequest):
    try:
        result = code_reviewer.review_code(body.code, body.language)
        task = save_task(
            module="review",
            title=f"{body.language} Code Review (Score: {result['score']}/100)",
            description=body.code[:150],
            language=body.language,
            input_data={"code": body.code, "language": body.language},
            result=result
        )
        return {**result, "task_id": task["id"]}
    except Exception as e:
        logger.exception("Code review failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Code review failed: {str(e)}")

@app.post("/api/github/inspect")
async def inspect_github_endpoint(body: GitHubInspectRequest):
    try:
        result = await github_service.inspect_repository(body.url)
        task = save_task(
            module="github",
            title=f"Inspected {result['repository']}",
            description=body.url,
            language=result.get("language"),
            input_data={"url": body.url},
            result=result
        )
        return {**result, "task_id": task["id"]}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.exception("GitHub inspect failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/github/file")
async def fetch_github_file_endpoint(body: GitHubFileRequest):
    try:
        result = await github_service.fetch_file_content(body.url, body.path)
        return result
    except Exception as e:
        logger.error("GitHub file fetch error: %s", e)
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/history")
async def get_history_endpoint(
    module: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    try:
        tasks = get_tasks(limit=limit, offset=offset, module=module, search=search)
        return tasks
    except Exception as e:
        logger.error("Error reading history: %s", e)
        raise HTTPException(status_code=500, detail="Failed to retrieve history.")

@app.get("/api/history/{task_id}")
async def get_single_history_endpoint(task_id: int):
    task = get_task_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found in local database.")
    return task

@app.delete("/api/history/{task_id}")
async def delete_history_endpoint(task_id: int):
    deleted = delete_task(task_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Task not found.")
    return {"deleted": True, "id": task_id}

@app.delete("/api/history")
async def clear_all_history_endpoint():
    count = clear_all_tasks()
    return {"cleared": True, "count": count}
