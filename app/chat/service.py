import uuid
import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database.models import Message, Conversation
from app.conversations.service import ConversationService, generate_title_from_text


class ChatService:

    @staticmethod
    def save_message(
        db: Session,
        conversation_id: str,
        role: str,
        content: str,
        tokens: int = 0
    ) -> Message:
        message_id = str(uuid.uuid4())
        message = Message(
            id=message_id,
            conversation_id=conversation_id,
            role=role,
            content=content,
            tokens=tokens
        )
        db.add(message)

        # Update parent conversation timestamp
        conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if conv:
            conv.updated_at = datetime.datetime.utcnow()
            if role == "user" and (conv.title == "New Chat" or not conv.title):
                conv.title = generate_title_from_text(content)

        db.commit()
        db.refresh(message)
        return message

    @staticmethod
    def get_messages_by_conversation(
        db: Session,
        conversation_id: str,
        user_id: int
    ) -> List[Message]:
        conv = ConversationService.get_conversation_by_id(db, conversation_id, user_id)
        if not conv:
            return []
        
        return db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at.asc()).all()

    @staticmethod
    def get_message_by_id(db: Session, message_id: str) -> Optional[Message]:
        return db.query(Message).filter(Message.id == message_id).first()

    @staticmethod
    def update_message_content(db: Session, message_id: str, new_content: str) -> Optional[Message]:
        msg = ChatService.get_message_by_id(db, message_id)
        if not msg:
            return None
        msg.content = new_content
        db.commit()
        db.refresh(msg)
        return msg

    @staticmethod
    def delete_messages_after_timestamp(db: Session, conversation_id: str, timestamp: datetime.datetime) -> int:
        deleted_count = db.query(Message).filter(
            Message.conversation_id == conversation_id,
            Message.created_at > timestamp
        ).delete()
        db.commit()
        return deleted_count

    @staticmethod
    def delete_last_assistant_message(db: Session, conversation_id: str) -> bool:
        last_msg = db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(desc(Message.created_at)).first()

        if last_msg and last_msg.role == "assistant":
            db.delete(last_msg)
            db.commit()
            return True
        return False

    @staticmethod
    def delete_single_message(db: Session, message_id: str, user_id: int) -> bool:
        msg = db.query(Message).filter(Message.id == message_id).first()
        if not msg:
            return False
        
        # Ensure conversation belongs to user
        conv = ConversationService.get_conversation_by_id(db, msg.conversation_id, user_id)
        if not conv:
            return False

        db.delete(msg)
        db.commit()
        return True
