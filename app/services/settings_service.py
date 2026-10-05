from typing import Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database.models import UserSettings


class UserSettingsUpdate(BaseModel):
    theme: Optional[str] = None  # 'dark', 'light'
    default_model: Optional[str] = None
    response_style: Optional[str] = None  # 'concise', 'balanced', 'creative'
    custom_system_prompt: Optional[str] = None


class UserSettingsResponse(BaseModel):
    id: int
    user_id: int
    theme: str
    default_model: str
    response_style: str
    custom_system_prompt: Optional[str] = None

    class Config:
        from_attributes = True


class SettingsService:

    @staticmethod
    def get_or_create_settings(db: Session, user_id: int) -> UserSettings:
        settings_obj = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
        if not settings_obj:
            settings_obj = UserSettings(
                user_id=user_id,
                theme="dark",
                default_model="llama-3.3-70b-versatile",
                response_style="balanced"
            )
            db.add(settings_obj)
            db.commit()
            db.refresh(settings_obj)
        return settings_obj

    @staticmethod
    def update_settings(db: Session, user_id: int, data: UserSettingsUpdate) -> UserSettings:
        settings_obj = SettingsService.get_or_create_settings(db, user_id)
        
        if data.theme:
            settings_obj.theme = data.theme
        if data.default_model:
            settings_obj.default_model = data.default_model
        if data.response_style:
            settings_obj.response_style = data.response_style
        if data.custom_system_prompt is not None:
            settings_obj.custom_system_prompt = data.custom_system_prompt

        db.commit()
        db.refresh(settings_obj)
        return settings_obj
