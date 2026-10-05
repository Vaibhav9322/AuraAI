from typing import List, Optional, Union
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.models import User
from app.auth.dependencies import get_current_user
from app.conversations.schemas import (
    ConversationCreate, ConversationUpdate, ConversationResponse, ConversationGrouped
)
from app.conversations.service import ConversationService

router = APIRouter(prefix="/api/conversations", tags=["Conversations"])


@router.get("", response_model=Union[List[ConversationResponse], ConversationGrouped])
def list_conversations(
    search: Optional[str] = Query(None, description="Search conversations by title"),
    archived: bool = Query(False, description="Filter archived conversations"),
    grouped: bool = Query(True, description="Group conversations by date (Today, Yesterday, etc.)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves all conversations for the authenticated user."""
    conversations = ConversationService.list_user_conversations(
        db, user_id=current_user.id, search=search, archived=archived
    )
    if grouped:
        return ConversationService.group_conversations_by_date(conversations)
    return [ConversationResponse.model_validate(c) for c in conversations]


@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
def create_conversation(
    data: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Creates a new conversation session."""
    conv = ConversationService.create_conversation(db, user_id=current_user.id, data=data)
    return ConversationResponse.model_validate(conv)


@router.get("/{conversation_id}", response_model=ConversationResponse)
def get_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves a single conversation by ID."""
    conv = ConversationService.get_conversation_by_id(db, conversation_id=conversation_id, user_id=current_user.id)
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return ConversationResponse.model_validate(conv)


@router.patch("/{conversation_id}", response_model=ConversationResponse)
def update_conversation(
    conversation_id: str,
    data: ConversationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Renames or updates archive status of a conversation."""
    conv = ConversationService.update_conversation(db, conversation_id=conversation_id, user_id=current_user.id, data=data)
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return ConversationResponse.model_validate(conv)


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Deletes a conversation and all associated messages."""
    success = ConversationService.delete_conversation(db, conversation_id=conversation_id, user_id=current_user.id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return None
