"""
Pydantic schemas for Syllabus-Wise Learning and Academic Structure.
Hierarchy: Subject -> Unit -> Chapter -> Topic -> Study Material.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class TopicCreate(BaseModel):
    topic_number: int = Field(..., ge=1)
    title: str = Field(..., min_length=2, max_length=255)
    learning_objectives: Optional[str] = None
    study_content: Optional[str] = None
    resource_url: Optional[str] = None
    is_published: bool = True
    order_index: int = 1

class TopicOut(BaseModel):
    id: int
    chapter_id: int
    topic_number: int
    title: str
    learning_objectives: Optional[str] = None
    study_content: Optional[str] = None
    resource_url: Optional[str] = None
    is_published: bool
    order_index: int
    created_at: datetime
    is_completed: Optional[bool] = False
    study_time_minutes: Optional[float] = 0.0

    class Config:
        from_attributes = True

class ChapterCreate(BaseModel):
    chapter_number: int = Field(..., ge=1)
    title: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    order_index: int = 1

class ChapterOut(BaseModel):
    id: int
    unit_id: int
    chapter_number: int
    title: str
    description: Optional[str] = None
    order_index: int
    topics: List[TopicOut] = []

    class Config:
        from_attributes = True

class UnitCreate(BaseModel):
    unit_number: int = Field(..., ge=1)
    title: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    order_index: int = 1

class UnitOut(BaseModel):
    id: int
    subject_id: int
    unit_number: int
    title: str
    description: Optional[str] = None
    order_index: int
    chapters: List[ChapterOut] = []

    class Config:
        from_attributes = True

class SubjectCreate(BaseModel):
    code: str = Field(..., min_length=2, max_length=50)
    title: str = Field(..., min_length=3, max_length=200)
    description: Optional[str] = None
    department: str = Field("Computer Science & Engineering", min_length=2)
    semester: int = Field(..., ge=1, le=12)
    academic_year: str = Field("2026-2027", min_length=4)

class SubjectOut(BaseModel):
    id: int
    code: str
    title: str
    description: Optional[str] = None
    department: str
    semester: int
    academic_year: str
    teacher_id: int
    teacher_name: Optional[str] = None
    total_topics: Optional[int] = 0
    completed_topics: Optional[int] = 0
    completion_percentage: Optional[float] = 0.0
    units: Optional[List[UnitOut]] = None

    class Config:
        from_attributes = True

class TopicProgressUpdate(BaseModel):
    is_completed: bool = True
    study_time_minutes: float = Field(0.0, ge=0.0)

class EnrollmentRequest(BaseModel):
    subject_id: int
