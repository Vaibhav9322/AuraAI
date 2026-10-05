import os
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.models import User, Attachment, Conversation
from app.auth.dependencies import get_current_user
from app.files.schemas import AttachmentResponse
from app.files.processor import DocumentProcessor
from app.conversations.service import ConversationService
from app.conversations.schemas import ConversationCreate

router = APIRouter(prefix="/api/files", tags=["Files"])


@router.post("/upload", response_model=AttachmentResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    conversation_id: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Uploads document/file, extracts text content, and persists metadata in MySQL."""
    # Ensure or create conversation
    if not conversation_id:
        conv = ConversationService.create_conversation(
            db,
            user_id=current_user.id,
            data=ConversationCreate(title=f"Analysis: {file.filename or 'File'}")
        )
        conversation_id = conv.id
    else:
        conv = ConversationService.get_conversation_by_id(db, conversation_id=conversation_id, user_id=current_user.id)
        if not conv:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")

    # Process and extract text
    file_id, filename, file_size, storage_path, mime_type, extracted_text = await DocumentProcessor.process_and_save(file, conversation_id)

    # Save attachment entity in database
    attachment = Attachment(
        id=file_id,
        conversation_id=conversation_id,
        filename=filename,
        file_path=storage_path,
        file_size=file_size,
        mime_type=mime_type,
        extracted_text=extracted_text
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)

    return AttachmentResponse.model_validate(attachment)


@router.delete("/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_file(
    attachment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Deletes uploaded file from storage and database."""
    att = db.query(Attachment).filter(Attachment.id == attachment_id).first()
    if not att:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File attachment not found.")

    # Ensure conversation belongs to user
    conv = ConversationService.get_conversation_by_id(db, conversation_id=att.conversation_id, user_id=current_user.id)
    if not conv:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    # Remove file from disk
    if os.path.exists(att.file_path):
        try:
            os.remove(att.file_path)
        except Exception as e:
            pass

    db.delete(att)
    db.commit()
    return None
