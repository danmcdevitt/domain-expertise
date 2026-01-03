-- Domain Expertise Schema
-- Stores domain examples with vector embeddings for semantic search

-- Enable the vector extension (pgvector)
CREATE EXTENSION IF NOT EXISTS vector;

-- Main examples table
CREATE TABLE IF NOT EXISTS domain_examples (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    domain TEXT NOT NULL,
    category TEXT NOT NULL,
    example_id TEXT NOT NULL,
    tags TEXT[] DEFAULT '{}',
    
    -- Content stored as JSONB for flexibility
    content JSONB NOT NULL,
    -- Expected structure:
    -- {
    --   "weak_content": "...",
    --   "weak_reasons": ["...", "..."],
    --   "strong_content": "...",
    --   "strong_reasons": ["...", "..."],
    --   "teaching_point": "...",
    --   "when_to_apply": "..."
    -- }
    
    -- Embedding vector (1536 dimensions for OpenAI ada-002)
    embedding vector(1536),
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Unique constraint on domain + example_id
    UNIQUE(domain, example_id)
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_domain_examples_domain ON domain_examples(domain);
CREATE INDEX IF NOT EXISTS idx_domain_examples_category ON domain_examples(domain, category);
CREATE INDEX IF NOT EXISTS idx_domain_examples_tags ON domain_examples USING GIN(tags);

-- Vector similarity index (using IVFFlat for performance)
-- Adjust lists based on data size: sqrt(n) where n is expected row count
CREATE INDEX IF NOT EXISTS idx_domain_examples_embedding 
ON domain_examples 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for updated_at
CREATE TRIGGER update_domain_examples_updated_at
    BEFORE UPDATE ON domain_examples
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Semantic search function
CREATE OR REPLACE FUNCTION search_domain_examples(
    query_embedding vector(1536),
    p_domain TEXT,
    p_category TEXT DEFAULT NULL,
    p_tags TEXT[] DEFAULT NULL,
    match_limit INT DEFAULT 10,
    similarity_threshold FLOAT DEFAULT 0.5
)
RETURNS TABLE (
    id UUID,
    domain TEXT,
    category TEXT,
    example_id TEXT,
    tags TEXT[],
    content JSONB,
    similarity FLOAT
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
        de.tags,
        de.content,
        1 - (de.embedding <=> query_embedding) as similarity
    FROM domain_examples de
    WHERE 
        de.domain = p_domain
        AND (p_category IS NULL OR de.category = p_category)
        AND (p_tags IS NULL OR de.tags && p_tags)
        AND de.embedding IS NOT NULL
        AND 1 - (de.embedding <=> query_embedding) > similarity_threshold
    ORDER BY de.embedding <=> query_embedding
    LIMIT match_limit;
END;
$$;

-- Helper function to count examples by domain
CREATE OR REPLACE FUNCTION count_domain_examples(p_domain TEXT)
RETURNS INTEGER
LANGUAGE SQL
AS $$
    SELECT COUNT(*)::INTEGER FROM domain_examples WHERE domain = p_domain;
$$;

-- Helper function to delete all examples for a domain
CREATE OR REPLACE FUNCTION delete_domain_examples(p_domain TEXT)
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM domain_examples WHERE domain = p_domain;
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$;

-- Row-level security policies
ALTER TABLE domain_examples ENABLE ROW LEVEL SECURITY;

-- Policy: Allow all operations for authenticated users (customize as needed)
CREATE POLICY "Allow all for authenticated users" ON domain_examples
    FOR ALL
    USING (true)
    WITH CHECK (true);

-- Comments for documentation
COMMENT ON TABLE domain_examples IS 'Stores contrast examples for domain expertise with vector embeddings';
COMMENT ON COLUMN domain_examples.content IS 'JSONB with weak_content, weak_reasons, strong_content, strong_reasons, teaching_point, when_to_apply';
COMMENT ON COLUMN domain_examples.embedding IS 'OpenAI ada-002 embedding (1536 dimensions) for semantic search';
COMMENT ON FUNCTION search_domain_examples IS 'Semantic search for examples using cosine similarity';
