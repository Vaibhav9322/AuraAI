import os
import uuid
import logging
from typing import Tuple, Optional
from fastapi import UploadFile, HTTPException, status
from app.config.settings import settings
from app.files.extractors import TextExtractor

logger = logging.getLogger("aura_ai.processor")

ALLOWED_EXTENSIONS = {
    ".pdf", ".docx", ".txt", ".csv", ".json",
    ".py", ".java", ".js", ".ts", ".html", ".css", ".sql", ".md", ".yaml", ".yml"
}


class DocumentProcessor:

    @staticmethod
    def validate_file(file: UploadFile) -> str:
        """Validates filename extension and size constraints."""
        filename = file.filename or "file"
        _, ext = os.path.splitext(filename.lower())
        
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type '{ext}'. Supported formats: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
            )
        return ext

    @staticmethod
    async def process_and_save(file: UploadFile, conversation_id: str) -> Tuple[str, str, int, str, str]:
        """Saves file to disk, calculates file size, and extracts text context."""
        ext = DocumentProcessor.validate_file(file)

        # Read file contents into memory
        file_bytes = await file.read()
        file_size = len(file_bytes)

        max_size_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
        if file_size > max_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File exceeds maximum allowed size of {settings.MAX_FILE_SIZE_MB}MB."
            )

        # Generate unique storage filename
        file_id = str(uuid.uuid4())
        safe_filename = file.filename or f"upload_{file_id}{ext}"
        storage_filename = f"{file_id}_{safe_filename}"
        storage_path = os.path.join(settings.UPLOAD_DIR, storage_filename)

        # Write to uploads directory
        with open(storage_path, "wb") as f:
            f.write(file_bytes)

        # Extract text based on file format
        extracted_text = ""
        if ext == ".pdf":
            extracted_text = TextExtractor.extract_from_pdf(file_bytes)
        elif ext == ".docx":
            extracted_text = TextExtractor.extract_from_docx(file_bytes)
        elif ext == ".csv":
            extracted_text = TextExtractor.extract_from_csv(file_bytes)
        else:
            extracted_text = TextExtractor.extract_from_text(file_bytes)

        mime_type = file.content_type or "application/octet-stream"
        return file_id, safe_filename, file_size, storage_path, mime_type, extracted_text
