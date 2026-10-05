import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class ConversationCreate(BaseModel):
    title: Optional[str] = "New Chat"
    model_used: Optional[str] = None


class ConversationUpdate(BaseModel):
    title: Optional[str] = None
    is_archived: Optional[bool] = None


class ConversationResponse(BaseModel):
    id: str
    user_id: int
    title: str
    is_archived: bool
    model_used: Optional[str] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True


class ConversationGrouped(BaseModel):
    today: List[ConversationResponse] = []
    yesterday: List[ConversationResponse] = []
    previous_7_days: List[ConversationResponse] = []
    older: List[ConversationResponse] = []
