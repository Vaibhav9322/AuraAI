import uuid
import datetime
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_

from app.database.models import Conversation
from app.conversations.schemas import ConversationCreate, ConversationUpdate, ConversationGrouped, ConversationResponse


def generate_title_from_text(text: str) -> str:
    """Generates a clean title snippet from the first message text."""
    clean_text = text.strip().replace('\n', ' ')
    if len(clean_text) <= 35:
        return clean_text.capitalize() if clean_text else "New Chat"
    
    # Truncate to nearest word
    words = clean_text[:35].split(' ')
    if len(words) > 1:
        words.pop()
    return " ".join(words).capitalize() + "..."


class ConversationService:

    @staticmethod
    def create_conversation(db: Session, user_id: int, data: ConversationCreate) -> Conversation:
        conv_id = str(uuid.uuid4())
        conv = Conversation(
            id=conv_id,
            user_id=user_id,
            title=data.title or "New Chat",
            model_used=data.model_used,
            is_archived=False
        )
        db.add(conv)
        db.commit()
        db.refresh(conv)
        return conv

    @staticmethod
    def get_conversation_by_id(db: Session, conversation_id: str, user_id: int) -> Optional[Conversation]:
        return db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id
        ).first()

    @staticmethod
    def list_user_conversations(
        db: Session,
        user_id: int,
        search: Optional[str] = None,
        archived: bool = False
    ) -> List[Conversation]:
        query = db.query(Conversation).filter(
            Conversation.user_id == user_id,
            Conversation.is_archived == archived
        )
        if search:
            query = query.filter(Conversation.title.ilike(f"%{search}%"))
        
        return query.order_by(desc(Conversation.updated_at)).all()

    @staticmethod
    def group_conversations_by_date(conversations: List[Conversation]) -> ConversationGrouped:
        now = datetime.datetime.utcnow()
        today_start = datetime.datetime(now.year, now.month, now.day)
        yesterday_start = today_start - datetime.timedelta(days=1)
        seven_days_ago = today_start - datetime.timedelta(days=7)

        grouped = ConversationGrouped()

        for c in conversations:
            item = ConversationResponse.model_validate(c)
            if c.updated_at >= today_start:
                grouped.today.append(item)
            elif c.updated_at >= yesterday_start:
                grouped.yesterday.append(item)
            elif c.updated_at >= seven_days_ago:
                grouped.previous_7_days.append(item)
            else:
                grouped.older.append(item)

        return grouped

    @staticmethod
    def update_conversation(
        db: Session,
        conversation_id: str,
        user_id: int,
        data: ConversationUpdate
    ) -> Optional[Conversation]:
        conv = ConversationService.get_conversation_by_id(db, conversation_id, user_id)
        if not conv:
            return None

        if data.title is not None:
            conv.title = data.title.strip()
        if data.is_archived is not None:
            conv.is_archived = data.is_archived
        
        conv.updated_at = datetime.datetime.utcnow()
        db.commit()
        db.refresh(conv)
        return conv

    @staticmethod
    def delete_conversation(db: Session, conversation_id: str, user_id: int) -> bool:
        conv = ConversationService.get_conversation_by_id(db, conversation_id, user_id)
        if not conv:
            return False
        db.delete(conv)
        db.commit()
        return True
