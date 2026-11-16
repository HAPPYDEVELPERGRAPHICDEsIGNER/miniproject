"""
Relational Database Models for SmartEdu AI Learning Platform.
Designed using SQLAlchemy ORM with foreign keys, indexes, and cascades.
"""
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Float, DateTime, ForeignKey, Index
)
from sqlalchemy.orm import relationship
from database.engine import Base

def utc_now():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(150), nullable=False)
    role = Column(String(20), nullable=False, default="student", index=True) # student, teacher, admin
    college = Column(String(200), nullable=True)
    department = Column(String(100), nullable=True)
    semester = Column(Integer, nullable=True)
    academic_year = Column(String(20), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    # Relationships
    taught_subjects = relationship("Subject", back_populates="teacher", cascade="all, delete-orphan")
    enrollments = relationship("Enrollment", back_populates="student", cascade="all, delete-orphan")
    topic_progresses = relationship("TopicProgress", back_populates="student", cascade="all, delete-orphan")
    assignment_submissions = relationship("AssignmentSubmission", back_populates="student", cascade="all, delete-orphan")
    quiz_attempts = relationship("QuizAttempt", back_populates="student", cascade="all, delete-orphan")
    code_submissions = relationship("CodeSubmission", back_populates="student", cascade="all, delete-orphan")
    code_snippets = relationship("CodeSnippet", back_populates="student", cascade="all, delete-orphan")
    ai_logs = relationship("AIAssistanceLog", back_populates="student", cascade="all, delete-orphan")
    weakness_records = relationship("WeaknessRecord", back_populates="student", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")

class Subject(Base):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    code = Column(String(50), unique=True, index=True, nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    department = Column(String(100), nullable=False)
    semester = Column(Integer, nullable=False)
    academic_year = Column(String(20), nullable=False)
    teacher_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    # Relationships
    teacher = relationship("User", back_populates="taught_subjects")
    enrollments = relationship("Enrollment", back_populates="subject", cascade="all, delete-orphan")
    units = relationship("Unit", back_populates="subject", cascade="all, delete-orphan", order_by="Unit.order_index")
    assignments = relationship("Assignment", back_populates="subject", cascade="all, delete-orphan")
    quizzes = relationship("Quiz", back_populates="subject", cascade="all, delete-orphan")

class Enrollment(Base):
    __tablename__ = "enrollments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)
    enrolled_at = Column(DateTime(timezone=True), default=utc_now)
    is_active = Column(Boolean, default=True)

    student = relationship("User", back_populates="enrollments")
    subject = relationship("Subject", back_populates="enrollments")

    __table_args__ = (
        Index("idx_student_subject_enroll", "student_id", "subject_id", unique=True),
    )

class Unit(Base):
    __tablename__ = "units"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)
    unit_number = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    order_index = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    subject = relationship("Subject", back_populates="units")
    chapters = relationship("Chapter", back_populates="unit", cascade="all, delete-orphan", order_by="Chapter.order_index")

class Chapter(Base):
    __tablename__ = "chapters"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    unit_id = Column(Integer, ForeignKey("units.id", ondelete="CASCADE"), nullable=False)
    chapter_number = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    order_index = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    unit = relationship("Unit", back_populates="chapters")
    topics = relationship("Topic", back_populates="chapter", cascade="all, delete-orphan", order_by="Topic.order_index")

class Topic(Base):
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    chapter_id = Column(Integer, ForeignKey("chapters.id", ondelete="CASCADE"), nullable=False)
    topic_number = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    learning_objectives = Column(Text, nullable=True)
    study_content = Column(Text, nullable=True) # Notes, markdown, summaries
    resource_url = Column(String(500), nullable=True)
    is_published = Column(Boolean, default=True)
    order_index = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    chapter = relationship("Chapter", back_populates="topics")
    progress_records = relationship("TopicProgress", back_populates="topic", cascade="all, delete-orphan")

class TopicProgress(Base):
    __tablename__ = "topic_progress"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    topic_id = Column(Integer, ForeignKey("topics.id", ondelete="CASCADE"), nullable=False)
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    study_time_minutes = Column(Float, default=0.0)
    attempts_count = Column(Integer, default=1)
    last_accessed_at = Column(DateTime(timezone=True), default=utc_now)

    student = relationship("User", back_populates="topic_progresses")
    topic = relationship("Topic", back_populates="progress_records")

    __table_args__ = (
        Index("idx_student_topic_prog", "student_id", "topic_id", unique=True),
    )

class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)
    topic_id = Column(Integer, ForeignKey("topics.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    max_score = Column(Float, default=100.0)
    deadline = Column(DateTime(timezone=True), nullable=True)
    is_published = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    subject = relationship("Subject", back_populates="assignments")
    submissions = relationship("AssignmentSubmission", back_populates="assignment", cascade="all, delete-orphan")

class AssignmentSubmission(Base):
    __tablename__ = "assignment_submissions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    submitted_at = Column(DateTime(timezone=True), default=utc_now)
    score = Column(Float, nullable=True)
    feedback = Column(Text, nullable=True)
    status = Column(String(30), default="submitted") # submitted, graded

    assignment = relationship("Assignment", back_populates="submissions")
    student = relationship("User", back_populates="assignment_submissions")

    __table_args__ = (
        Index("idx_student_assignment_sub", "assignment_id", "student_id", unique=True),
    )

class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)
    topic_id = Column(Integer, ForeignKey("topics.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    time_limit_minutes = Column(Integer, default=15)
    total_marks = Column(Float, default=20.0)
    is_published = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    subject = relationship("Subject", back_populates="quizzes")
    questions = relationship("QuizQuestion", back_populates="quiz", cascade="all, delete-orphan", order_by="QuizQuestion.order_index")
    attempts = relationship("QuizAttempt", back_populates="quiz", cascade="all, delete-orphan")

class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False)
    question_text = Column(Text, nullable=False)
    question_type = Column(String(30), default="mcq") # mcq, multiple, coding
    options_json = Column(Text, nullable=False) # JSON list of choices
    correct_answer_json = Column(Text, nullable=False) # JSON correct choice(s)
    explanation = Column(Text, nullable=True)
    marks = Column(Float, default=1.0)
    order_index = Column(Integer, default=1)

    quiz = relationship("Quiz", back_populates="questions")

class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    score = Column(Float, nullable=False)
    max_score = Column(Float, nullable=False)
    answers_json = Column(Text, nullable=False)
    time_taken_seconds = Column(Integer, default=0)
    started_at = Column(DateTime(timezone=True), default=utc_now)
    completed_at = Column(DateTime(timezone=True), default=utc_now)

    quiz = relationship("Quiz", back_populates="attempts")
    student = relationship("User", back_populates="quiz_attempts")

class CodeSubmission(Base):
    __tablename__ = "code_submissions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="SET NULL"), nullable=True)
    topic_id = Column(Integer, ForeignKey("topics.id", ondelete="SET NULL"), nullable=True)
    language = Column(String(50), nullable=False)
    source_code = Column(Text, nullable=False)
    custom_input = Column(Text, nullable=True)
    status = Column(String(50), default="Pending") # Accepted, Compilation Error, Runtime Error, Time Limit Exceeded
    stdout = Column(Text, nullable=True)
    stderr = Column(Text, nullable=True)
    compile_output = Column(Text, nullable=True)
    execution_time = Column(Float, nullable=True) # in seconds
    memory_used = Column(Float, nullable=True) # in KB
    exit_code = Column(Integer, nullable=True)
    provider = Column(String(50), default="Judge0")
    created_at = Column(DateTime(timezone=True), default=utc_now, index=True)

    student = relationship("User", back_populates="code_submissions")

class CodeSnippet(Base):
    __tablename__ = "code_snippets"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(200), nullable=False)
    language = Column(String(50), nullable=False)
    code = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    student = relationship("User", back_populates="code_snippets")

class AIAssistanceLog(Base):
    __tablename__ = "ai_assistance_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="SET NULL"), nullable=True)
    topic_id = Column(Integer, ForeignKey("topics.id", ondelete="SET NULL"), nullable=True)
    user_prompt = Column(Text, nullable=False)
    ai_response = Column(Text, nullable=False)
    assistance_type = Column(String(50), default="concept") # concept, error_debug, hint, practice
    created_at = Column(DateTime(timezone=True), default=utc_now, index=True)

    student = relationship("User", back_populates="ai_logs")

class WeaknessRecord(Base):
    __tablename__ = "weakness_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)
    topic_id = Column(Integer, ForeignKey("topics.id", ondelete="SET NULL"), nullable=True)
    concept_name = Column(String(200), nullable=False)
    difficulty_level = Column(String(20), nullable=False) # High, Medium, Low
    struggle_score = Column(Float, default=0.5) # 0.0 to 1.0
    reasons_json = Column(Text, nullable=False) # List of explanations
    recommended_actions_json = Column(Text, nullable=False) # List of recommended study items
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    student = relationship("User", back_populates="weakness_records")

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(50), default="announcement") # assignment, quiz, deadline, feedback, weakness
    link_url = Column(String(300), nullable=True)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, index=True)

    user = relationship("User", back_populates="notifications")
