from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database.connection import get_db
from app.database.models import User, UserSettings
from app.auth.schemas import UserCreate, UserLogin, UserResponse, TokenResponse, MessageResponse
from app.auth.security import hash_password, verify_password, create_access_token
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register_user(user_in: UserCreate, response: Response, db: Session = Depends(get_db)):
    """Registers a new user, creates default user settings, sets HTTP-only auth cookie and returns JWT."""
    # Check if email or username already registered
    existing_user = db.query(User).filter(
        or_(User.email == user_in.email.lower(), User.username == user_in.username.lower())
    ).first()

    if existing_user:
        if existing_user.email.lower() == user_in.email.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email address already exists."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username is already taken. Please choose another."
            )

    # Create new user entity with Argon2 hashed password
    hashed_pwd = hash_password(user_in.password)
    user = User(
        email=user_in.email.lower(),
        username=user_in.username,
        password_hash=hashed_pwd,
        is_active=True
    )
    db.add(user)
    db.flush()  # Flush to obtain user.id

    # Create default user settings
    user_settings = UserSettings(
        user_id=user.id,
        theme="dark",
        default_model="llama-3.3-70b-versatile",
        response_style="balanced"
    )
    db.add(user_settings)
    db.commit()
    db.refresh(user)

    # Generate JWT token
    token = create_access_token(data={"sub": str(user.id), "username": user.username})

    # Set secure HTTP-only cookie
    response.set_cookie(
        key="access_token",
        value=f"Bearer {token}",
        httponly=True,
        max_age=86400,  # 24 hours
        samesite="lax",
        secure=False  # Set to True in HTTPS production environments
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.post("/login", response_model=TokenResponse)
def login_user(credentials: UserLogin, response: Response, db: Session = Depends(get_db)):
    """Authenticates user via email or username and sets HTTP-only JWT auth cookie."""
    identifier = credentials.email_or_username.strip().lower()
    
    # Query by email or username
    user = db.query(User).filter(
        or_(User.email == identifier, User.username == identifier)
    ).first()

    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email/username or password."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated. Please contact support."
        )

    # Generate JWT token
    token = create_access_token(data={"sub": str(user.id), "username": user.username})

    # Set secure HTTP-only cookie
    response.set_cookie(
        key="access_token",
        value=f"Bearer {token}",
        httponly=True,
        max_age=86400,
        samesite="lax",
        secure=False
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.post("/logout", response_model=MessageResponse)
def logout_user(response: Response):
    """Logs out user by clearing the authentication HTTP-only cookie."""
    response.delete_cookie(key="access_token")
    return MessageResponse(message="Successfully logged out.")


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Retrieves profile of currently authenticated user."""
    return UserResponse.model_validate(current_user)
