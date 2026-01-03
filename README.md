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
# Create a new domain
expertise init copywriting

# Edit the files in domains/copywriting/
# - principles.md
# - rubrics/*.md
# - examples/*/*.md

# Validate your domain
expertise validate copywriting

# Index examples for semantic search
expertise index copywriting

# Test retrieval
expertise query copywriting "B2B SaaS headline cold traffic"
```

## Configuration

Set environment variables for Supabase (or use local SQLite):

```bash
export EXPERTISE_SUPABASE_URL=https://xxx.supabase.co
export EXPERTISE_SUPABASE_KEY=xxx
```

## Domain Structure

```
domains/
└── copywriting/
    ├── domain.yaml           # Configuration
    ├── principles.md         # Core principles (Tier 1)
    ├── rubrics/              # Evaluation frameworks (Tier 2)
    │   ├── headline-analysis.md
    │   └── landing-page-audit.md
    ├── examples/             # Contrast examples (Tier 3)
    │   ├── headlines/
    │   │   ├── contrast-001.md
    │   │   └── contrast-002.md
    │   └── ctas/
    │       └── contrast-001.md
    └── frameworks/           # Deep reference (Tier 4)
        └── aida.md
```

## Usage in Code

```python
from expertise import ExpertiseEngine

engine = ExpertiseEngine.from_config({
    "domains_path": "./domains",
    "vector_store": {
        "type": "supabase",  # or "sqlite"
        "url": "...",
        "key": "...",
    }
})

# Get analysis context for a task
context = engine.prepare_analysis_context(
    domain_name="copywriting",
    task="headline_analysis",
    query="B2B SaaS cold traffic problem-aware",
)

print(context.principles)     # Core principles
print(context.rubric)         # Headline analysis rubric
print(context.examples)       # 5 relevant contrast examples
print(context.token_count)    # Total tokens
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

## License

MIT
