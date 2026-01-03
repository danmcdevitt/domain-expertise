"""Plain text document loader."""

from pathlib import Path

from .base import Document, DocumentLoader


class TextLoader(DocumentLoader):
    """Load plain text documents.
    
    Simple loader for .txt files and raw text.
    """
    
    supported_extensions = [".txt", ".text"]
    
    def __init__(self, encoding: str = "utf-8"):
        """Initialize text loader.
        
        Args:
            encoding: File encoding to use.
        """
        self.encoding = encoding
    
    def load(self, path: Path | str) -> list[Document]:
        """Load text from file path."""
        path = Path(path)
        
        if not path.exists():
            raise FileNotFoundError(f"Text file not found: {path}")
        
        try:
            content = path.read_text(encoding=self.encoding)
        except UnicodeDecodeError:
            # Try with different encoding
            content = path.read_text(encoding="latin-1")
        
        return self.load_text(content, source=str(path))
    
    def load_text(self, text: str, source: str = "text") -> list[Document]:
        """Load from raw text."""
        if not text.strip():
            return []
        
        # Try to extract title from first line if it looks like a title
        lines = text.strip().split("\n")
        title = None
        
        if len(lines) > 1:
            first_line = lines[0].strip()
            # Heuristic: short first line followed by blank line is likely a title
            if len(first_line) < 100 and (len(lines) == 1 or not lines[1].strip()):
                title = first_line
        
        return [Document(
            content=text.strip(),
            source=source,
            title=title,
        )]
