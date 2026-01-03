"""
Type definitions for domain expertise system.
"""

from dataclasses import dataclass, field
from typing import Any
from pathlib import Path


@dataclass
class Principle:
    """A core principle that always applies to this domain."""
    title: str
    explanation: str
    why_it_matters: str


@dataclass
class RubricLevel:
    """A scoring level within a rubric."""
    score: int
    label: str  # "Exceptional", "Adequate", "Slop"
    criteria: list[str]


@dataclass
class Rubric:
    """Evaluation framework for a specific task."""
    id: str
    name: str
    description: str
    levels: list[RubricLevel]
    red_flags: list[str]
    evaluation_questions: list[str]


@dataclass
class ContrastExample:
    """A WEAK vs STRONG example with annotations."""
    id: str
    domain: str
    category: str
    tags: list[str]

    # The contrast
    weak_content: str
    weak_reasons: list[str]
    strong_content: str
    strong_reasons: list[str]

    # Teaching
    teaching_point: str
    when_to_apply: str

    # For retrieval
    embedding: list[float] | None = None
    similarity: float | None = None


@dataclass
class Domain:
    """A complete domain with all its knowledge."""
    name: str
    path: Path
    principles: list[Principle] = field(default_factory=list)
    rubrics: list[Rubric] = field(default_factory=list)
    examples: list[ContrastExample] = field(default_factory=list)

    @property
    def principles_path(self) -> Path:
        return self.path / "principles.md"

    @property
    def rubrics_path(self) -> Path:
        return self.path / "rubrics"

    @property
    def examples_path(self) -> Path:
        return self.path / "examples"


@dataclass
class AnalysisContext:
    """Everything needed for an analysis task."""
    principles: str
    rubric: Rubric | None
    examples: list[ContrastExample]
    token_count: int


@dataclass
class DomainConfig:
    """Configuration for a domain from domain.yaml."""
    id: str
    name: str
    description: str
    rubric_triggers: dict[str, list[str]] = field(default_factory=dict)
    example_categories: list[str] = field(default_factory=list)


@dataclass
class ExpertiseConfig:
    """Configuration for the expertise engine."""
    domains_path: Path
    vector_store: dict[str, Any]
    domains_enabled: list[str] | None = None  # None = all domains
