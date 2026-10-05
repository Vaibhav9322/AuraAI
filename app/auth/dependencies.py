from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.models import User
from app.auth.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def get_token_from_request(request: Request, header_token: Optional[str] = Depends(oauth2_scheme)) -> Optional[str]:
    """Extracts JWT token from Authorization header or HTTP-only Cookie."""
    if header_token:
        return header_token
    cookie_token = request.cookies.get("access_token")
    if cookie_token:
        # Strip "Bearer " prefix if stored in cookie with prefix
        if cookie_token.startswith("Bearer "):
            return cookie_token[7:]
        return cookie_token
    return None


def get_current_user(
    request: Request,
    token: Optional[str] = Depends(get_token_from_request),
    db: Session = Depends(get_db)
) -> User:
    """Dependency that returns authenticated user or raises 401 Unauthorized exception."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception
    
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    
    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception
        
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive")
        
    return user


def get_current_user_optional(
    request: Request,
    token: Optional[str] = Depends(get_token_from_request),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Optional dependency that returns user if authenticated, or None if guest."""
    if not token:
        return None
    try:
        return get_current_user(request=request, token=token, db=db)
    except HTTPException:
        return None
