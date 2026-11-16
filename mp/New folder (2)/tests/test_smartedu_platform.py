"""
Comprehensive Pytest Test Suite for SmartEdu AI Platform.
Tests Authentication, RBAC, Syllabus Management, Code Execution,
AI Tutor, Quizzes, Scikit-Learn Regression Analytics, and Notifications.
"""
import pytest
from fastapi.testclient import TestClient
from main import app
from database.engine import SessionLocal
from database.seed_data import init_database_tables, seed_initial_data

@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Ensure database schema and initial data are present."""
    init_database_tables()
    with SessionLocal() as db:
        seed_initial_data(db)

@pytest.fixture
def client():
    return TestClient(app)

# ==============================================================================
# 1. Authentication & RBAC Tests
# ==============================================================================

def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "integrations" in data

def test_login_student(client):
    response = client.post("/api/auth/login", json={
        "email": "student.alex@smartedu.edu",
        "password": "Student@2026"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["role"] == "student"
    assert data["user"]["email"] == "student.alex@smartedu.edu"

def test_login_teacher(client):
    response = client.post("/api/auth/login", json={
        "email": "prof.sharma@smartedu.edu",
        "password": "Teacher@2026"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["role"] == "teacher"

def test_login_invalid_password(client):
    response = client.post("/api/auth/login", json={
        "email": "student.alex@smartedu.edu",
        "password": "WrongPassword123"
    })
    assert response.status_code == 401

def test_register_new_student(client):
    import uuid
    rand_email = f"test_{uuid.uuid4().hex[:8]}@smartedu.edu"
    response = client.post("/api/auth/register", json={
        "email": rand_email,
        "password": "StrongPassword2026!",
        "full_name": "Test User",
        "role": "student",
        "semester": 4
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == rand_email

# ==============================================================================
# 2. RBAC & Access Control
# ==============================================================================

def test_student_cannot_create_subject(client):
    # Log in as student
    login = client.post("/api/auth/login", json={
        "email": "student.alex@smartedu.edu",
        "password": "Student@2026"
    }).json()
    token = login["access_token"]

    response = client.post(
        "/api/academic/subjects",
        json={
            "code": "HACK101",
            "title": "Unauthorized Subject",
            "department": "CSE",
            "semester": 4,
            "academic_year": "2026-2027"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    # Must be forbidden for students
    assert response.status_code == 403

def test_teacher_can_create_subject(client):
    import uuid
    login = client.post("/api/auth/login", json={
        "email": "prof.sharma@smartedu.edu",
        "password": "Teacher@2026"
    }).json()
    token = login["access_token"]

    code = f"CS{uuid.uuid4().hex[:4].upper()}"
    response = client.post(
        "/api/academic/subjects",
        json={
            "code": code,
            "title": "Advanced Operating Systems",
            "department": "Computer Science & Engineering",
            "semester": 5,
            "academic_year": "2026-2027"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == code

# ==============================================================================
# 3. Syllabus & Learning System
# ==============================================================================

def test_get_subjects_and_syllabus(client):
    login = client.post("/api/auth/login", json={
        "email": "student.alex@smartedu.edu",
        "password": "Student@2026"
    }).json()
    token = login["access_token"]

    # Get enrolled subjects
    res = client.get("/api/academic/subjects", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    subjects = res.json()
    assert len(subjects) >= 1
    dsa = subjects[0]

    # Get complete syllabus tree
    s_res = client.get(f"/api/academic/subjects/{dsa['id']}/syllabus", headers={"Authorization": f"Bearer {token}"})
    assert s_res.status_code == 200
    s_data = s_res.json()
    assert "units" in s_data
    assert len(s_data["units"]) >= 1
    assert "chapters" in s_data["units"][0]
    assert "topics" in s_data["units"][0]["chapters"][0]

def test_update_topic_progress(client):
    login = client.post("/api/auth/login", json={
        "email": "student.alex@smartedu.edu",
        "password": "Student@2026"
    }).json()
    token = login["access_token"]

    # Mark topic 1 as complete with 15 mins study time
    res = client.put(
        "/api/academic/topics/1/progress",
        json={"is_completed": True, "study_time_minutes": 15.0},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["is_completed"] is True

def test_continue_learning(client):
    login = client.post("/api/auth/login", json={
        "email": "student.alex@smartedu.edu",
        "password": "Student@2026"
    }).json()
    token = login["access_token"]

    res = client.get("/api/academic/continue-learning", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["has_resume"] is True

# ==============================================================================
# 4. Personal Coding Platform & Execution
# ==============================================================================

def test_execute_python_code(client):
    login = client.post("/api/auth/login", json={
        "email": "student.alex@smartedu.edu",
        "password": "Student@2026"
    }).json()
    token = login["access_token"]

    res = client.post(
        "/api/coding/execute",
        json={
            "language": "Python",
            "source_code": "a = 5\nb = 7\nprint('SUM:', a + b)",
            "custom_input": ""
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "Accepted"
    assert "SUM: 12" in data["stdout"]

def test_save_and_retrieve_snippet(client):
    login = client.post("/api/auth/login", json={
        "email": "student.alex@smartedu.edu",
        "password": "Student@2026"
    }).json()
    token = login["access_token"]

    # Save snippet
    res = client.post(
        "/api/coding/snippets",
        json={
            "title": "Binary Search Algorithm",
            "language": "Python",
            "code": "def bsearch(arr, t): pass"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200
    snip_id = res.json()["id"]

    # List snippets
    l_res = client.get("/api/coding/snippets", headers={"Authorization": f"Bearer {token}"})
    assert l_res.status_code == 200
    snippets = l_res.json()
    assert any(s["id"] == snip_id for s in snippets)

# ==============================================================================
# 5. AI Learning Assistant & Weakness Detection
# ==============================================================================

def test_ai_tutor_chat(client):
    login = client.post("/api/auth/login", json={
        "email": "student.alex@smartedu.edu",
        "password": "Student@2026"
    }).json()
    token = login["access_token"]

    res = client.post(
        "/api/ai/chat",
        json={
            "message": "Can you explain how amortized time works in dynamic arrays?",
            "assistance_type": "concept"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200
    data = res.json()
    assert "response" in data
    assert len(data["response"]) > 20

def test_weakness_report(client):
    login = client.post("/api/auth/login", json={
        "email": "student.alex@smartedu.edu",
        "password": "Student@2026"
    }).json()
    token = login["access_token"]

    res = client.get("/api/ai/weaknesses", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert "total_weaknesses_detected" in data
    assert "weaknesses" in data

# ==============================================================================
# 6. Quizzes & Assessments
# ==============================================================================

def test_quizzes_and_submission(client):
    login = client.post("/api/auth/login", json={
        "email": "student.alex@smartedu.edu",
        "password": "Student@2026"
    }).json()
    token = login["access_token"]

    # List quizzes
    q_list = client.get("/api/assessments/quizzes", headers={"Authorization": f"Bearer {token}"}).json()
    assert len(q_list) >= 1
    quiz_id = q_list[0]["id"]

    # Get quiz details
    q_det = client.get(f"/api/assessments/quizzes/{quiz_id}", headers={"Authorization": f"Bearer {token}"}).json()
    assert len(q_det["questions"]) >= 1
    q1_id = q_det["questions"][0]["id"]

    # Submit quiz attempt
    sub_res = client.post(
        f"/api/assessments/quizzes/{quiz_id}/submit",
        json={
            "answers": {str(q1_id): "O(1)"},
            "time_taken_seconds": 120
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert sub_res.status_code == 200
    attempt_data = sub_res.json()
    assert "score" in attempt_data
    assert "answers_review" in attempt_data

# ==============================================================================
# 7. Scikit-Learn Regression Analytics & Performance Graphs
# ==============================================================================

def test_regression_analysis_service(client):
    login = client.post("/api/auth/login", json={
        "email": "student.alex@smartedu.edu",
        "password": "Student@2026"
    }).json()
    token = login["access_token"]

    res = client.get("/api/analytics/regression", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["has_sufficient_data"] is True
    assert "metrics" in data
    assert "r2_score" in data["metrics"]
    assert "plot_data" in data
    assert len(data["plot_data"]) >= 5

def test_performance_graphs_data(client):
    login = client.post("/api/auth/login", json={
        "email": "student.alex@smartedu.edu",
        "password": "Student@2026"
    }).json()
    token = login["access_token"]

    res = client.get("/api/analytics/graphs", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    graphs = res.json()
    assert "quiz_trends" in graphs
    assert "study_time" in graphs
    assert "subject_comparison" in graphs
    assert "weakness_distribution" in graphs
    assert "coding_distribution" in graphs
    assert "completion_rate" in graphs

# ==============================================================================
# 8. Notifications
# ==============================================================================

def test_notifications_workflow(client):
    login = client.post("/api/auth/login", json={
        "email": "student.alex@smartedu.edu",
        "password": "Student@2026"
    }).json()
    token = login["access_token"]

    res = client.get("/api/notifications", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    notifs = res.json()
    assert len(notifs) >= 1

    # Mark all read
    m_res = client.put("/api/notifications/mark-all-read", headers={"Authorization": f"Bearer {token}"})
    assert m_res.status_code == 200
