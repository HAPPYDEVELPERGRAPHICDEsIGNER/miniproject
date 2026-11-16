"""
FastAPI Router for Quizzes, Assessments, and Assignments.
Supports timed tests, instant automated grading, and teacher assignment workflows.
"""
import json
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database.engine import get_db
from database.orm_models import (
    User, Subject, Quiz, QuizQuestion, QuizAttempt,
    Assignment, AssignmentSubmission, Notification
)
from schemas.assessment_schemas import (
    QuizCreate, QuizOut, QuizQuestionOut, QuizSubmitRequest, QuizAttemptOut,
    AssignmentCreate, AssignmentOut, AssignmentSubmissionCreate, AssignmentGrade
)
from services.auth_service import get_current_user, require_teacher, require_student

router = APIRouter(prefix="/api/assessments", tags=["Assessments, Quizzes & Assignments"])

# ==============================================================================
# QUIZZES
# ==============================================================================

@router.get("/quizzes", response_model=List[QuizOut])
def get_quizzes(
    subject_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieves available quizzes with completion and attempt status."""
    query = db.query(Quiz).filter(Quiz.is_published == True)
    if subject_id:
        query = query.filter(Quiz.subject_id == subject_id)

    quizzes = query.all()
    out = []
    for q in quizzes:
        attempt = db.query(QuizAttempt).filter(
            QuizAttempt.quiz_id == q.id,
            QuizAttempt.student_id == current_user.id
        ).order_by(QuizAttempt.completed_at.desc()).first()

        out.append(QuizOut(
            id=q.id,
            subject_id=q.subject_id,
            topic_id=q.topic_id,
            title=q.title,
            description=q.description,
            time_limit_minutes=q.time_limit_minutes,
            total_marks=q.total_marks,
            is_published=q.is_published,
            created_at=q.created_at,
            question_count=len(q.questions),
            user_attempted=bool(attempt),
            last_score=attempt.score if attempt else None
        ))
    return out

@router.get("/quizzes/{quiz_id}", response_model=QuizOut)
def get_quiz_details(
    quiz_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Returns quiz questions (hiding correct answers for students prior to submission)."""
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found.")

    attempt = db.query(QuizAttempt).filter(
        QuizAttempt.quiz_id == quiz.id,
        QuizAttempt.student_id == current_user.id
    ).first()

    questions_out = []
    for q in quiz.questions:
        options = json.loads(q.options_json) if q.options_json else []
        # Expose correct answers only if user is teacher/admin OR student has already submitted
        correct_ans = json.loads(q.correct_answer_json) if (current_user.role in ("teacher", "admin") or attempt) else None
        expl = q.explanation if (current_user.role in ("teacher", "admin") or attempt) else None

        questions_out.append(QuizQuestionOut(
            id=q.id,
            quiz_id=q.quiz_id,
            question_text=q.question_text,
            question_type=q.question_type,
            options=options,
            correct_answers=correct_ans,
            explanation=expl,
            marks=q.marks,
            order_index=q.order_index
        ))

    return QuizOut(
        id=quiz.id,
        subject_id=quiz.subject_id,
        topic_id=quiz.topic_id,
        title=quiz.title,
        description=quiz.description,
        time_limit_minutes=quiz.time_limit_minutes,
        total_marks=quiz.total_marks,
        is_published=quiz.is_published,
        created_at=quiz.created_at,
        question_count=len(quiz.questions),
        questions=questions_out,
        user_attempted=bool(attempt),
        last_score=attempt.score if attempt else None
    )

@router.post("/quizzes", response_model=QuizOut)
def create_quiz(
    req: QuizCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher)
):
    """Teachers create a new quiz with questions."""
    subject = db.query(Subject).filter(Subject.id == req.subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found.")

    quiz = Quiz(
        subject_id=req.subject_id,
        topic_id=req.topic_id,
        title=req.title.strip(),
        description=req.description,
        time_limit_minutes=req.time_limit_minutes,
        total_marks=req.total_marks,
        is_published=True
    )
    db.add(quiz)
    db.flush()

    for q_data in req.questions:
        q_item = QuizQuestion(
            quiz_id=quiz.id,
            question_text=q_data.question_text,
            question_type=q_data.question_type,
            options_json=json.dumps(q_data.options),
            correct_answer_json=json.dumps(q_data.correct_answers),
            explanation=q_data.explanation,
            marks=q_data.marks,
            order_index=q_data.order_index
        )
        db.add(q_item)

    db.commit()
    db.refresh(quiz)

    return QuizOut(
        id=quiz.id,
        subject_id=quiz.subject_id,
        topic_id=quiz.topic_id,
        title=quiz.title,
        description=quiz.description,
        time_limit_minutes=quiz.time_limit_minutes,
        total_marks=quiz.total_marks,
        is_published=quiz.is_published,
        created_at=quiz.created_at,
        question_count=len(quiz.questions)
    )

@router.post("/quizzes/{quiz_id}/submit", response_model=QuizAttemptOut)
def submit_quiz_attempt(
    quiz_id: int,
    req: QuizSubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student)
):
    """
    Submits student answers, performs instant automated grading,
    persists attempt, and returns score + review feedback.
    """
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found.")

    earned_score = 0.0
    total_marks = 0.0
    review_items = []

    for q in quiz.questions:
        total_marks += q.marks
        correct_answers = json.loads(q.correct_answer_json) if q.correct_answer_json else []
        options = json.loads(q.options_json) if q.options_json else []
        
        # User answer for this question
        user_ans = req.answers.get(str(q.id)) or req.answers.get(q.id)

        is_correct = False
        if user_ans:
            if isinstance(user_ans, list):
                is_correct = sorted(user_ans) == sorted(correct_answers)
            else:
                is_correct = str(user_ans).strip() in [str(c).strip() for c in correct_answers]

        if is_correct:
            earned_score += q.marks

        review_items.append({
            "question_id": q.id,
            "question_text": q.question_text,
            "options": options,
            "student_answer": user_ans,
            "correct_answers": correct_answers,
            "is_correct": is_correct,
            "marks_awarded": q.marks if is_correct else 0.0,
            "max_marks": q.marks,
            "explanation": q.explanation
        })

    max_score = total_marks if total_marks > 0 else quiz.total_marks
    percentage = round((earned_score / max_score * 100.0), 1) if max_score > 0 else 0.0

    attempt = QuizAttempt(
        quiz_id=quiz.id,
        student_id=current_user.id,
        score=earned_score,
        max_score=max_score,
        answers_json=json.dumps(req.answers),
        time_taken_seconds=req.time_taken_seconds,
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc)
    )
    db.add(attempt)

    # In-app notification for quiz completion
    db.add(Notification(
        user_id=current_user.id,
        title=f"Quiz Completed: {quiz.title}",
        message=f"You scored {earned_score}/{max_score} ({percentage}%). Review your answer breakdown in the Quizzes portal.",
        notification_type="quiz",
        link_url="#quizzes"
    ))

    db.commit()
    db.refresh(attempt)

    return QuizAttemptOut(
        id=attempt.id,
        quiz_id=quiz.id,
        quiz_title=quiz.title,
        student_id=current_user.id,
        score=earned_score,
        max_score=max_score,
        percentage=percentage,
        time_taken_seconds=req.time_taken_seconds,
        completed_at=attempt.completed_at,
        answers_review=review_items
    )

