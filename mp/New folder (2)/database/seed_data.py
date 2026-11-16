"""
Database Initialization and Seed Data for SmartEdu AI Learning Platform.
Creates initial admin, professor, student accounts, syllabus hierarchy, quizzes, and historical data.
"""
import os
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import json
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from database.engine import engine, Base, SessionLocal
from database.orm_models import (
    User, Subject, Unit, Chapter, Topic, Enrollment, TopicProgress,
    Assignment, AssignmentSubmission, Quiz, QuizQuestion, QuizAttempt,
    CodeSubmission, CodeSnippet, Notification, WeaknessRecord
)
from services.auth_service import hash_password

def init_database_tables():
    """Creates all SQLAlchemy tables if they do not exist."""
    Base.metadata.create_all(bind=engine)

def seed_initial_data(db: Session):
    """Populates realistic college courses, syllabus, and user accounts if empty."""
    # Check if admin already exists
    if db.query(User).filter(User.role == "admin").first():
        return

    now = datetime.now(timezone.utc)

    # 1. Admin Account
    admin = User(
        email="admin@smartedu.edu",
        hashed_password=hash_password("Admin@SecurePass2026"),
        full_name="System Administrator",
        role="admin",
        college="National Institute of Technology",
        department="Academic Administration",
        is_active=True
    )
    db.add(admin)

    # 2. Teacher Account
    teacher = User(
        email="prof.sharma@smartedu.edu",
        hashed_password=hash_password("Teacher@2026"),
        full_name="Prof. Rajesh Sharma",
        role="teacher",
        college="National Institute of Technology",
        department="Computer Science & Engineering",
        academic_year="2026-2027",
        is_active=True
    )
    db.add(teacher)
    db.flush()

    # 3. Student Accounts
    student1 = User(
        email="student.alex@smartedu.edu",
        hashed_password=hash_password("Student@2026"),
        full_name="Alex Turner",
        role="student",
        college="National Institute of Technology",
        department="Computer Science & Engineering",
        semester=4,
        academic_year="2026-2027",
        is_active=True
    )
    student2 = User(
        email="student.priya@smartedu.edu",
        hashed_password=hash_password("Student@2026"),
        full_name="Priya Patel",
        role="student",
        college="National Institute of Technology",
        department="Computer Science & Engineering",
        semester=4,
        academic_year="2026-2027",
        is_active=True
    )
    db.add_all([student1, student2])
    db.flush()

    # 4. Subjects
    dsa_subject = Subject(
        code="CS401",
        title="Data Structures & Algorithms",
        description="Comprehensive study of linear and non-linear data structures, algorithm design paradigms, asymptotic analysis, and problem-solving.",
        department="Computer Science & Engineering",
        semester=4,
        academic_year="2026-2027",
        teacher_id=teacher.id
    )
    dbms_subject = Subject(
        code="CS402",
        title="Database Management Systems",
        description="Relational database architecture, relational algebra, SQL optimization, normalization, indexing, transaction management, and concurrency.",
        department="Computer Science & Engineering",
        semester=4,
        academic_year="2026-2027",
        teacher_id=teacher.id
    )
    db.add_all([dsa_subject, dbms_subject])
    db.flush()

    # 5. Enrollments
    db.add_all([
        Enrollment(student_id=student1.id, subject_id=dsa_subject.id),
        Enrollment(student_id=student1.id, subject_id=dbms_subject.id),
        Enrollment(student_id=student2.id, subject_id=dsa_subject.id),
        Enrollment(student_id=student2.id, subject_id=dbms_subject.id)
    ])
    db.flush()

    # 6. Syllabus Hierarchy: Unit -> Chapter -> Topic
    # --- DSA Unit 1 ---
    u1 = Unit(
        subject_id=dsa_subject.id,
        unit_number=1,
        title="Unit 1: Linear Data Structures & Complexity",
        description="Foundational linear collections, memory layouts, and asymptotic runtime analysis.",
        order_index=1
    )
    db.add(u1)
    db.flush()

    c1 = Chapter(
        unit_id=u1.id,
        chapter_number=1,
        title="Chapter 1: Dynamic Arrays & Linked Lists",
        description="Memory contiguous vs node-allocated structures.",
        order_index=1
    )
    db.add(c1)
    db.flush()

    t1 = Topic(
        chapter_id=c1.id,
        topic_number=1,
        title="Dynamic Arrays & Amortized Complexity",
        learning_objectives="Understand geometric resizing (doubling strategy), amortized O(1) appending, cache locality, and vector implementations.",
        study_content="""### Dynamic Arrays & Amortized Complexity
A **dynamic array** is a random-access list of elements whose capacity expands automatically as elements are inserted.

#### Key Principles:
1. **Contiguous Allocation:** Elements are stored in contiguous memory blocks, yielding $O(1)$ indexed reads.
2. **Geometric Growth:** When the internal capacity is reached, an array of double size is allocated ($2N$), and existing elements are copied.
3. **Amortized Analysis:** While a single resize costs $O(N)$, doing $N$ pushes costs $O(N)$ work total, meaning each push costs $O(1)$ amortized time.

```python
class DynamicArray:
    def __init__(self):
        self.capacity = 2
        self.size = 0
        self.data = [None] * self.capacity

    def push_back(self, val):
        if self.size == self.capacity:
            self._resize(self.capacity * 2)
        self.data[self.size] = val
        self.size += 1

    def _resize(self, new_cap):
        new_data = [None] * new_cap
        for i in range(self.size):
            new_data[i] = self.data[i]
        self.data = new_data
        self.capacity = new_cap
```""",
        is_published=True,
        order_index=1
    )
    t2 = Topic(
        chapter_id=c1.id,
        topic_number=2,
        title="Singly and Doubly Linked Lists",
        learning_objectives="Master pointer manipulation, node allocations, cycle detection using Floyd's Tortoise & Hare, and list reversals.",
        study_content="""### Singly and Doubly Linked Lists
Linked structures store elements across distinct heap memory allocations connected via pointers.

#### Operations:
- Insertion at Head: $O(1)$
- Search: $O(N)$
- Reversal: In-place pointer redirection using `prev`, `curr`, `next_node`.

```python
class Node:
    def __init__(self, val, next=None):
        self.val = val
        self.next = next

def reverse_list(head):
    prev = None
    curr = head
    while curr:
        nxt = curr.next
        curr.next = prev
        prev = curr
        curr = nxt
    return prev
```""",
        is_published=True,
        order_index=2
    )
    db.add_all([t1, t2])

    c2 = Chapter(
        unit_id=u1.id,
        chapter_number=2,
        title="Chapter 2: Stacks & Queues",
        description="LIFO and FIFO data structures and their system applications.",
        order_index=2
    )
    db.add(c2)
    db.flush()

    t3 = Topic(
        chapter_id=c2.id,
        topic_number=3,
        title="Stack Applications & Expression Evaluation",
        learning_objectives="Evaluate postfix expressions, parse balanced parentheses, and manage function call frames.",
        study_content="""### Stacks & Expression Evaluation
A **Stack** operates on the Last-In, First-Out (LIFO) protocol. Key operations include `push`, `pop`, and `peek`, all operating in strict $O(1)$ time.

#### Monotonic Stacks:
Used for next greater element searches in linear time $O(N)$ rather than brute force $O(N^2)$.
""",
        is_published=True,
        order_index=3
    )
    db.add(t3)

    # --- DSA Unit 2 ---
    u2 = Unit(
        subject_id=dsa_subject.id,
        unit_number=2,
        title="Unit 2: Trees & Hierarchical Structures",
        description="Tree graphs, binary search trees, balancing mechanisms (AVL/Red-Black), and heap priority queues.",
        order_index=2
    )
    db.add(u2)
    db.flush()

    c3 = Chapter(
        unit_id=u2.id,
        chapter_number=3,
        title="Chapter 3: Binary Search Trees & Heaps",
        description="Logarithmic search trees and priority queues.",
        order_index=1
    )
    db.add(c3)
    db.flush()

    t4 = Topic(
        chapter_id=c3.id,
        topic_number=4,
        title="Binary Tree Traversals (Inorder, Preorder, Postorder, BFS)",
        learning_objectives="Implement Depth-First Search traversals recursively and iteratively with explicit stack, and Breadth-First Search with queue.",
        study_content="""### Binary Tree Traversals
Traversing a binary tree visits every node exactly once.

1. **Inorder (Left, Root, Right):** Produces non-decreasing order on Binary Search Trees.
2. **Preorder (Root, Left, Right):** Useful for cloning and serializing trees.
3. **Postorder (Left, Right, Root):** Optimal for bottom-up node deletions and evaluating abstract syntax trees.
""",
        is_published=True,
        order_index=4
    )
    t5 = Topic(
        chapter_id=c3.id,
        topic_number=5,
        title="Recursion, Backtracking & Memoization",
        learning_objectives="Formulate recurrence relations, state space tree pruning, base case definitions, and overlapping subproblem caching.",
        study_content="""### Recursion & Backtracking
Recursion expresses a computational solution in terms of self-similar smaller subproblems.

#### Invariants:
- Must have one or more well-defined **base cases** to terminate recursion.
- Must guarantee state progression toward base cases to avoid call stack overflow.
""",
        is_published=True,
        order_index=5
    )
    db.add_all([t4, t5])
    db.flush()

    # 7. Quizzes and Assessments
    q1 = Quiz(
        subject_id=dsa_subject.id,
        topic_id=t1.id,
        title="Quiz 1: Linear Data Structures & Complexity",
        description="Assesses knowledge of arrays, amortized complexity, and pointer operations.",
        time_limit_minutes=15,
        total_marks=20.0,
        is_published=True
    )
    q2 = Quiz(
        subject_id=dsa_subject.id,
        topic_id=t3.id,
        title="Quiz 2: Stacks, Queues & Expressions",
        description="Evaluation of prefix/postfix, stack invariants, and queue implementations.",
        time_limit_minutes=15,
        total_marks=20.0,
        is_published=True
    )
    q3 = Quiz(
        subject_id=dsa_subject.id,
        topic_id=t4.id,
        title="Quiz 3: Tree Traversals & BST Invariants",
        description="Binary search tree search, insertion, and traversal algorithms.",
        time_limit_minutes=20,
        total_marks=25.0,
        is_published=True
    )
    q4 = Quiz(
        subject_id=dsa_subject.id,
        topic_id=t5.id,
        title="Quiz 4: Recursion & Backtracking Fundamentals",
        description="Recurrence relations, call stack behavior, and base conditions.",
        time_limit_minutes=20,
        total_marks=25.0,
        is_published=True
    )
    q5 = Quiz(
        subject_id=dsa_subject.id,
        topic_id=t2.id,
        title="Quiz 5: Linked List Pointer Algorithms",
        description="Cycle detection, fast & slow pointers, and node manipulation.",
        time_limit_minutes=15,
        total_marks=20.0,
        is_published=True
    )
    db.add_all([q1, q2, q3, q4, q5])
    db.flush()

    # Questions for Quiz 1
    db.add_all([
        QuizQuestion(
            quiz_id=q1.id,
            question_text="What is the amortized time complexity of appending an element to a dynamic array that doubles its capacity upon filling?",
            question_type="mcq",
            options_json=json.dumps(["O(1)", "O(N)", "O(log N)", "O(N^2)"]),
            correct_answer_json=json.dumps(["O(1)"]),
            explanation="Although a single resize operation requires copying N elements (O(N)), doubling the array allows N subsequent pushes without resizing, resulting in O(1) amortized time per operation.",
            marks=10.0,
            order_index=1
        ),
        QuizQuestion(
            quiz_id=q1.id,
            question_text="Which of the following data structures provides O(1) indexed random read access by memory offset?",
            question_type="mcq",
            options_json=json.dumps(["Array", "Singly Linked List", "Doubly Linked List", "Binary Search Tree"]),
            correct_answer_json=json.dumps(["Array"]),
            explanation="Arrays store elements in contiguous memory, allowing immediate calculation of element address via base + index * size.",
            marks=10.0,
            order_index=2
        )
    ])

    # Questions for Quiz 4 (Recursion)
    db.add_all([
        QuizQuestion(
            quiz_id=q4.id,
            question_text="What happens if a recursive function does not define or reach a valid base case?",
            question_type="mcq",
            options_json=json.dumps(["RecursionError / Stack Overflow", "Segmentation Fault in CPU registers", "Automatic garbage collection", "The compiler rewrites it into an iterative loop"]),
            correct_answer_json=json.dumps(["RecursionError / Stack Overflow"]),
            explanation="Without a base case, call frames are repeatedly pushed onto the program call stack until the maximum call stack limit is exceeded, triggering a stack overflow error.",
            marks=12.5,
            order_index=1
        ),
        QuizQuestion(
            quiz_id=q4.id,
            question_text="Which technique is used in recursion to store previously computed subproblem results to avoid exponential redundant computation?",
            question_type="mcq",
            options_json=json.dumps(["Memoization", "Virtual Memory Paging", "Pointer Swizzling", "Tail Inversion"]),
            correct_answer_json=json.dumps(["Memoization"]),
            explanation="Memoization caches returned subproblem values in a lookup table (e.g. hash map or array) so each subproblem is calculated only once.",
            marks=12.5,
            order_index=2
        )
    ])

    # 8. Historical Quiz Attempts & Progress for Student 1 (Alex)
    # 5 assessments to enable statistical Regression Analysis!
    db.add_all([
        TopicProgress(student_id=student1.id, topic_id=t1.id, is_completed=True, study_time_minutes=42.0, attempts_count=2, completed_at=now - timedelta(days=28)),
        TopicProgress(student_id=student1.id, topic_id=t2.id, is_completed=True, study_time_minutes=35.0, attempts_count=1, completed_at=now - timedelta(days=21)),
        TopicProgress(student_id=student1.id, topic_id=t3.id, is_completed=True, study_time_minutes=50.0, attempts_count=2, completed_at=now - timedelta(days=14)),
        TopicProgress(student_id=student1.id, topic_id=t4.id, is_completed=True, study_time_minutes=40.0, attempts_count=1, completed_at=now - timedelta(days=7)),
        TopicProgress(student_id=student1.id, topic_id=t5.id, is_completed=False, study_time_minutes=75.0, attempts_count=4, completed_at=None) # Struggling on Recursion!
    ])

    # 5 Quiz attempts for Student 1
    db.add_all([
        QuizAttempt(quiz_id=q1.id, student_id=student1.id, score=18.0, max_score=20.0, answers_json=json.dumps({}), time_taken_seconds=420, completed_at=now - timedelta(days=25)),
        QuizAttempt(quiz_id=q2.id, student_id=student1.id, score=17.0, max_score=20.0, answers_json=json.dumps({}), time_taken_seconds=510, completed_at=now - timedelta(days=18)),
        QuizAttempt(quiz_id=q3.id, student_id=student1.id, score=21.0, max_score=25.0, answers_json=json.dumps({}), time_taken_seconds=630, completed_at=now - timedelta(days=12)),
        QuizAttempt(quiz_id=q5.id, student_id=student1.id, score=16.0, max_score=20.0, answers_json=json.dumps({}), time_taken_seconds=490, completed_at=now - timedelta(days=6)),
        QuizAttempt(quiz_id=q4.id, student_id=student1.id, score=10.0, max_score=25.0, answers_json=json.dumps({}), time_taken_seconds=780, completed_at=now - timedelta(days=1)) # Lower score on recursion
    ])

    # Code Submissions for Student 1
    db.add_all([
        CodeSubmission(
            student_id=student1.id,
            subject_id=dsa_subject.id,
            topic_id=t1.id,
            language="Python",
            source_code="print('Dynamic array implementation')",
            status="Accepted",
            stdout="Dynamic array implementation\n",
            execution_time=0.035,
            memory_used=12300.0,
            provider="Judge0 Cloud",
            created_at=now - timedelta(days=20)
        ),
        CodeSubmission(
            student_id=student1.id,
            subject_id=dsa_subject.id,
            topic_id=t5.id,
            language="Python",
            source_code="def recurse(n):\n    return recurse(n+1)\nrecurse(1)",
            status="Runtime Error",
            stderr="RecursionError: maximum recursion depth exceeded",
            execution_time=0.12,
            memory_used=14500.0,
            provider="Judge0 Cloud",
            created_at=now - timedelta(days=2)
        )
    ])

    # Seed Weakness Record for Student 1 (Recursion)
    db.add(
        WeaknessRecord(
            student_id=student1.id,
            subject_id=dsa_subject.id,
            topic_id=t5.id,
            concept_name="Recursion, Backtracking & Memoization",
            difficulty_level="High",
            struggle_score=0.82,
            reasons_json=json.dumps([
                "Scored 40.0% on Quiz 4: Recursion & Backtracking Fundamentals.",
                "Encountered RecursionError (stack overflow) in code submissions.",
                "High study duration (75 mins) without topic completion."
            ]),
            recommended_actions_json=json.dumps([
                "Review base case mechanics and call-stack unwinding in study notes.",
                "Practice writing simple recursion tree traces on paper.",
                "Ask AI Tutor for step-by-step Socratic hints."
            ]),
            updated_at=now
        )
    )

    # Notifications
    db.add_all([
        Notification(
            user_id=student1.id,
            title="Weakness Alert: Recursion Practice Recommended",
            message="Your performance indicators suggest revision is needed on 'Recursion & Backtracking'. Check your personalized study recommendations.",
            notification_type="weakness",
            link_url="#analytics",
            is_read=False
        ),
        Notification(
            user_id=student1.id,
            title="New Assignment: DSA Lab 1",
            message="Prof. Rajesh Sharma published 'Binary Tree Traversals Implementation'. Due in 7 days.",
            notification_type="assignment",
            link_url="#assignments",
            is_read=False
        ),
        Notification(
            user_id=teacher.id,
            title="Student Attention Alert",
            message="Student Alex Turner was flagged for High difficulty in 'Recursion & Backtracking'.",
            notification_type="weakness",
            link_url="#teacher-students",
            is_read=False
        )
    ])

    db.commit()
    print("Database successfully seeded with realistic academic data!")

if __name__ == "__main__":
    init_database_tables()
    with SessionLocal() as session:
        seed_initial_data(session)
