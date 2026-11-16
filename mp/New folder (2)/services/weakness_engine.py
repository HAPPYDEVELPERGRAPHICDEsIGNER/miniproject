"""
AI Student Weakness Detection Engine.
Multi-indicator algorithm analyzing:
- Quiz marks & failed questions
- Coding errors (compilation, runtime, timeouts)
- Assignment marks
- Study time & repeated topic attempts
- Topic completion rates
Explains WHY each topic was flagged with High, Medium, or Low difficulty.
"""
import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from database.orm_models import (
    User, Subject, Topic, TopicProgress, QuizAttempt, Quiz,
    AssignmentSubmission, Assignment, CodeSubmission, AIAssistanceLog,
    WeaknessRecord, Notification
)

logger = logging.getLogger("smartedu.weakness_engine")

def analyze_student_weaknesses(student_id: int, db: Session) -> List[Dict[str, Any]]:
    """
    Performs comprehensive multi-indicator weakness assessment for a given student.
    Persists results in weakness_records table.
    """
    student = db.query(User).filter(User.id == student_id).first()
    if not student:
        return []

    # Get student enrolled subjects
    enrolled_subjects = [e.subject for e in student.enrollments if e.is_active and e.subject]
    if not enrolled_subjects:
        enrolled_subjects = db.query(Subject).all() # fallback if enrolled in all

    detected_weaknesses: List[Dict[str, Any]] = []

    for subject in enrolled_subjects:
        # Check all topics in this subject
        topics = (
            db.query(Topic)
            .join(Topic.chapter)
            .join(Topic.chapter.property.mapper.class_.unit)
            .filter(Topic.chapter.property.mapper.class_.unit.property.mapper.class_.subject_id == subject.id)
            .all()
        )

        for topic in topics:
            reasons = []
            struggle_points = 0.0

            # 1. Topic Progress & Study Time vs Completion
            progress = (
                db.query(TopicProgress)
                .filter(TopicProgress.student_id == student_id, TopicProgress.topic_id == topic.id)
                .first()
            )
            if progress:
                if not progress.is_completed and progress.study_time_minutes > 45:
                    struggle_points += 0.25
                    reasons.append(f"High study duration ({progress.study_time_minutes:.1f} mins) without marking topic as mastered.")
                if progress.attempts_count >= 3 and not progress.is_completed:
                    struggle_points += 0.20
                    reasons.append(f"Repeated revisions ({progress.attempts_count} access attempts) without topic completion.")

            # 2. Quiz Performance linked to Subject/Topic
            quizzes = db.query(Quiz).filter(Quiz.subject_id == subject.id).all()
            for quiz in quizzes:
                # Filter attempts by this student
                attempt = (
                    db.query(QuizAttempt)
                    .filter(QuizAttempt.quiz_id == quiz.id, QuizAttempt.student_id == student_id)
                    .order_by(QuizAttempt.completed_at.desc())
                    .first()
                )
                if attempt and attempt.max_score > 0:
                    score_pct = (attempt.score / attempt.max_score) * 100.0
                    if score_pct < 50.0:
                        struggle_points += 0.35
                        reasons.append(f"Scored {score_pct:.1f}% on related quiz '{quiz.title}'.")
                    elif score_pct < 65.0:
                        struggle_points += 0.15
                        reasons.append(f"Borderline score ({score_pct:.1f}%) on quiz '{quiz.title}'.")

            # 3. Coding Submissions & Errors linked to this topic / language
            code_subs = (
                db.query(CodeSubmission)
                .filter(CodeSubmission.student_id == student_id)
                .filter((CodeSubmission.topic_id == topic.id) | (CodeSubmission.subject_id == subject.id))
                .all()
            )
            runtime_errors = sum(1 for c in code_subs if c.status == "Runtime Error")
            compile_errors = sum(1 for c in code_subs if c.status in ("Compilation Error", "Internal Error"))
            tle_errors = sum(1 for c in code_subs if c.status == "Time Limit Exceeded")

            if compile_errors > 0 or runtime_errors > 0 or tle_errors > 0:
                total_err = compile_errors + runtime_errors + tle_errors
                if total_err >= 3:
                    struggle_points += 0.30
                    reasons.append(f"Encountered {total_err} code execution failures ({compile_errors} compilation, {runtime_errors} runtime, {tle_errors} timeout).")
                elif total_err >= 1:
                    struggle_points += 0.15
                    reasons.append(f"Recent code errors in practical tasks ({total_err} errors logged).")

            # 4. AI Assistance Questions (Corroborating signal)
            ai_questions = (
                db.query(AIAssistanceLog)
                .filter(AIAssistanceLog.student_id == student_id)
                .filter((AIAssistanceLog.topic_id == topic.id) | (AIAssistanceLog.subject_id == subject.id))
                .count()
            )
            if ai_questions >= 3 and struggle_points > 0.2:
                struggle_points += 0.15
                reasons.append(f"Sought AI debugging and clarification {ai_questions} times on this module.")

            # Determine difficulty rating if struggle is evident
            if struggle_points >= 0.25 and reasons:
                normalized_score = min(round(struggle_points, 2), 1.0)
                if normalized_score >= 0.65:
                    difficulty = "High"
                elif normalized_score >= 0.40:
                    difficulty = "Medium"
                else:
                    difficulty = "Low"

                # Generate actionable recommendations
                recommended_actions = [
                    f"Review core conceptual notes for '{topic.title}'.",
                    f"Practice 2-3 code implementations with step-by-step test cases.",
                    f"Re-take practice quizzes to verify retention."
                ]
                if difficulty == "High":
                    recommended_actions.insert(0, f"Request teacher 1-on-1 feedback or use AI Tutor 'concept breakdown' mode.")

                # Save / update in database
                record = (
                    db.query(WeaknessRecord)
                    .filter(
                        WeaknessRecord.student_id == student_id,
                        WeaknessRecord.subject_id == subject.id,
                        WeaknessRecord.concept_name == topic.title
                    )
                    .first()
                )
                if not record:
                    record = WeaknessRecord(
                        student_id=student_id,
                        subject_id=subject.id,
                        topic_id=topic.id,
                        concept_name=topic.title,
                        difficulty_level=difficulty,
                        struggle_score=normalized_score,
                        reasons_json=json.dumps(reasons),
                        recommended_actions_json=json.dumps(recommended_actions),
                        updated_at=datetime.now(timezone.utc)
                    )
                    db.add(record)
                else:
                    record.difficulty_level = difficulty
                    record.struggle_score = normalized_score
                    record.reasons_json = json.dumps(reasons)
                    record.recommended_actions_json = json.dumps(recommended_actions)
                    record.updated_at = datetime.now(timezone.utc)

                detected_weaknesses.append({
                    "concept_name": topic.title,
                    "difficulty_level": difficulty,
                    "struggle_score": normalized_score,
                    "subject_title": subject.title,
                    "reasons": reasons,
                    "recommended_actions": recommended_actions,
                    "updated_at": datetime.now(timezone.utc)
                })

    db.commit()
    return detected_weaknesses