# ==============================================================================
# ASSIGNMENTS
# ==============================================================================

@router.get("/assignments", response_model=List[AssignmentOut])
def get_assignments(
    subject_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieves assignments with student submission status and grades."""
    query = db.query(Assignment).filter(Assignment.is_published == True)
    if subject_id:
        query = query.filter(Assignment.subject_id == subject_id)

    assignments = query.all()
    out = []
    for a in assignments:
        sub = db.query(AssignmentSubmission).filter(
            AssignmentSubmission.assignment_id == a.id,
            AssignmentSubmission.student_id == current_user.id
        ).first()

        out.append(AssignmentOut(
            id=a.id,
            subject_id=a.subject_id,
            topic_id=a.topic_id,
            title=a.title,
            description=a.description,
            max_score=a.max_score,
            deadline=a.deadline,
            is_published=a.is_published,
            created_at=a.created_at,
            submitted=bool(sub),
            submission_id=sub.id if sub else None,
            student_score=sub.score if sub else None,
            feedback=sub.feedback if sub else None
        ))
    return out

@router.post("/assignments", response_model=AssignmentOut)
def create_assignment(
    req: AssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher)
):
    """Teachers publish a new assignment."""
    assignment = Assignment(
        subject_id=req.subject_id,
        topic_id=req.topic_id,
        title=req.title.strip(),
        description=req.description,
        max_score=req.max_score,
        deadline=req.deadline,
        is_published=req.is_published
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    # Notify enrolled students
    enrollments = db.query(User).join(User.enrollments).filter(
        User.enrollments.property.mapper.class_.subject_id == req.subject_id
    ).all()
    for st in enrollments:
        db.add(Notification(
            user_id=st.id,
            title=f"New Assignment: {assignment.title}",
            message=f"An assignment has been posted in your enrolled course. Deadline: {assignment.deadline.strftime('%b %d, %Y') if assignment.deadline else 'No deadline'}.",
            notification_type="assignment",
            link_url="#assignments"
        ))
    db.commit()

    return AssignmentOut(
        id=assignment.id,
        subject_id=assignment.subject_id,
        topic_id=assignment.topic_id,
        title=assignment.title,
        description=assignment.description,
        max_score=assignment.max_score,
        deadline=assignment.deadline,
        is_published=assignment.is_published,
        created_at=assignment.created_at,
        submitted=False
    )

@router.post("/assignments/{assignment_id}/submit")
def submit_assignment(
    assignment_id: int,
    req: AssignmentSubmissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student)
):
    """Students submit code or written solutions for an assignment."""
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found.")

    sub = db.query(AssignmentSubmission).filter(
        AssignmentSubmission.assignment_id == assignment_id,
        AssignmentSubmission.student_id == current_user.id
    ).first()

    now = datetime.now(timezone.utc)
    if not sub:
        sub = AssignmentSubmission(
            assignment_id=assignment_id,
            student_id=current_user.id,
            content=req.content,
            submitted_at=now,
            status="submitted"
        )
        db.add(sub)
    else:
        sub.content = req.content
        sub.submitted_at = now
        sub.status = "submitted"

    db.commit()
    return {"message": "Assignment successfully submitted.", "submission_id": sub.id}

@router.post("/assignments/submissions/{submission_id}/grade")
def grade_assignment(
    submission_id: int,
    req: AssignmentGrade,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher)
):
    """Teachers grade a student's assignment and provide feedback."""
    sub = db.query(AssignmentSubmission).filter(AssignmentSubmission.id == submission_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found.")

    sub.score = req.score
    sub.feedback = req.feedback
    sub.status = "graded"

    # Notify student
    db.add(Notification(
        user_id=sub.student_id,
        title=f"Assignment Graded: {sub.assignment.title}",
        message=f"You received {req.score}/{sub.assignment.max_score}. Teacher Feedback: {req.feedback or 'Good effort.'}",
        notification_type="feedback",
        link_url="#assignments"
    ))
    db.commit()
    return {"message": "Assignment graded successfully.", "score": req.score}
