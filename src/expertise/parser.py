"""
Parsers for domain expertise markdown files.

Handles:
- principles.md → list[Principle]
- rubrics/*.md → Rubric
- examples/*.md → ContrastExample
"""

import re
import yaml
from typing import Any

from .types import Principle, Rubric, RubricLevel, ContrastExample


def parse_principles(content: str) -> list[Principle]:
    """
    Parse principles.md into list of Principle objects.

    Expected format:
    # Core Principles: Domain Name

    ## 1. Principle Title
    Explanation paragraph.

    Why this matters: explanation.

    ## 2. Another Principle
    ...
    """
    principles = []

    # Split by ## headers (principle sections)
    sections = re.split(r'\n##\s+', content)

    for section in sections[1:]:  # Skip the # header
        lines = section.strip().split('\n')
        if not lines:
            continue

        # First line is title (may have number prefix)
        title_line = lines[0]
        title = re.sub(r'^\d+\.\s*', '', title_line).strip()

        # Rest is explanation
        body = '\n'.join(lines[1:]).strip()

        # Try to extract "Why this matters" section
        why_match = re.search(
            r'(?:Why (?:this|it) matters|Importance)[:\s]*(.+?)(?:\n\n|\Z)',
            body,
            re.IGNORECASE | re.DOTALL
        )

        if why_match:
            why = why_match.group(1).strip()
            explanation = body[:why_match.start()].strip()
        else:
            explanation = body
            why = ""

        if title:
            principles.append(Principle(
                title=title,
                explanation=explanation,
                why_it_matters=why,
            ))

    return principles


def parse_rubric(content: str, rubric_id: str) -> Rubric:
    """
    Parse a rubric markdown file.

    Expected format:
    # Rubric: Task Name

    Description paragraph.

    ## Scoring

    ### 5 - Exceptional
    - Criterion 1
    - Criterion 2

    ### 3 - Adequate
    - Criterion 1

    ### 1 - Slop
    - Criterion 1

    ## Red Flags
    - Flag 1
    - Flag 2

    ## Evaluation Questions
    1. Question 1?
    2. Question 2?
    """
    # Extract frontmatter if present
    frontmatter = {}
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            frontmatter = yaml.safe_load(parts[1]) or {}
            content = parts[2]

    # Get title
    title_match = re.search(r'^#\s+(?:Rubric:\s*)?(.+)$', content, re.MULTILINE)
    name = title_match.group(1).strip() if title_match else rubric_id

    # Get description (first paragraph after title)
    desc_match = re.search(r'^#.+?\n\n(.+?)\n\n', content, re.DOTALL)
    description = desc_match.group(1).strip() if desc_match else ""

    # Parse scoring levels
    levels = []
    level_pattern = r'###\s+(\d+)\s*[-–]\s*(\w+)\n((?:[-*]\s+.+\n?)+)'
    for match in re.finditer(level_pattern, content):
        score = int(match.group(1))
        label = match.group(2)
        criteria_text = match.group(3)
        criteria = [
            line.strip().lstrip('-*').strip()
            for line in criteria_text.strip().split('\n')
            if line.strip()
        ]
        levels.append(RubricLevel(score=score, label=label, criteria=criteria))

    # Sort levels by score descending
    levels.sort(key=lambda x: x.score, reverse=True)

    # Parse red flags
    red_flags = []
    flags_match = re.search(
        r'##\s+Red Flags?\n((?:[-*]\s+.+\n?)+)',
        content,
        re.IGNORECASE
    )
    if flags_match:
        red_flags = [
            line.strip().lstrip('-*').strip()
            for line in flags_match.group(1).strip().split('\n')
            if line.strip()
        ]

    # Parse evaluation questions
    questions = []
    questions_match = re.search(
        r'##\s+Evaluation Questions?\n((?:\d+\.\s+.+\n?)+)',
        content,
        re.IGNORECASE
    )
    if questions_match:
        questions = [
            re.sub(r'^\d+\.\s*', '', line.strip())
            for line in questions_match.group(1).strip().split('\n')
            if line.strip()
        ]

    return Rubric(
        id=rubric_id,
        name=name,
        description=description,
        levels=levels,
        red_flags=red_flags,
        evaluation_questions=questions,
    )


def parse_example(content: str, file_path: str = "") -> ContrastExample:
    """
    Parse a contrast example markdown file.

    Expected format:
    ---
    id: category-contrast-001
    domain: copywriting
    category: headlines
    tags: [B2B, SaaS, problem-agitation]
    ---

    # Pattern Name

    ## WEAK
    "The weak example"

    ### Why it's weak:
    - Reason 1
    - Reason 2

    ## STRONG
    "The strong example"

    ### Why it works:
    - Reason 1
    - Reason 2

    ## Teaching Point
    One sentence insight.

    ## When to Apply
    Context for using this pattern.
    """
    # Extract frontmatter
    frontmatter: dict[str, Any] = {}
    body = content

    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            frontmatter = yaml.safe_load(parts[1]) or {}
            body = parts[2]

    # Defaults from frontmatter or filename
    example_id = frontmatter.get('id', file_path.replace('.md', ''))
    domain = frontmatter.get('domain', '')
    category = frontmatter.get('category', '')
    tags = frontmatter.get('tags', [])

    # Parse WEAK section
    weak_match = re.search(
        r'##\s+WEAK\s*\n+"?([^"]+)"?\s*\n+###\s+Why.+?:\s*\n((?:[-*]\s+.+\n?)+)',
        body,
        re.IGNORECASE
    )
    if weak_match:
        weak_content = weak_match.group(1).strip().strip('"')
        weak_reasons = [
            line.strip().lstrip('-*').strip()
            for line in weak_match.group(2).strip().split('\n')
            if line.strip()
        ]
    else:
        weak_content = ""
        weak_reasons = []

    # Parse STRONG section
    strong_match = re.search(
        r'##\s+STRONG\s*\n+"?([^"]+)"?\s*\n+###\s+Why.+?:\s*\n((?:[-*]\s+.+\n?)+)',
        body,
        re.IGNORECASE
    )
    if strong_match:
        strong_content = strong_match.group(1).strip().strip('"')
        strong_reasons = [
            line.strip().lstrip('-*').strip()
            for line in strong_match.group(2).strip().split('\n')
            if line.strip()
        ]
    else:
        strong_content = ""
        strong_reasons = []

    # Parse Teaching Point
    teaching_match = re.search(
        r'##\s+Teaching Point\s*\n+(.+?)(?:\n\n|\n##|\Z)',
        body,
        re.IGNORECASE | re.DOTALL
    )
    teaching_point = teaching_match.group(1).strip() if teaching_match else ""

    # Parse When to Apply
    apply_match = re.search(
        r'##\s+When to Apply\s*\n+(.+?)(?:\n\n|\n##|\Z)',
        body,
        re.IGNORECASE | re.DOTALL
    )
    when_to_apply = apply_match.group(1).strip() if apply_match else ""

    return ContrastExample(
        id=example_id,
        domain=domain,
        category=category,
        tags=tags,
        weak_content=weak_content,
        weak_reasons=weak_reasons,
        strong_content=strong_content,
        strong_reasons=strong_reasons,
        teaching_point=teaching_point,
        when_to_apply=when_to_apply,
    )
