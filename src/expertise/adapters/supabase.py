"""
Supabase adapter using pgvector for embeddings.
"""

import os
from typing import Any

from supabase import create_client, Client

from .base import VectorStoreAdapter
from ..types import ContrastExample


class SupabaseAdapter(VectorStoreAdapter):
    """
    Vector store adapter using Supabase with pgvector.

    Requires table:
        CREATE TABLE domain_examples (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            domain TEXT NOT NULL,
            category TEXT NOT NULL,
            example_id TEXT NOT NULL,
            content JSONB NOT NULL,
            embedding vector(1536),
            created_at TIMESTAMPTZ DEFAULT NOW(),
            UNIQUE(domain, example_id)
        );

        CREATE INDEX ON domain_examples
            USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100);
    """

    def __init__(
        self,
        url: str | None = None,
        key: str | None = None,
        table: str = "domain_examples",
    ):
        self.url = url or os.environ.get("EXPERTISE_SUPABASE_URL")
        self.key = key or os.environ.get("EXPERTISE_SUPABASE_KEY")
        self.table = table

        if not self.url or not self.key:
            raise ValueError(
                "Supabase URL and key required. "
                "Set EXPERTISE_SUPABASE_URL and EXPERTISE_SUPABASE_KEY env vars."
            )

        self.client: Client = create_client(self.url, self.key)

    def index(self, examples: list[ContrastExample]) -> int:
        """Index examples into Supabase."""
        indexed = 0

        for example in examples:
            # Generate embedding
            text = self.example_to_text(example)
            embedding = self.get_embedding(text)

            # Prepare record
            record = {
                "domain": example.domain,
                "category": example.category,
                "example_id": example.id,
                "content": {
                    "id": example.id,
                    "tags": example.tags,
                    "weak_content": example.weak_content,
                    "weak_reasons": example.weak_reasons,
                    "strong_content": example.strong_content,
                    "strong_reasons": example.strong_reasons,
                    "teaching_point": example.teaching_point,
                    "when_to_apply": example.when_to_apply,
                },
                "embedding": embedding,
            }

            # Upsert (insert or update)
            self.client.table(self.table).upsert(
                record,
                on_conflict="domain,example_id",
            ).execute()

            indexed += 1

        return indexed

    def search(
        self,
        query: str,
        domain: str | None = None,
        category: str | None = None,
        limit: int = 5,
    ) -> list[ContrastExample]:
        """Search for similar examples using vector similarity."""
        # Get query embedding
        query_embedding = self.get_embedding(query)

        # Build RPC call for similarity search
        # This requires a Supabase function - see schema below
        params: dict[str, Any] = {
            "query_embedding": query_embedding,
            "match_count": limit,
        }

        if domain:
            params["filter_domain"] = domain
        if category:
            params["filter_category"] = category

        # Call the similarity search function
        response = self.client.rpc(
            "search_domain_examples",
            params,
        ).execute()

        # Convert to ContrastExample objects
        examples = []
        for row in response.data:
            content = row["content"]
            example = ContrastExample(
                id=content["id"],
                domain=row["domain"],
                category=row["category"],
                tags=content.get("tags", []),
                weak_content=content.get("weak_content", ""),
                weak_reasons=content.get("weak_reasons", []),
                strong_content=content.get("strong_content", ""),
                strong_reasons=content.get("strong_reasons", []),
                teaching_point=content.get("teaching_point", ""),
                when_to_apply=content.get("when_to_apply", ""),
                similarity=row.get("similarity"),
            )
            examples.append(example)

        return examples

    def delete_domain(self, domain: str) -> int:
        """Delete all examples for a domain."""
        response = self.client.table(self.table).delete().eq(
            "domain", domain
        ).execute()
        return len(response.data) if response.data else 0

    def count(self, domain: str | None = None) -> int:
        """Count indexed examples."""
        query = self.client.table(self.table).select("id", count="exact")
        if domain:
            query = query.eq("domain", domain)
        response = query.execute()
        return response.count or 0


# SQL for Supabase setup
SUPABASE_SCHEMA = """
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create table for domain examples
CREATE TABLE IF NOT EXISTS domain_examples (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    domain TEXT NOT NULL,
    category TEXT NOT NULL,
    example_id TEXT NOT NULL,
    content JSONB NOT NULL,
    embedding vector(1536),
    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(domain, example_id)
);

-- Create vector index for similarity search
CREATE INDEX IF NOT EXISTS domain_examples_embedding_idx
    ON domain_examples
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- Create indexes for filtering
CREATE INDEX IF NOT EXISTS domain_examples_domain_idx ON domain_examples(domain);
CREATE INDEX IF NOT EXISTS domain_examples_category_idx ON domain_examples(domain, category);

-- Create similarity search function
CREATE OR REPLACE FUNCTION search_domain_examples(
    query_embedding vector(1536),
    match_count int DEFAULT 5,
    filter_domain text DEFAULT NULL,
    filter_category text DEFAULT NULL
)
RETURNS TABLE (
    id uuid,
    domain text,
    category text,
    example_id text,
    content jsonb,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        de.id,
        de.domain,
        de.category,
        de.example_id,
        de.content,
        1 - (de.embedding <=> query_embedding) as similarity
    FROM domain_examples de
    WHERE
        (filter_domain IS NULL OR de.domain = filter_domain)
        AND (filter_category IS NULL OR de.category = filter_category)
    ORDER BY de.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
"""
