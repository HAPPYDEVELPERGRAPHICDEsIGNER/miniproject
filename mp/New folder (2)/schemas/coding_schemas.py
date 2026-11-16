"""
Pydantic schemas for the Personal Coding Platform.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class CodeExecutionRequest(BaseModel):
    language: str = Field(..., description="Programming language: Python, C, C++, Java, JavaScript, etc.")
    source_code: str = Field(..., min_length=1, max_length=50000)
    custom_input: Optional[str] = ""
    subject_id: Optional[int] = None
    topic_id: Optional[int] = None

class CodeExecutionResponse(BaseModel):
    submission_id: Optional[int] = None
    status: str
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    compile_output: Optional[str] = None
    execution_time: Optional[float] = None
    memory_used: Optional[float] = None
    exit_code: Optional[int] = None
    provider: str
    message: Optional[str] = None

class CodeSnippetCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    language: str
    code: str

class CodeSnippetOut(BaseModel):
    id: int
    student_id: int
    title: str
    language: str
    code: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class CodeSubmissionOut(BaseModel):
    id: int
    student_id: int
    subject_id: Optional[int] = None
    topic_id: Optional[int] = None
    language: str
    source_code: str
    custom_input: Optional[str] = None
    status: str
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    compile_output: Optional[str] = None
    execution_time: Optional[float] = None
    memory_used: Optional[float] = None
    exit_code: Optional[int] = None
    provider: str
    created_at: datetime

    class Config:
        from_attributes = True
