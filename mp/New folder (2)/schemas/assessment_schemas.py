"""
Pydantic schemas for Quizzes, Assessments, and Assignments.
"""
from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field

# Assignments
class AssignmentCreate(BaseModel):
    subject_id: int
    topic_id: Optional[int] = None
    title: str = Field(..., min_length=2, max_length=255)
    description: str
    max_score: float = 100.0
    deadline: Optional[datetime] = None
    is_published: bool = True

class AssignmentSubmissionCreate(BaseModel):
    content: str = Field(..., min_length=2)

class AssignmentGrade(BaseModel):
    score: float = Field(..., ge=0.0)
    feedback: Optional[str] = None

class AssignmentOut(BaseModel):
    id: int
    subject_id: int
    topic_id: Optional[int] = None
    title: str
    description: str
    max_score: float
    deadline: Optional[datetime] = None
    is_published: bool
    created_at: datetime
    submitted: Optional[bool] = False
    submission_id: Optional[int] = None
    student_score: Optional[float] = None
    feedback: Optional[str] = None

    class Config:
        from_attributes = True

# Quizzes
class QuizQuestionCreate(BaseModel):
    question_text: str = Field(..., min_length=3)
    question_type: str = Field("mcq", pattern="^(mcq|multiple|coding)$")
    options: List[str] = Field(..., min_items=2)
    correct_answers: List[str] = Field(..., min_items=1)
    explanation: Optional[str] = None
    marks: float = 1.0
    order_index: int = 1

class QuizQuestionOut(BaseModel):
    id: int
    quiz_id: int
    question_text: str
    question_type: str
    options: List[str]
    # correct_answers hidden from students during test
    correct_answers: Optional[List[str]] = None
    explanation: Optional[str] = None
    marks: float
    order_index: int

class QuizCreate(BaseModel):
    subject_id: int
    topic_id: Optional[int] = None
    title: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    time_limit_minutes: int = Field(15, ge=1, le=180)
    total_marks: float = Field(20.0, ge=1.0)
    questions: List[QuizQuestionCreate] = []

class QuizSubmitRequest(BaseModel):
    answers: dict[str, Any] # question_id -> chosen option(s)
    time_taken_seconds: int = 0

class QuizAttemptOut(BaseModel):
    id: int
    quiz_id: int
    quiz_title: str
    student_id: int
    score: float
    max_score: float
    percentage: float
    time_taken_seconds: int
    completed_at: datetime
    answers_review: Optional[List[dict]] = None

class QuizOut(BaseModel):
    id: int
    subject_id: int
    topic_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    time_limit_minutes: int
    total_marks: float
    is_published: bool
    created_at: datetime
    question_count: int = 0
    questions: Optional[List[QuizQuestionOut]] = None
    user_attempted: Optional[bool] = False
    last_score: Optional[float] = None

    class Config:
        from_attributes = True
