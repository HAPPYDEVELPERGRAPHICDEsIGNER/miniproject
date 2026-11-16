"""
Pydantic schemas for AI Assistant & Weakness Detection.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class AIChatRequest(BaseModel):
    message: str = Field(..., min_length=2, max_length=5000)
    assistance_type: str = Field("concept", pattern="^(concept|error_debug|hint|practice|syllabus)$")
    subject_id: Optional[int] = None
    topic_id: Optional[int] = None
    code_context: Optional[str] = None
    error_context: Optional[str] = None

class AIChatResponse(BaseModel):
    response: str
    assistance_type: str
    hints: Optional[List[str]] = None
    recommended_topics: Optional[List[str]] = None
    provider: str
    model: str

class WeaknessItem(BaseModel):
    concept_name: str
    difficulty_level: str # High, Medium, Low
    struggle_score: float # 0.0 - 1.0
    subject_title: Optional[str] = None
    reasons: List[str]
    recommended_actions: List[str]
    updated_at: datetime

class WeaknessReport(BaseModel):
    student_id: int
    student_name: str
    total_weaknesses_detected: int
    high_struggle_count: int
    medium_struggle_count: int
    low_struggle_count: int
    weaknesses: List[WeaknessItem]
    overall_recommendation: str
