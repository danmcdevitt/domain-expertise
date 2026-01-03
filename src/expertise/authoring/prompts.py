"""Prompts for the domain authoring agent."""

EXTRACTION_PROMPTS = {
    "analyze_sources": """You are a domain expertise architect. Analyze the following source documents to understand the key concepts, principles, and patterns in this domain.

<source_documents>
{documents}
</source_documents>

Provide a structured analysis:

1. **Domain Overview**: What is this domain about? Who is the target audience?

2. **Core Principles** (3-7): What are the fundamental truths that experts in this domain agree on? These should be:
   - Non-negotiable rules that separate good work from bad
   - Specific enough to be actionable
   - Universal across contexts within the domain

3. **Key Tasks**: What are the main tasks someone would need evaluated in this domain? (e.g., "headline analysis", "landing page audit")

4. **Quality Spectrum**: What separates exceptional work from mediocre and poor work in this domain? What are the red flags of bad work?

5. **Teaching Patterns**: What are the most important distinctions to teach? What are common mistakes vs expert approaches?

Format your response as structured text that can be parsed.""",

    "extract_principles": """Based on this analysis and source material, extract the core principles for this domain.

<analysis>
{analysis}
</analysis>

<source_documents>
{documents}
</source_documents>

Generate a principles.md file in this exact format:

```markdown
# Core Principles: {domain_name}

These are the non-negotiable truths that separate effective {domain_type} from slop.

## 1. [Principle Title]

[2-3 sentence explanation of the principle.]

Why this matters: [One sentence on why this is critical.]

## 2. [Principle Title]

[Explanation.]

Why this matters: [Importance.]

[Continue for all principles...]
```

Requirements:
- 3-7 principles (prefer fewer, more powerful principles)
- Each principle should be specific and actionable
- Include concrete examples where helpful
- The "Why this matters" should be a single punchy sentence""",

    "extract_rubric": """Create an evaluation rubric for the task: {task_name}

<analysis>
{analysis}
</analysis>

<source_documents>
{documents}
</source_documents>

Generate a rubric in this exact format:

```markdown
# Rubric: {task_name}

{description}

## Scoring

### 5 - Exceptional
- [Specific criteria for exceptional work]
- [Another criterion]
- [Use bullet points, 4-6 items]

### 4 - Strong
- [Criteria for strong work]
- [Minor issues acceptable]

### 3 - Adequate
- [Meets basic requirements]
- [Notable gaps or weaknesses]

### 2 - Weak
- [Clear problems]
- [Missing key elements]

### 1 - Slop
- [Fundamental failures]
- [Common AI/low-effort patterns]

## Red Flags (Instant Slop Indicators)
- [Pattern that immediately signals low quality]
- [Another red flag]
- [5-10 items]

## Evaluation Questions
1. [Question to ask when evaluating?]
2. [Another key question?]
[5-10 questions]
```

Be specific. Use actual examples of good and bad patterns where possible.""",

    "extract_contrast_example": """Create a contrast example showing WEAK vs STRONG for this pattern.

<pattern>
{pattern}
</pattern>

<context>
{context}
</context>

<source_material>
{source_material}
</source_material>

Generate a contrast example in this exact format:

```markdown
---
id: {example_id}
domain: {domain}
category: {category}
tags: [{tags}]
---

# {pattern_name}

## WEAK
"{weak_example}"

### Why it's weak:
- [Specific reason tied to principles]
- [Another reason]
- [2-4 bullet points]

## STRONG
"{strong_example}"

### Why it works:
- [Specific reason tied to principles]
- [Another reason]
- [2-4 bullet points]

## Teaching Point
[One sentence that captures the key lesson.]

## When to Apply
[1-2 sentences on when to use this pattern.]
```

Requirements:
- Examples must be realistic and specific
- WEAK should be recognizably bad but not cartoonishly terrible
- STRONG should be achievable, not impossibly perfect
- Reasons should tie back to core principles
- Teaching point should be memorable""",

    "suggest_categories": """Based on this domain analysis, suggest categories for organizing contrast examples.

<analysis>
{analysis}
</analysis>

<domain>
{domain_name}
</domain>

Provide 3-8 categories, each with:
1. Category name (lowercase, underscores)
2. Description
3. 2-3 example patterns that would belong in this category

Format:
```
category: headlines
description: Headline patterns for ads, landing pages, and emails
patterns:
  - Problem-agitation headlines
  - Outcome-focused headlines
  - Curiosity headlines

category: ctas
description: Call-to-action button and link text
patterns:
  - Action verbs vs passive
  - Benefit-focused CTAs
  - Urgency patterns
```""",

    "refine_content": """Review and improve this domain content.

<content>
{content}
</content>

<feedback>
{feedback}
</feedback>

Provide an improved version that addresses the feedback while maintaining the required format.

Key improvements to consider:
- Make principles more specific and actionable
- Ensure examples are realistic
- Tighten language (remove filler)
- Add specificity where vague
- Ensure consistency with domain voice""",
}
