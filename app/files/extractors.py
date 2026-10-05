import io
import logging
from typing import Optional

logger = logging.getLogger("aura_ai.extractors")


class TextExtractor:
    @staticmethod
    def extract_from_pdf(file_bytes: bytes) -> str:
        """Extracts text from PDF documents using PyMuPDF (fitz)."""
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            text_chunks = []
            for page in doc:
                text_chunks.append(page.get_text())
            doc.close()
            return "\n".join(text_chunks).strip()
        except Exception as e:
            logger.error(f"PDF extraction error: {e}")
            return f"[Error extracting PDF text: {str(e)}]"

    @staticmethod
    def extract_from_docx(file_bytes: bytes) -> str:
        """Extracts text from Microsoft Word .docx documents using python-docx."""
        try:
            import docx
            doc = docx.Document(io.BytesIO(file_bytes))
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            return "\n".join(paragraphs).strip()
        except Exception as e:
            logger.error(f"DOCX extraction error: {e}")
            return f"[Error extracting DOCX text: {str(e)}]"

    @staticmethod
    def extract_from_csv(file_bytes: bytes) -> str:
        """Extracts summary and data preview from CSV spreadsheets using pandas."""
        try:
            import pandas as pd
            df = pd.read_csv(io.BytesIO(file_bytes))
            summary = f"CSV Dimensions: {df.shape[0]} rows, {df.shape[1]} columns.\n"
            summary += f"Columns: {', '.join(df.columns.tolist())}\n\n"
            summary += "Head Sample:\n" + df.head(15).to_string()
            return summary
        except Exception as e:
            logger.error(f"CSV extraction error: {e}")
            # Fallback to plain text reading
            try:
                return file_bytes.decode('utf-8', errors='ignore')
            except Exception:
                return f"[Error extracting CSV text: {str(e)}]"

    @staticmethod
    def extract_from_text(file_bytes: bytes) -> str:
        """Extracts plain text from text, code, JSON, HTML, CSS files."""
        try:
            return file_bytes.decode('utf-8')
        except UnicodeDecodeError:
            try:
                return file_bytes.decode('latin-1')
            except Exception as e:
                return f"[Error decoding text file: {str(e)}]"
