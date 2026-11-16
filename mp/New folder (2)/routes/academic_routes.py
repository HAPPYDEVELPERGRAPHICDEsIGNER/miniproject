"""
FastAPI Router for Academic Syllabus Management and Learning Hierarchy.
Hierarchy: Subject -> Unit -> Chapter -> Topic -> Notes/Objectives/Practice.
"""
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database.engine import get_db
from database.orm_models import (
    User, Subject, Unit, Chapter, Topic, Enrollment, TopicProgress
)
from schemas.academic_schemas import (
    SubjectCreate, SubjectOut, UnitCreate, UnitOut,
    ChapterCreate, ChapterOut, TopicCreate, TopicOut,
    TopicProgressUpdate, EnrollmentRequest
)
from services.auth_service import get_current_user, require_teacher, require_student

router = APIRouter(prefix="/api/academic", tags=["Academic Syllabus"])

@router.get("/subjects", response_model=List[SubjectOut])
def get_subjects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns subjects tailored to the user role:
    - Student: Enrolled subjects with completion percentages
    - Teacher: Taught subjects
    - Admin: All subjects
    """
    if current_user.role == "teacher":
        subjects = db.query(Subject).filter(Subject.teacher_id == current_user.id).all()
    elif current_user.role == "student":
        enrollments = db.query(Enrollment).filter(Enrollment.student_id == current_user.id, Enrollment.is_active == True).all()
        subjects = [e.subject for e in enrollments if e.subject]
        if not subjects:
            # Fallback to subjects matching student's semester or all
            subjects = db.query(Subject).filter(Subject.semester == current_user.semester).all() or db.query(Subject).all()
    else:
        subjects = db.query(Subject).all()

    result = []
    for s in subjects:
        # Calculate completion metrics for the student
        total_topics = 0
        completed_topics = 0
        for unit in s.units:
            for ch in unit.chapters:
                for top in ch.topics:
                    if top.is_published:
                        total_topics += 1
                        if current_user.role == "student":
                            prog = db.query(TopicProgress).filter(
                                TopicProgress.student_id == current_user.id,
                                TopicProgress.topic_id == top.id,
                                TopicProgress.is_completed == True
                            ).first()
                            if prog:
                                completed_topics += 1

        completion_pct = round((completed_topics / total_topics * 100.0), 1) if total_topics > 0 else 0.0

        result.append(SubjectOut(
            id=s.id,
            code=s.code,
            title=s.title,
            description=s.description,
            department=s.department,
            semester=s.semester,
            academic_year=s.academic_year,
            teacher_id=s.teacher_id,
            teacher_name=s.teacher.full_name if s.teacher else "Faculty Member",
            total_topics=total_topics,
            completed_topics=completed_topics,
            completion_percentage=completion_pct
        ))
    return result

@router.post("/subjects", response_model=SubjectOut)
def create_subject(
    req: SubjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher)
):
    """Teachers create a new subject."""
    existing = db.query(Subject).filter(Subject.code == req.code.upper().strip()).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Subject with code '{req.code}' already exists.")

    subject = Subject(
        code=req.code.upper().strip(),
        title=req.title.strip(),
        description=req.description,
        department=req.department,
        semester=req.semester,
        academic_year=req.academic_year,
        teacher_id=current_user.id
    )
    db.add(subject)
    db.commit()
    db.refresh(subject)
    return SubjectOut(
        id=subject.id,
        code=subject.code,
        title=subject.title,
        description=subject.description,
        department=subject.department,
        semester=subject.semester,
        academic_year=subject.academic_year,
        teacher_id=subject.teacher_id,
        teacher_name=current_user.full_name,
        total_topics=0,
        completed_topics=0,
        completion_percentage=0.0
    )

@router.get("/subjects/{subject_id}/syllabus")
def get_subject_syllabus(
    subject_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Returns complete syllabus hierarchy: Units -> Chapters -> Topics with student progress."""
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found.")

    units_data = []
    total_topics = 0
    completed_topics = 0

    for u in subject.units:
        chapters_data = []
        for ch in u.chapters:
            topics_data = []
            for top in ch.topics:
                # Filter unpublished topics for students
                if current_user.role == "student" and not top.is_published:
                    continue
                
                total_topics += 1
                prog = db.query(TopicProgress).filter(
                    TopicProgress.student_id == current_user.id,
                    TopicProgress.topic_id == top.id
                ).first() if current_user.role == "student" else None

                is_comp = prog.is_completed if prog else False
                st_time = prog.study_time_minutes if prog else 0.0
                if is_comp:
                    completed_topics += 1

                topics_data.append({
                    "id": top.id,
                    "chapter_id": top.chapter_id,
                    "topic_number": top.topic_number,
                    "title": top.title,
                    "learning_objectives": top.learning_objectives,
                    "study_content": top.study_content,
                    "resource_url": top.resource_url,
                    "is_published": top.is_published,
                    "order_index": top.order_index,
                    "is_completed": is_comp,
                    "study_time_minutes": st_time
                })
            chapters_data.append({
                "id": ch.id,
                "unit_id": ch.unit_id,
                "chapter_number": ch.chapter_number,
                "title": ch.title,
                "description": ch.description,
                "order_index": ch.order_index,
                "topics": topics_data
            })
        units_data.append({
            "id": u.id,
            "subject_id": u.subject_id,
            "unit_number": u.unit_number,
            "title": u.title,
            "description": u.description,
            "order_index": u.order_index,
            "chapters": chapters_data
        })

    pct = round((completed_topics / total_topics * 100.0), 1) if total_topics > 0 else 0.0

    return {
        "subject": {
            "id": subject.id,
            "code": subject.code,
            "title": subject.title,
            "description": subject.description,
            "department": subject.department,
            "semester": subject.semester,
            "academic_year": subject.academic_year,
            "teacher_name": subject.teacher.full_name if subject.teacher else "Faculty"
        },
        "total_topics": total_topics,
        "completed_topics": completed_topics,
        "completion_percentage": pct,
        "units": units_data
    }

