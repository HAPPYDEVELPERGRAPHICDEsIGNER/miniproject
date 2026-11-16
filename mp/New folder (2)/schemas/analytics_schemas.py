"""
Pydantic schemas for Regression Analysis, Graphs & Notifications.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class RegressionModelMetrics(BaseModel):
    r2_score: float
    mae: float
    rmse: float
    data_points_count: int
    has_sufficient_data: bool
    status_message: str

class RegressionPoint(BaseModel):
    label: str
    study_hours: float
    quiz_average: float
    coding_success_rate: float
    actual_score: float
    predicted_score: float

class RegressionAnalysisResponse(BaseModel):
    student_id: Optional[int] = None
    student_name: Optional[str] = None
    has_sufficient_data: bool
    data_points_count: int
    required_points: int = 5
    metrics: RegressionModelMetrics
    coefficients: Dict[str, float]
    intercept: float
    plot_data: List[RegressionPoint]
    disclaimer: str = "Predictions are statistical estimates based on historical trends, not guaranteed academic outcomes."

class AnalyticsSummary(BaseModel):
    enrolled_subjects_count: int
    overall_completion_rate: float
    total_study_time_hours: float
    coding_submissions_count: int
    coding_success_rate: float
    average_quiz_score: float
    weakness_count: int

class NotificationOut(BaseModel):
    id: int
    user_id: int
    title: str
    message: str
    notification_type: str
    link_url: Optional[str] = None
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True
