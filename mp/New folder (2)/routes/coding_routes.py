"""
FastAPI Router for Personal Coding Platform.
Provides multi-language execution via Judge0, submission auditing, and code snippets.
"""
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database.engine import get_db
from database.orm_models import User, CodeSubmission, CodeSnippet
from schemas.coding_schemas import (
    CodeExecutionRequest, CodeExecutionResponse,
    CodeSnippetCreate, CodeSnippetOut, CodeSubmissionOut
)
from services.auth_service import get_current_user, require_student
from services.judge0_service import execute_code

router = APIRouter(prefix="/api/coding", tags=["Personal Coding Platform"])

@router.post("/execute", response_model=CodeExecutionResponse)
async def run_and_audit_code(
    req: CodeExecutionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Compiles and executes student code via Judge0 API (or local sandboxed runner for Python).
    Stores submission record in database for historical auditing and weakness detection.
    """
    exec_result = await execute_code(
        language=req.language,
        source_code=req.source_code,
        custom_input=req.custom_input
    )

    # Persist submission record in database
    submission = CodeSubmission(
        student_id=current_user.id,
        subject_id=req.subject_id,
        topic_id=req.topic_id,
        language=req.language,
        source_code=req.source_code,
        custom_input=req.custom_input,
        status=exec_result.get("status", "Unknown"),
        stdout=exec_result.get("stdout"),
        stderr=exec_result.get("stderr"),
        compile_output=exec_result.get("compile_output"),
        execution_time=exec_result.get("execution_time"),
        memory_used=exec_result.get("memory_used"),
        exit_code=exec_result.get("exit_code"),
        provider=exec_result.get("provider", "Judge0"),
        created_at=datetime.now(timezone.utc)
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)

    return CodeExecutionResponse(
        submission_id=submission.id,
        status=exec_result.get("status", "Unknown"),
        stdout=exec_result.get("stdout"),
        stderr=exec_result.get("stderr"),
        compile_output=exec_result.get("compile_output"),
        execution_time=exec_result.get("execution_time"),
        memory_used=exec_result.get("memory_used"),
        exit_code=exec_result.get("exit_code"),
        provider=exec_result.get("provider", "Judge0"),
        message=exec_result.get("message")
    )

@router.get("/submissions", response_model=List[CodeSubmissionOut])
def get_user_submissions(
    limit: int = 25,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieves user's coding submission history."""
    query = db.query(CodeSubmission)
    if current_user.role == "student":
        query = query.filter(CodeSubmission.student_id == current_user.id)
    return query.order_by(CodeSubmission.created_at.desc()).limit(limit).all()

@router.post("/snippets", response_model=CodeSnippetOut)
def save_code_snippet(
    req: CodeSnippetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Saves a reusable code snippet for future learning."""
    snippet = CodeSnippet(
        student_id=current_user.id,
        title=req.title.strip(),
        language=req.language,
        code=req.code,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db.add(snippet)
    db.commit()
    db.refresh(snippet)
    return snippet

@router.get("/snippets", response_model=List[CodeSnippetOut])
def get_code_snippets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieves saved code snippets."""
    return db.query(CodeSnippet).filter(CodeSnippet.student_id == current_user.id).order_by(CodeSnippet.updated_at.desc()).all()

@router.delete("/snippets/{snippet_id}")
def delete_code_snippet(
    snippet_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Deletes a code snippet."""
    snippet = db.query(CodeSnippet).filter(CodeSnippet.id == snippet_id, CodeSnippet.student_id == current_user.id).first()
    if not snippet:
        raise HTTPException(status_code=404, detail="Snippet not found.")
    db.delete(snippet)
    db.commit()
    return {"deleted": True, "id": snippet_id}