@router.post("/units")
def create_unit(
    req: UnitCreate,
    subject_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher)
):
    """Teachers add a syllabus unit to a subject."""
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found.")
    if current_user.role != "admin" and subject.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized to modify this subject.")

    unit = Unit(
        subject_id=subject_id,
        unit_number=req.unit_number,
        title=req.title,
        description=req.description,
        order_index=req.order_index
    )
    db.add(unit)
    db.commit()
    db.refresh(unit)
    return {"message": "Unit created", "unit_id": unit.id, "title": unit.title}

@router.post("/chapters")
def create_chapter(
    req: ChapterCreate,
    unit_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher)
):
    """Teachers add a chapter to a unit."""
    unit = db.query(Unit).filter(Unit.id == unit_id).first()
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found.")

    chapter = Chapter(
        unit_id=unit_id,
        chapter_number=req.chapter_number,
        title=req.title,
        description=req.description,
        order_index=req.order_index
    )
    db.add(chapter)
    db.commit()
    db.refresh(chapter)
    return {"message": "Chapter created", "chapter_id": chapter.id, "title": chapter.title}

@router.post("/topics")
def create_topic(
    req: TopicCreate,
    chapter_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher)
):
    """Teachers add a topic with notes and objectives to a chapter."""
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found.")

    topic = Topic(
        chapter_id=chapter_id,
        topic_number=req.topic_number,
        title=req.title,
        learning_objectives=req.learning_objectives,
        study_content=req.study_content,
        resource_url=req.resource_url,
        is_published=req.is_published,
        order_index=req.order_index
    )
    db.add(topic)
    db.commit()
    db.refresh(topic)
    return {"message": "Topic created", "topic_id": topic.id, "title": topic.title}

@router.put("/topics/{topic_id}/progress")
def update_topic_progress(
    topic_id: int,
    req: TopicProgressUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student)
):
    """Students mark topic as complete and record study duration."""
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found.")

    prog = db.query(TopicProgress).filter(
        TopicProgress.student_id == current_user.id,
        TopicProgress.topic_id == topic_id
    ).first()

    now = datetime.now(timezone.utc)
    if not prog:
        prog = TopicProgress(
            student_id=current_user.id,
            topic_id=topic_id,
            is_completed=req.is_completed,
            completed_at=now if req.is_completed else None,
            study_time_minutes=req.study_time_minutes,
            attempts_count=1,
            last_accessed_at=now
        )
        db.add(prog)
    else:
        prog.is_completed = req.is_completed
        if req.is_completed and not prog.completed_at:
            prog.completed_at = now
        prog.study_time_minutes += req.study_time_minutes
        prog.attempts_count += 1
        prog.last_accessed_at = now

    db.commit()
    return {
        "topic_id": topic_id,
        "is_completed": prog.is_completed,
        "total_study_minutes": round(prog.study_time_minutes, 1)
    }

@router.get("/continue-learning")
def get_continue_learning(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student)
):
    """Fetches the last accessed topic or the next pending topic to resume studying."""
    last_prog = (
        db.query(TopicProgress)
        .filter(TopicProgress.student_id == current_user.id)
        .order_by(TopicProgress.last_accessed_at.desc())
        .first()
    )
    if last_prog and last_prog.topic:
        return {
            "has_resume": True,
            "topic_id": last_prog.topic.id,
            "topic_title": last_prog.topic.title,
            "chapter_title": last_prog.topic.chapter.title if last_prog.topic.chapter else "",
            "subject_id": last_prog.topic.chapter.unit.subject.id if last_prog.topic.chapter and last_prog.topic.chapter.unit else None,
            "subject_title": last_prog.topic.chapter.unit.subject.title if last_prog.topic.chapter and last_prog.topic.chapter.unit else "",
            "is_completed": last_prog.is_completed
        }

    # If no progress yet, return first topic of first enrolled subject
    first_topic = db.query(Topic).filter(Topic.is_published == True).first()
    if first_topic:
        return {
            "has_resume": True,
            "topic_id": first_topic.id,
            "topic_title": first_topic.title,
            "chapter_title": first_topic.chapter.title if first_topic.chapter else "",
            "subject_id": first_topic.chapter.unit.subject.id if first_topic.chapter and first_topic.chapter.unit else None,
            "subject_title": first_topic.chapter.unit.subject.title if first_topic.chapter and first_topic.chapter.unit else "",
            "is_completed": False
        }

    return {"has_resume": False}
