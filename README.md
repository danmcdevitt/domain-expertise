# Domain Expertise

> Portable domain knowledge system for AI agents.

## Overview

This package provides a structured way to encode domain expertise that AI agents can use for analysis and recommendations. It implements a tiered knowledge system:

- **Tier 1: Core Principles** - Foundational truths always loaded (~1,500 tokens)
- **Tier 2: Judgment Rubrics** - Task-specific evaluation frameworks (~2,000 tokens)
- **Tier 3: Contrast Examples** - WEAK vs STRONG with annotations (~500-800 tokens each)
- **Tier 4: Deep Frameworks** - On-demand reference material

## Installation

```bash
pip install domain-expertise

# Or from source
pip install -e .
```

## Quick Start

```bash
# Create a new domain manually
expertise init my_domain

# Or create from source documents using AI
expertise author my_domain "My Domain Name" -s ./source_docs/

# Validate your domain
expertise validate my_domain

# Index examples for semantic search (requires OPENAI_API_KEY)
expertise index my_domain

# Test retrieval
expertise query my_domain "your search query"

# Get full analysis context
expertise context my_domain task_name "query"
```

## Available Domains

| Domain | Principles | Rubrics | Examples |
|--------|------------|---------|----------|
| copywriting | 5 | 1 | 4 |
| landing_pages | 5 | 1 | 2 |
| email_copy | 5 | 1 | 1 |

## CLI Commands

| Command | Description |
|---------|-------------|
| `expertise list` | List available domains |
| `expertise init <domain>` | Create domain from template |
| `expertise author <id> <name>` | Create domain from sources using AI |
| `expertise validate <domain>` | Validate domain structure |
| `expertise stats <domain>` | Show domain statistics |
| `expertise index <domain>` | Index examples for search |
| `expertise query <domain> <q>` | Search for examples |
| `expertise context <domain> <task> <q>` | Get full analysis context |
| `expertise load <path>` | Preview source documents |
| `expertise generate <domain> <type>` | Generate single content piece |

## Configuration

Set environment variables:

```bash
# For embeddings (required for index/query)
export OPENAI_API_KEY=sk-...

# For Supabase storage (optional, uses SQLite otherwise)
export EXPERTISE_SUPABASE_URL=https://xxx.supabase.co
export EXPERTISE_SUPABASE_KEY=xxx

# For AI authoring
export ANTHROPIC_API_KEY=sk-ant-...
```

## Domain Structure

```
domains/
├── copywriting/
│   ├── domain.yaml           # Configuration
│   ├── principles.md         # Core principles (Tier 1)
│   ├── rubrics/              # Evaluation frameworks (Tier 2)
│   │   └── headline-analysis.md
│   ├── examples/             # Contrast examples (Tier 3)
│   │   ├── headlines/
│   │   │   └── contrast-001.md
│   │   └── ctas/
│   │       └── contrast-001.md
│   └── frameworks/           # Deep reference (Tier 4)
├── landing_pages/
│   ├── domain.yaml
│   ├── principles.md
│   ├── rubrics/
│   │   └── page-audit.md
│   └── examples/
│       ├── heroes/
│       └── ctas/
└── email_copy/
    ├── domain.yaml
    ├── principles.md
    ├── rubrics/
    │   └── subject-line-analysis.md
    └── examples/
        └── subject_lines/
```

## Usage in Code

```python
from expertise import ExpertiseEngine
from expertise.types import ExpertiseConfig

config = ExpertiseConfig(
    domains_path="./domains",
    vector_store={
        "type": "sqlite",  # or "supabase"
        "path": "./cache/embeddings.db",
    }
)

engine = ExpertiseEngine.from_config(config)

# Get analysis context for a task
context = engine.prepare_analysis_context(
    domain_name="copywriting",
    task="headline_analysis",
    query="B2B SaaS cold traffic problem-aware",
)

print(context.principles)     # Core principles
print(context.rubric)         # Headline analysis rubric
print(context.examples)       # Relevant contrast examples
print(context.token_count)    # Total tokens
```

## Document Loaders

Load source documents for AI-assisted authoring:

```python
from expertise.loaders import UnifiedLoader

loader = UnifiedLoader()

# Load from file or directory
docs = loader.load_directory("./source_docs/", recursive=True)

# Supported formats
# - PDF (.pdf)
# - Word (.docx)
# - Markdown (.md)
# - Text (.txt)

for doc in docs:
    print(f"{doc.source}: {doc.word_count} words")
```

## Domain Authoring Agent

Create domains from source documents:

```python
from expertise.authoring import DomainAuthoringAgent

agent = DomainAuthoringAgent()

# Load source material
agent.load_sources("./research_docs/")

# Analyze domain patterns
analysis = agent.analyze_domain()

# Extract structured content
principles = agent.extract_principles("My Domain")
rubric = agent.extract_rubric("Content Analysis")
example = agent.extract_contrast_example(
    pattern="Common mistake vs expert approach",
    domain="my_domain",
    category="general",
    example_id="general-001",
    tags=["intro", "common"]
)

# Or create complete domain
stats = agent.create_domain(
    domain_id="my_domain",
    domain_name="My Domain Expertise",
    output_path="./domains/my_domain",
    source_path="./research_docs/",
)
```

## Contrast Example Format

```markdown
---
id: headlines-contrast-001
domain: copywriting
category: headlines
tags: [B2B, SaaS, problem-agitation]
---

# Problem-Agitation Headlines

## WEAK
"Are You Struggling with Lead Generation?"

### Why it's weak:
- Generic question everyone ignores
- "Struggling" is vague
- No specific visual

## STRONG
"Still Manually Copying Leads from LinkedIn into Your CRM Every Morning?"

### Why it works:
- Specific action (copying from LinkedIn to CRM)
- Specific time (every morning)
- Reader pictures themselves doing it

## Teaching Point
Specificity creates recognition.

## When to Apply
Use for problem-aware audiences who haven't solved yet.
```

## Supabase Setup

For production use with Supabase:

1. Create a Supabase project
2. Run the migration in `supabase/migrations/001_domain_examples.sql`
3. Set environment variables

See `supabase/README.md` for detailed setup instructions.

## Integration with FunnelGenius

This package is designed to work as a submodule with FunnelGenius:

```bash
# In FunnelGenius
git submodule add https://github.com/yourusername/domain-expertise.git lib/domain-expertise
git submodule update --init --recursive
```

Then use the integration module:

```python
from agents.expertise import get_analysis_context, format_expertise_prompt

# Get context for an agent
context = get_analysis_context(
    domain="copywriting",
    task="headline_analysis",
    query="B2B SaaS cold traffic"
)

# Format as system prompt
prompt = format_expertise_prompt(
    domain="copywriting",
    task="headline_analysis"
)
```

## License

MIT
