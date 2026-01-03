"""Document loaders for ingesting source material."""

from .base import DocumentLoader, Document
from .pdf import PDFLoader
from .docx import DocxLoader
from .markdown import MarkdownLoader
from .text import TextLoader
from .unified import UnifiedLoader

__all__ = [
    "DocumentLoader",
    "Document",
    "PDFLoader",
    "DocxLoader",
    "MarkdownLoader",
    "TextLoader",
    "UnifiedLoader",
]
