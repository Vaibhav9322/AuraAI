import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class MessageCreate(BaseModel):
    conversation_id: Optional[str] = None
    role: str = "user"  # 'user', 'assistant', 'system'
    content: str
    model: Optional[str] = None
    attachment_ids: Optional[List[str]] = []


class MessageEdit(BaseModel):
    message_id: str
    new_content: str = Field(..., min_length=1)


class MessageRegenerate(BaseModel):
    conversation_id: str
    model: Optional[str] = None


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    tokens: Optional[int] = 0
    created_at: datetime.datetime

    class Config:
        from_attributes = True
