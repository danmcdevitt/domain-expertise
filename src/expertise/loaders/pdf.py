"""PDF document loader using PyMuPDF."""

from pathlib import Path

import fitz  # PyMuPDF

from .base import Document, DocumentLoader


class PDFLoader(DocumentLoader):
    """Load PDF documents.
    
    Can load as single document or split by pages.
    """
    
    supported_extensions = [".pdf"]
    
    def __init__(self, split_pages: bool = False):
        """Initialize PDF loader.
        
        Args:
            split_pages: If True, return one Document per page.
                        If False, return single Document with all text.
        """
        self.split_pages = split_pages
    
    def load(self, path: Path | str) -> list[Document]:
        """Load PDF from file path."""
        path = Path(path)
        
        if not path.exists():
            raise FileNotFoundError(f"PDF not found: {path}")
        
        doc = fitz.open(path)
        
        try:
            if self.split_pages:
                return self._load_by_pages(doc, str(path))
            else:
                return self._load_as_single(doc, str(path))
        finally:
            doc.close()
    
    def load_text(self, text: str, source: str = "text") -> list[Document]:
        """PDFs can't be loaded from raw text."""
        raise NotImplementedError("PDFLoader cannot load from raw text")
    
    def _load_by_pages(self, doc: fitz.Document, source: str) -> list[Document]:
        """Load as separate documents per page."""
        documents = []
        
        for page_num, page in enumerate(doc, start=1):
            text = page.get_text()
            if text.strip():  # Skip empty pages
                documents.append(Document(
                    content=text,
                    source=source,
                    title=doc.metadata.get("title"),
                    page_number=page_num,
                    metadata={
                        "total_pages": len(doc),
                        "author": doc.metadata.get("author"),
                    }
                ))
        
        return documents
    
    def _load_as_single(self, doc: fitz.Document, source: str) -> list[Document]:
        """Load as single document with all pages."""
        all_text = []
        
        for page in doc:
            text = page.get_text()
            if text.strip():
                all_text.append(text)
        
        if not all_text:
            return []
        
        return [Document(
            content="\n\n".join(all_text),
            source=source,
            title=doc.metadata.get("title"),
            metadata={
                "total_pages": len(doc),
                "author": doc.metadata.get("author"),
            }
        )]
