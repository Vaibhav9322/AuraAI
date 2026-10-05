import datetime
from typing import Optional
from pydantic import BaseModel


class AttachmentResponse(BaseModel):
    id: str
    conversation_id: str
    message_id: Optional[str] = None
    filename: str
    file_size: int
    mime_type: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True
