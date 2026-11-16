"""
FastAPI Router for Authentication, User Profiles, and System Initialization.
"""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database.engine import get_db
from database.orm_models import User
from schemas.auth_schemas import UserRegister, UserLogin, TokenResponse, UserOut
from services.auth_service import hash_password, verify_password, create_access_token, get_current_user
from config import settings

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/register", response_model=TokenResponse)
def register_user(req: UserRegister, db: Session = Depends(get_db)):
    """Registers a new student, teacher, or admin user."""
    existing = db.query(User).filter(User.email == req.email.lower()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists."
        )

    user = User(
        email=req.email.lower(),
        hashed_password=hash_password(req.password),
        full_name=req.full_name.strip(),
        role=req.role,
        college=req.college,
        department=req.department,
        semester=req.semester,
        academic_year=req.academic_year,
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    access_token = create_access_token(data={"sub": str(user.id), "role": user.role, "email": user.email})
    return {"access_token": access_token, "token_type": "bearer", "user": user}

@router.post("/login", response_model=TokenResponse)
def login_user(req: UserLogin, db: Session = Depends(get_db)):
    """Authenticates credentials and issues a JWT token."""
    user = db.query(User).filter(User.email == req.email.lower()).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account has been disabled."
        )

    access_token = create_access_token(data={"sub": str(user.id), "role": user.role, "email": user.email})
    return {"access_token": access_token, "token_type": "bearer", "user": user}

@router.get("/me", response_model=UserOut)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Returns the authenticated user's profile."""
    return current_user

@router.get("/system-status")
def get_system_status():
    """Returns diagnostics on configured providers without leaking API keys."""
    return settings.get_public_integrations_status()

@router.post("/setup-admin")
def setup_initial_admin(db: Session = Depends(get_db)):
    """Bootstraps the default administrator account if one does not exist."""
    admin = db.query(User).filter(User.role == "admin").first()
    if admin:
        return {"message": "Admin account is already initialized.", "email": admin.email}

    admin = User(
        email=settings.ADMIN_INITIAL_EMAIL.lower(),
        hashed_password=hash_password(settings.ADMIN_INITIAL_PASSWORD),
        full_name="System Administrator",
        role="admin",
        department="Central Administration",
        is_active=True
    )
    db.add(admin)
    db.commit()
    return {"message": "Initial administrator successfully initialized.", "email": admin.email}
