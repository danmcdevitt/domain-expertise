"""
SQLite adapter for local file-based vector storage.

Uses SQLite for metadata and numpy for vector operations.
Fully portable - no external dependencies.
"""

import json
import sqlite3
from pathlib import Path
from typing import Any

import numpy as np

from .base import VectorStoreAdapter
from ..types import ContrastExample


class SQLiteAdapter(VectorStoreAdapter):
    """
    Local file-based vector store using SQLite.

    Stores embeddings as JSON arrays in SQLite.
    Uses numpy for cosine similarity calculations.
    """

    def __init__(self, path: Path | str = "./cache/embeddings.db"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize the SQLite database."""
        with sqlite3.connect(self.path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS domain_examples (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    domain TEXT NOT NULL,
                    category TEXT NOT NULL,
                    example_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    embedding TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(domain, example_id)
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_domain
                ON domain_examples(domain)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_domain_category
                ON domain_examples(domain, category)
            """)
            conn.commit()

    def index(self, examples: list[ContrastExample]) -> int:
        """Index examples into SQLite."""
        indexed = 0

        with sqlite3.connect(self.path) as conn:
            for example in examples:
                # Generate embedding
                text = self.example_to_text(example)
                embedding = self.get_embedding(text)

                # Prepare content as JSON
                content = json.dumps({
                    "id": example.id,
                    "tags": example.tags,
                    "weak_content": example.weak_content,
                    "weak_reasons": example.weak_reasons,
                    "strong_content": example.strong_content,
                    "strong_reasons": example.strong_reasons,
                    "teaching_point": example.teaching_point,
                    "when_to_apply": example.when_to_apply,
                })

                # Insert or replace
                conn.execute("""
                    INSERT OR REPLACE INTO domain_examples
                    (domain, category, example_id, content, embedding)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    example.domain,
                    example.category,
                    example.id,
                    content,
                    json.dumps(embedding),
                ))

                indexed += 1

            conn.commit()

        return indexed

    def search(
        self,
        query: str,
        domain: str | None = None,
        category: str | None = None,
        limit: int = 5,
    ) -> list[ContrastExample]:
        """Search for similar examples using cosine similarity."""
        # Get query embedding
        query_embedding = np.array(self.get_embedding(query))

        # Build query
        sql = "SELECT domain, category, example_id, content, embedding FROM domain_examples"
        params: list[Any] = []
        conditions = []

        if domain:
            conditions.append("domain = ?")
            params.append(domain)
        if category:
            conditions.append("category = ?")
            params.append(category)

        if conditions:
            sql += " WHERE " + " AND ".join(conditions)

        # Fetch all matching rows (we'll sort by similarity in Python)
        with sqlite3.connect(self.path) as conn:
            cursor = conn.execute(sql, params)
            rows = cursor.fetchall()

        # Calculate similarities
        results = []
        for row in rows:
            domain_val, category_val, example_id, content_json, embedding_json = row
            content = json.loads(content_json)
            embedding = np.array(json.loads(embedding_json))

            # Cosine similarity
            similarity = float(np.dot(query_embedding, embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(embedding)
            ))

            example = ContrastExample(
                id=content["id"],
                domain=domain_val,
                category=category_val,
                tags=content.get("tags", []),
                weak_content=content.get("weak_content", ""),
                weak_reasons=content.get("weak_reasons", []),
                strong_content=content.get("strong_content", ""),
                strong_reasons=content.get("strong_reasons", []),
                teaching_point=content.get("teaching_point", ""),
                when_to_apply=content.get("when_to_apply", ""),
                similarity=similarity,
            )
            results.append(example)

        # Sort by similarity descending and limit
        results.sort(key=lambda x: x.similarity or 0, reverse=True)
        return results[:limit]

    def delete_domain(self, domain: str) -> int:
        """Delete all examples for a domain."""
        with sqlite3.connect(self.path) as conn:
            cursor = conn.execute(
                "DELETE FROM domain_examples WHERE domain = ?",
                (domain,)
            )
            conn.commit()
            return cursor.rowcount

    def count(self, domain: str | None = None) -> int:
        """Count indexed examples."""
        with sqlite3.connect(self.path) as conn:
            if domain:
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM domain_examples WHERE domain = ?",
                    (domain,)
                )
            else:
                cursor = conn.execute("SELECT COUNT(*) FROM domain_examples")
            return cursor.fetchone()[0]
