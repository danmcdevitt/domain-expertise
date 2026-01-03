"""Unified document loader that auto-detects file types."""

from pathlib import Path
from typing import Iterator

from .base import Document, DocumentLoader
from .pdf import PDFLoader
from .docx import DocxLoader
from .markdown import MarkdownLoader
from .text import TextLoader


class UnifiedLoader(DocumentLoader):
    """Unified loader that handles all supported file types.
    
    Automatically selects the appropriate loader based on file extension.
    """
    
    supported_extensions = [".pdf", ".docx", ".doc", ".md", ".markdown", ".txt", ".text"]
    
    def __init__(
        self,
        pdf_split_pages: bool = False,
        docx_include_tables: bool = True,
        markdown_split_headings: bool = False,
    ):
        """Initialize unified loader.
        
        Args:
            pdf_split_pages: Split PDFs into one document per page.
            docx_include_tables: Include table content from DOCX files.
            markdown_split_headings: Split Markdown at headings.
        """
        self.loaders = {
            ".pdf": PDFLoader(split_pages=pdf_split_pages),
            ".docx": DocxLoader(include_tables=docx_include_tables),
            ".doc": DocxLoader(include_tables=docx_include_tables),
            ".md": MarkdownLoader(split_headings=markdown_split_headings),
            ".markdown": MarkdownLoader(split_headings=markdown_split_headings),
            ".txt": TextLoader(),
            ".text": TextLoader(),
        }
    
    def load(self, path: Path | str) -> list[Document]:
        """Load document using appropriate loader."""
        path = Path(path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        ext = path.suffix.lower()
        
        if ext not in self.loaders:
            raise ValueError(f"Unsupported file type: {ext}")
        
        return self.loaders[ext].load(path)
    
    def load_text(self, text: str, source: str = "text") -> list[Document]:
        """Load from raw text using text loader."""
        return TextLoader().load_text(text, source)
    
    def load_directory(
        self,
        directory: Path | str,
        recursive: bool = True,
    ) -> list[Document]:
        """Load all supported documents from a directory.
        
        Args:
            directory: Directory to scan.
            recursive: Search subdirectories.
            
        Returns:
            List of all loaded documents.
        """
        directory = Path(directory)
        
        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")
        
        if not directory.is_dir():
            raise ValueError(f"Not a directory: {directory}")
        
        documents = []
        
        if recursive:
            files = directory.rglob("*")
        else:
            files = directory.glob("*")
        
        for path in files:
            if path.is_file() and path.suffix.lower() in self.supported_extensions:
                try:
                    docs = self.load(path)
                    documents.extend(docs)
                except Exception as e:
                    # Log error but continue with other files
                    print(f"Warning: Could not load {path}: {e}")
        
        return documents
    
    def iter_directory(self, directory: Path | str) -> Iterator[Document]:
        """Iterate over documents in directory (memory efficient)."""
        directory = Path(directory)
        
        for path in directory.rglob("*"):
            if path.is_file() and path.suffix.lower() in self.supported_extensions:
                try:
                    yield from self.load(path)
                except Exception as e:
                    print(f"Warning: Could not load {path}: {e}")


# Convenience function
def load_documents(
    path: Path | str,
    recursive: bool = True,
) -> list[Document]:
    """Load documents from a file or directory.
    
    Args:
        path: File path or directory to load.
        recursive: If directory, search subdirectories.
        
    Returns:
        List of loaded documents.
    """
    path = Path(path)
    loader = UnifiedLoader()
    
    if path.is_dir():
        return loader.load_directory(path, recursive=recursive)
    else:
        return loader.load(path)
