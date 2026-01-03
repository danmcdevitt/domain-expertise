"""Markdown document loader."""

import re
from pathlib import Path

from .base import Document, DocumentLoader


class MarkdownLoader(DocumentLoader):
    """Load Markdown documents.
    
    Can extract frontmatter and split by headings.
    """
    
    supported_extensions = [".md", ".markdown"]
    
    def __init__(
        self,
        split_headings: bool = False,
        heading_level: int = 2,
        extract_frontmatter: bool = True,
    ):
        """Initialize Markdown loader.
        
        Args:
            split_headings: If True, split into separate docs at headings.
            heading_level: Heading level to split at (1-6).
            extract_frontmatter: Parse YAML frontmatter into metadata.
        """
        self.split_headings = split_headings
        self.heading_level = heading_level
        self.extract_frontmatter = extract_frontmatter
    
    def load(self, path: Path | str) -> list[Document]:
        """Load Markdown from file path."""
        path = Path(path)
        
        if not path.exists():
            raise FileNotFoundError(f"Markdown file not found: {path}")
        
        content = path.read_text(encoding="utf-8")
        return self.load_text(content, source=str(path))
    
    def load_text(self, text: str, source: str = "text") -> list[Document]:
        """Load from raw Markdown text."""
        content = text
        metadata = {}
        title = None
        
        # Extract frontmatter if present
        if self.extract_frontmatter:
            content, metadata = self._extract_frontmatter(content)
            title = metadata.get("title")
        
        # Extract title from first H1 if not in frontmatter
        if not title:
            title = self._extract_title(content)
        
        if self.split_headings:
            return self._split_by_headings(content, source, title, metadata)
        else:
            return [Document(
                content=content.strip(),
                source=source,
                title=title,
                metadata=metadata,
            )]
    
    def _extract_frontmatter(self, content: str) -> tuple[str, dict]:
        """Extract YAML frontmatter from content."""
        if not content.startswith("---"):
            return content, {}
        
        # Find closing ---
        match = re.match(r"^---\n(.*?)\n---\n?(.*)$", content, re.DOTALL)
        if not match:
            return content, {}
        
        frontmatter_text = match.group(1)
        content = match.group(2)
        
        # Simple YAML parsing (key: value pairs)
        metadata = {}
        for line in frontmatter_text.split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()
                # Handle lists (simple case)
                if value.startswith("[") and value.endswith("]"):
                    value = [v.strip().strip("'\"") for v in value[1:-1].split(",")]
                metadata[key] = value
        
        return content, metadata
    
    def _extract_title(self, content: str) -> str | None:
        """Extract title from first H1 heading."""
        match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        return match.group(1).strip() if match else None
    
    def _split_by_headings(
        self,
        content: str,
        source: str,
        title: str | None,
        metadata: dict,
    ) -> list[Document]:
        """Split content at specified heading level."""
        pattern = r"^(#{" + str(self.heading_level) + r"})\s+(.+)$"
        
        documents = []
        sections = re.split(pattern, content, flags=re.MULTILINE)
        
        # First section (before any matching headings)
        if sections[0].strip():
            documents.append(Document(
                content=sections[0].strip(),
                source=source,
                title=title,
                section="Introduction",
                metadata=metadata,
            ))
        
        # Process heading/content pairs
        i = 1
        while i < len(sections) - 1:
            heading_marker = sections[i]  # e.g., "##"
            heading_text = sections[i + 1]  # e.g., "Section Title"
            
            # Find content until next heading
            if i + 2 < len(sections):
                section_content = sections[i + 2]
            else:
                section_content = ""
            
            full_content = f"{heading_marker} {heading_text}\n\n{section_content}".strip()
            
            documents.append(Document(
                content=full_content,
                source=source,
                title=title,
                section=heading_text.strip(),
                metadata=metadata,
            ))
            
            i += 3
        
        return documents
