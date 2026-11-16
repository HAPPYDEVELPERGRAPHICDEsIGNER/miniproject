"""
Pydantic schemas for Authentication and User Management.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)
    full_name: str = Field(..., min_length=2, max_length=150)
    role: str = Field(..., pattern="^(student|teacher|admin)$")
    college: Optional[str] = "Engineering Institute of Technology"
    department: Optional[str] = "Computer Science & Engineering"
    semester: Optional[int] = Field(None, ge=1, le=12)
    academic_year: Optional[str] = "2026-2027"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"

class UserOut(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    college: Optional[str] = None
    department: Optional[str] = None
    semester: Optional[int] = None
    academic_year: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

TokenResponse.model_rebuild()
