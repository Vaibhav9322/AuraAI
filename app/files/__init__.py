from .routes import router as files_router
from .processor import DocumentProcessor
from .extractors import TextExtractor

__all__ = ["files_router", "DocumentProcessor", "TextExtractor"]
