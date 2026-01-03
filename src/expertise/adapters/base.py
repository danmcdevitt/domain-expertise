"""
Base adapter interface for vector stores.
"""

from abc import ABC, abstractmethod
from typing import Any

from ..types import ContrastExample


class VectorStoreAdapter(ABC):
    """Abstract base class for vector store adapters."""

    @abstractmethod
    def index(self, examples: list[ContrastExample]) -> int:
        """
        Index examples into the vector store.

        Args:
            examples: List of contrast examples to index

        Returns:
            Number of examples indexed
        """
        pass

    @abstractmethod
    def search(
        self,
        query: str,
        domain: str | None = None,
        category: str | None = None,
        limit: int = 5,
    ) -> list[ContrastExample]:
        """
        Search for relevant examples.

        Args:
            query: Search query text
            domain: Filter by domain
            category: Filter by category
            limit: Maximum number of results

        Returns:
            List of matching examples with similarity scores
        """
        pass

    @abstractmethod
    def delete_domain(self, domain: str) -> int:
        """
        Delete all examples for a domain.

        Args:
            domain: Domain name to delete

        Returns:
            Number of examples deleted
        """
        pass

    @abstractmethod
    def count(self, domain: str | None = None) -> int:
        """
        Count indexed examples.

        Args:
            domain: Optional domain to filter by

        Returns:
            Number of examples
        """
        pass

    def get_embedding(self, text: str) -> list[float]:
        """Get embedding for text using OpenAI."""
        import openai

        client = openai.OpenAI()
        response = client.embeddings.create(
            model="text-embedding-ada-002",
            input=text,
        )
        return response.data[0].embedding

    def example_to_text(self, example: ContrastExample) -> str:
        """Convert example to text for embedding."""
        parts = [
            f"Domain: {example.domain}",
            f"Category: {example.category}",
            f"Tags: {', '.join(example.tags)}",
            f"WEAK: {example.weak_content}",
            f"STRONG: {example.strong_content}",
            f"Teaching: {example.teaching_point}",
            f"Apply when: {example.when_to_apply}",
        ]
        return "\n".join(parts)
