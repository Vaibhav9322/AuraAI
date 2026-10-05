import json
import asyncio
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database.connection import get_db, SessionLocal
from app.database.models import User, Attachment
from app.auth.dependencies import get_current_user
from app.chat.schemas import MessageCreate, MessageEdit, MessageRegenerate, MessageResponse
from app.chat.service import ChatService
from app.conversations.service import ConversationService
from app.conversations.schemas import ConversationCreate
from app.ai.factory import AIProviderFactory

router = APIRouter(prefix="/api/chat", tags=["Chat & Streaming"])


@router.post("")
async def send_chat_message(
    payload: MessageCreate = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Processes user chat input, handles file attachment context, saves message, and streams AI response via SSE."""
    user_text = payload.content.strip()
    if not user_text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Message content cannot be empty.")

    conv_id = payload.conversation_id
    if not conv_id:
        conv = ConversationService.create_conversation(
            db,
            user_id=current_user.id,
            data=ConversationCreate(title=user_text[:35], model_used=payload.model)
        )
        conv_id = conv.id
    else:
        conv = ConversationService.get_conversation_by_id(db, conversation_id=conv_id, user_id=current_user.id)
        if not conv:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")

    # Link any pending uploaded attachments to this message
    if payload.attachment_ids:
        db.query(Attachment).filter(
            Attachment.id.in_(payload.attachment_ids),
            Attachment.conversation_id == conv_id
        ).update({"conversation_id": conv_id}, synchronize_session=False)
        db.commit()

    # 1. Save user message
    user_msg = ChatService.save_message(
        db,
        conversation_id=conv_id,
        role="user",
        content=user_text
    )

    # 2. Build conversation history context
    history_messages = ChatService.get_messages_by_conversation(db, conversation_id=conv_id, user_id=current_user.id)
    ai_context = []

    # Fetch document attachments for context injection
    attachments = db.query(Attachment).filter(Attachment.conversation_id == conv_id).all()
    if attachments:
        doc_context_str = "--- ATTACHED DOCUMENTS & FILE CONTEXT ---\n"
        for att in attachments:
            if att.extracted_text:
                doc_context_str += f"\nFile: {att.filename}\nExtracted Content:\n{att.extracted_text}\n"
        doc_context_str += "--- END OF DOCUMENTS ---\n\n"
        ai_context.append({"role": "system", "content": f"You have access to the following user-uploaded documents to answer questions accurately:\n{doc_context_str}"})

    for msg in history_messages:
        ai_context.append({"role": msg.role, "content": msg.content})

    # 3. Stream AI response
    provider = AIProviderFactory.get_provider()

    async def event_generator():
        full_assistant_text = ""
        try:
            yield f"data: {json.dumps({'type': 'meta', 'conversation_id': conv_id, 'user_message_id': user_msg.id})}\n\n"

            async for token in provider.stream(ai_context, model=payload.model):
                full_assistant_text += token
                yield f"data: {json.dumps({'type': 'chunk', 'content': token})}\n\n"

            save_db = SessionLocal()
            try:
                assistant_msg = ChatService.save_message(
                    save_db,
                    conversation_id=conv_id,
                    role="assistant",
                    content=full_assistant_text
                )
                yield f"data: {json.dumps({'type': 'done', 'conversation_id': conv_id, 'message_id': assistant_msg.id})}\n\n"
            finally:
                save_db.close()

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/regenerate")
async def regenerate_last_response(
    payload: MessageRegenerate = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Deletes the last assistant message and streams a fresh AI response."""
    conv = ConversationService.get_conversation_by_id(db, conversation_id=payload.conversation_id, user_id=current_user.id)
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")

    ChatService.delete_last_assistant_message(db, payload.conversation_id)

    history_messages = ChatService.get_messages_by_conversation(db, conversation_id=payload.conversation_id, user_id=current_user.id)
    if not history_messages:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No message history available.")

    ai_context = []
    attachments = db.query(Attachment).filter(Attachment.conversation_id == payload.conversation_id).all()
    if attachments:
        doc_context_str = "--- ATTACHED DOCUMENTS & FILE CONTEXT ---\n"
        for att in attachments:
            if att.extracted_text:
                doc_context_str += f"\nFile: {att.filename}\nExtracted Content:\n{att.extracted_text}\n"
        doc_context_str += "--- END OF DOCUMENTS ---\n\n"
        ai_context.append({"role": "system", "content": f"You have access to the following user-uploaded documents to answer questions accurately:\n{doc_context_str}"})

    for msg in history_messages:
        ai_context.append({"role": msg.role, "content": msg.content})

    provider = AIProviderFactory.get_provider()

    async def event_generator():
        full_assistant_text = ""
        try:
            yield f"data: {json.dumps({'type': 'meta', 'conversation_id': payload.conversation_id})}\n\n"

            async for token in provider.stream(ai_context, model=payload.model):
                full_assistant_text += token
                yield f"data: {json.dumps({'type': 'chunk', 'content': token})}\n\n"

            save_db = SessionLocal()
            try:
                assistant_msg = ChatService.save_message(
                    save_db,
                    conversation_id=payload.conversation_id,
                    role="assistant",
                    content=full_assistant_text
                )
                yield f"data: {json.dumps({'type': 'done', 'conversation_id': payload.conversation_id, 'message_id': assistant_msg.id})}\n\n"
            finally:
                save_db.close()

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/edit")
async def edit_user_message(
    payload: MessageEdit = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Edits a previous user message, truncates subsequent branch messages, and streams new AI response."""
    target_msg = ChatService.get_message_by_id(db, payload.message_id)
    if not target_msg or target_msg.role != "user":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User message not found.")

    conv = ConversationService.get_conversation_by_id(db, conversation_id=target_msg.conversation_id, user_id=current_user.id)
    if not conv:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    ChatService.update_message_content(db, payload.message_id, payload.new_content.strip())
    ChatService.delete_messages_after_timestamp(db, target_msg.conversation_id, target_msg.created_at)

    history_messages = ChatService.get_messages_by_conversation(db, conversation_id=target_msg.conversation_id, user_id=current_user.id)
    ai_context = []
    attachments = db.query(Attachment).filter(Attachment.conversation_id == target_msg.conversation_id).all()
    if attachments:
        doc_context_str = "--- ATTACHED DOCUMENTS & FILE CONTEXT ---\n"
        for att in attachments:
            if att.extracted_text:
                doc_context_str += f"\nFile: {att.filename}\nExtracted Content:\n{att.extracted_text}\n"
        doc_context_str += "--- END OF DOCUMENTS ---\n\n"
        ai_context.append({"role": "system", "content": f"You have access to the following user-uploaded documents to answer questions accurately:\n{doc_context_str}"})

    for msg in history_messages:
        ai_context.append({"role": msg.role, "content": msg.content})

    provider = AIProviderFactory.get_provider()

    async def event_generator():
        full_assistant_text = ""
        try:
            yield f"data: {json.dumps({'type': 'meta', 'conversation_id': target_msg.conversation_id})}\n\n"

            async for token in provider.stream(ai_context):
                full_assistant_text += token
                yield f"data: {json.dumps({'type': 'chunk', 'content': token})}\n\n"

            save_db = SessionLocal()
            try:
                assistant_msg = ChatService.save_message(
                    save_db,
                    conversation_id=target_msg.conversation_id,
                    role="assistant",
                    content=full_assistant_text
                )
                yield f"data: {json.dumps({'type': 'done', 'conversation_id': target_msg.conversation_id, 'message_id': assistant_msg.id})}\n\n"
            finally:
                save_db.close()

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.delete("/messages/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_single_message(
    message_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Deletes an individual message from a conversation."""
    success = ChatService.delete_single_message(db, message_id=message_id, user_id=current_user.id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found.")
    return None
