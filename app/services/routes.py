from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.models import User
from app.auth.dependencies import get_current_user
from app.services.settings_service import SettingsService, UserSettingsUpdate, UserSettingsResponse

router = APIRouter(prefix="/api/settings", tags=["User Settings"])


@router.get("", response_model=UserSettingsResponse)
def get_user_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves settings for the authenticated user."""
    settings_obj = SettingsService.get_or_create_settings(db, user_id=current_user.id)
    return UserSettingsResponse.model_validate(settings_obj)


@router.patch("", response_model=UserSettingsResponse)
def update_user_settings(
    data: UserSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Updates user settings (Theme, Default Model, Response Style, System Prompt)."""
    settings_obj = SettingsService.update_settings(db, user_id=current_user.id, data=data)
    return UserSettingsResponse.model_validate(settings_obj)
