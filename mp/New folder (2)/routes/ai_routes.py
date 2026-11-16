"""
FastAPI Router for AI Personal Learning Assistant and Weakness Detection.
"""
import json
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database.engine import get_db
from database.orm_models import User, Subject, Topic, AIAssistanceLog, WeaknessRecord
from schemas.ai_schemas import (
    AIChatRequest, AIChatResponse, WeaknessReport, WeaknessItem
)
from services.auth_service import get_current_user, require_student
from services.ai_tutor_service import get_ai_tutoring_response
from services.weakness_engine import analyze_student_weaknesses

router = APIRouter(prefix="/api/ai", tags=["AI Learning Assistant & Weakness Detection"])

@router.post("/chat", response_model=AIChatResponse)
async def chat_with_ai_tutor(
    req: AIChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Pedagogical AI tutor endpoint.
    Extracts student context (subject, topic, compiler errors, weak topics)
    and returns Socratic guidance, hints, and concept explanations.
    """
    subject_title = None
    topic_title = None
    if req.subject_id:
        sub = db.query(Subject).filter(Subject.id == req.subject_id).first()
        if sub:
            subject_title = sub.title
    if req.topic_id:
        top = db.query(Topic).filter(Topic.id == req.topic_id).first()
        if top:
            topic_title = top.title

    # Query known weak topics for this student
    weak_records = (
        db.query(WeaknessRecord)
        .filter(WeaknessRecord.student_id == current_user.id)
        .order_by(WeaknessRecord.struggle_score.desc())
        .limit(3)
        .all()
    )
    weak_names = [w.concept_name for w in weak_records]

    tutor_reply = await get_ai_tutoring_response(
        student_name=current_user.full_name,
        message=req.message,
        assistance_type=req.assistance_type,
        subject_title=subject_title,
        topic_title=topic_title,
        code_context=req.code_context,
        error_context=req.error_context,
        weak_topics=weak_names
    )

    # Save interaction log
    log = AIAssistanceLog(
        student_id=current_user.id,
        subject_id=req.subject_id,
        topic_id=req.topic_id,
        user_prompt=req.message,
        ai_response=tutor_reply.get("response", ""),
        assistance_type=req.assistance_type,
        created_at=datetime.now(timezone.utc)
    )
    db.add(log)
    db.commit()

    return AIChatResponse(
        response=tutor_reply.get("response", ""),
        assistance_type=req.assistance_type,
        provider=tutor_reply.get("provider", "SmartEdu Tutor"),
        model=tutor_reply.get("model", "Default")
    )

@router.get("/weaknesses", response_model=WeaknessReport)
def get_student_weakness_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student)
):
    """Retrieves or calculates the student's weakness report with detailed reasons and recommendations."""
    # Analyze and ensure records are up-to-date
    analyze_student_weaknesses(current_user.id, db)

    records = (
        db.query(WeaknessRecord)
        .filter(WeaknessRecord.student_id == current_user.id)
        .order_by(WeaknessRecord.struggle_score.desc())
        .all()
    )

    items = []
    high_count = 0
    medium_count = 0
    low_count = 0

    for r in records:
        if r.difficulty_level == "High":
            high_count += 1
        elif r.difficulty_level == "Medium":
            medium_count += 1
        else:
            low_count += 1

        reasons = json.loads(r.reasons_json) if r.reasons_json else []
        actions = json.loads(r.recommended_actions_json) if r.recommended_actions_json else []

        items.append(WeaknessItem(
            concept_name=r.concept_name,
            difficulty_level=r.difficulty_level,
            struggle_score=r.struggle_score,
            subject_title=r.student.enrollments[0].subject.title if r.student.enrollments else "Core Subject",
            reasons=reasons,
            recommended_actions=actions,
            updated_at=r.updated_at
        ))

    overall_rec = "Focus priority revision on High Difficulty topics. Utilize Socratic AI hints and run code tests with small boundary inputs."
    if high_count == 0 and medium_count == 0:
        overall_rec = "Excellent academic momentum! No major conceptual bottlenecks detected across active coursework."

    return WeaknessReport(
        student_id=current_user.id,
        student_name=current_user.full_name,
        total_weaknesses_detected=len(items),
        high_struggle_count=high_count,
        medium_struggle_count=medium_count,
        low_struggle_count=low_count,
        weaknesses=items,
        overall_recommendation=overall_rec
    )

@router.post("/analyze-weaknesses")
def trigger_weakness_analysis(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student)
):
    """Triggers an on-demand re-evaluation of student weakness indicators."""
    results = analyze_student_weaknesses(current_user.id, db)
    return {
        "status": "Analysis complete",
        "weaknesses_evaluated": len(results),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
