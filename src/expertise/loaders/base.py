"""Base document loader interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator


@dataclass
class Document:
    """A loaded document with metadata."""
    
    content: str
    source: str  # File path or URL
    title: str | None = None
    page_number: int | None = None  # For multi-page docs
    section: str | None = None  # For structured docs
    metadata: dict = field(default_factory=dict)
    
    @property
    def word_count(self) -> int:
        """Approximate word count."""
        return len(self.content.split())
    
    @property
    def char_count(self) -> int:
        """Character count."""
        return len(self.content)
    
    def __repr__(self) -> str:
        preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"Document(source={self.source!r}, words={self.word_count}, preview={preview!r})"


class DocumentLoader(ABC):
    """Base class for document loaders."""
    
    supported_extensions: list[str] = []
    
    @abstractmethod
    def load(self, path: Path | str) -> list[Document]:
        """Load document(s) from a file path.
        
        Returns a list because some formats (like PDF) may be split into
        multiple documents (one per page).
        """
        pass
    
    @abstractmethod
    def load_text(self, text: str, source: str = "text") -> list[Document]:
        """Load from raw text content."""
        pass
    
    def can_load(self, path: Path | str) -> bool:
        """Check if this loader can handle the given file."""
        path = Path(path)
        return path.suffix.lower() in self.supported_extensions
    
    def iter_directory(self, directory: Path | str) -> Iterator[Document]:
        """Iterate over all loadable files in a directory."""
        directory = Path(directory)
        for path in directory.rglob("*"):
            if path.is_file() and self.can_load(path):
                yield from self.load(path)
