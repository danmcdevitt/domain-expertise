# Supabase Setup for Domain Expertise

This directory contains the database schema for storing domain examples with vector embeddings.

## Quick Start

### Option 1: Using Supabase Dashboard

1. Create a new Supabase project at https://supabase.com/dashboard
2. Go to SQL Editor
3. Run the contents of `migrations/001_domain_examples.sql`

### Option 2: Using Supabase CLI

```bash
# Install Supabase CLI
brew install supabase/tap/supabase

# Login
supabase login

# Link to your project
supabase link --project-ref <your-project-ref>

# Run migrations
supabase db push
```

## Environment Variables

Set these in your environment or `.env` file:

```bash
export EXPERTISE_SUPABASE_URL=https://xxx.supabase.co
export EXPERTISE_SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
export OPENAI_API_KEY=sk-...  # For generating embeddings
```

## Schema Overview

### Table: `domain_examples`

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| domain | TEXT | Domain identifier (e.g., "copywriting") |
| category | TEXT | Category within domain (e.g., "headlines") |
| example_id | TEXT | Unique example identifier |
| tags | TEXT[] | Searchable tags |
| content | JSONB | Full example content |
| embedding | vector(1536) | OpenAI embedding for semantic search |

### Functions

- `search_domain_examples(...)` - Semantic search with similarity scoring
- `count_domain_examples(domain)` - Count examples in a domain
- `delete_domain_examples(domain)` - Delete all examples in a domain

## Usage

```python
from expertise import ExpertiseEngine
from expertise.types import ExpertiseConfig

config = ExpertiseConfig(
    domains_path="./domains",
    vector_store={
        "type": "supabase",
        "url": os.environ["EXPERTISE_SUPABASE_URL"],
        "key": os.environ["EXPERTISE_SUPABASE_KEY"],
    }
)

engine = ExpertiseEngine.from_config(config)

# Index examples (generates embeddings and stores in Supabase)
engine.index_domain("copywriting")

# Search semantically
examples = engine.get_examples(
    domain_name="copywriting",
    query="B2B SaaS headline for cold traffic",
    limit=5
)
```
