"""
ExpertiseEngine - Core retrieval system for domain expertise.

Provides tiered retrieval:
- Tier 1: Core principles (always loaded)
- Tier 2: Task-specific rubrics
- Tier 3: Semantically retrieved examples
- Tier 4: On-demand frameworks
"""

from pathlib import Path
from typing import Any
import yaml
import tiktoken

from .types import (
    Domain,
    Principle,
    Rubric,
    ContrastExample,
    AnalysisContext,
    ExpertiseConfig,
)
from .adapters.base import VectorStoreAdapter
from .adapters.supabase import SupabaseAdapter
from .adapters.sqlite import SQLiteAdapter
from .parser import parse_principles, parse_rubric, parse_example


class ExpertiseEngine:
    """
    Main engine for domain expertise retrieval.

    Usage:
        engine = ExpertiseEngine.from_config(config)
        context = engine.prepare_analysis_context(
            domain="copywriting",
            task="headline_analysis",
            query="B2B SaaS cold traffic"
        )
    """

    def __init__(
        self,
        domains_path: Path,
        vector_store: VectorStoreAdapter,
        domains_enabled: list[str] | None = None,
    ):
        self.domains_path = Path(domains_path)
        self.vector_store = vector_store
        self.domains_enabled = domains_enabled
        self._domains: dict[str, Domain] = {}
        self._encoder = tiktoken.get_encoding("cl100k_base")

    @classmethod
    def from_config(cls, config: ExpertiseConfig | dict) -> "ExpertiseEngine":
        """Create engine from configuration."""
        if isinstance(config, dict):
            config = ExpertiseConfig(**config)

        # Create vector store adapter
        store_config = config.vector_store
        store_type = store_config.get("type", "sqlite")

        if store_type == "supabase":
            vector_store = SupabaseAdapter(
                url=store_config["url"],
                key=store_config["key"],
                table=store_config.get("table", "domain_examples"),
            )
        elif store_type == "sqlite" or store_type == "file":
            vector_store = SQLiteAdapter(
                path=Path(store_config.get("path", "./cache/embeddings.db"))
            )
        else:
            raise ValueError(f"Unknown vector store type: {store_type}")

        return cls(
            domains_path=config.domains_path,
            vector_store=vector_store,
            domains_enabled=config.domains_enabled,
        )

    def load_domain(self, domain_name: str) -> Domain:
        """Load a domain from disk."""
        if domain_name in self._domains:
            return self._domains[domain_name]

        domain_path = self.domains_path / domain_name
        if not domain_path.exists():
            raise ValueError(f"Domain not found: {domain_name}")

        domain = Domain(name=domain_name, path=domain_path)

        # Load principles
        principles_file = domain.principles_path
        if principles_file.exists():
            domain.principles = parse_principles(principles_file.read_text())

        # Load rubrics
        rubrics_dir = domain.rubrics_path
        if rubrics_dir.exists():
            for rubric_file in rubrics_dir.glob("*.md"):
                rubric = parse_rubric(rubric_file.read_text(), rubric_file.stem)
                domain.rubrics.append(rubric)

        self._domains[domain_name] = domain
        return domain

    def get_principles(self, domain_name: str) -> str:
        """Get core principles for a domain (Tier 1 - always loaded)."""
        domain = self.load_domain(domain_name)
        principles_file = domain.principles_path
        if principles_file.exists():
            return principles_file.read_text()
        return ""

    def get_rubric(self, domain_name: str, task: str) -> Rubric | None:
        """Get evaluation rubric for a specific task (Tier 2)."""
        domain = self.load_domain(domain_name)

        # Try exact match first
        rubric_file = domain.rubrics_path / f"{task}.md"
        if rubric_file.exists():
            return parse_rubric(rubric_file.read_text(), task)

        # Try fuzzy match from loaded rubrics
        task_lower = task.lower().replace("_", "-").replace(" ", "-")
        for rubric in domain.rubrics:
            if rubric.id.lower() == task_lower:
                return rubric

        return None

    def get_examples(
        self,
        domain_name: str,
        query: str,
        category: str | None = None,
        limit: int = 5,
    ) -> list[ContrastExample]:
        """Retrieve relevant contrast examples via semantic search (Tier 3)."""
        return self.vector_store.search(
            query=query,
            domain=domain_name,
            category=category,
            limit=limit,
        )

    def get_framework(self, domain_name: str, framework_id: str) -> str | None:
        """Get deep reference framework on-demand (Tier 4)."""
        domain = self.load_domain(domain_name)
        frameworks_dir = domain.path / "frameworks"

        framework_file = frameworks_dir / f"{framework_id}.md"
        if framework_file.exists():
            return framework_file.read_text()

        return None

    def prepare_analysis_context(
        self,
        domain_name: str,
        task: str,
        query: str,
        token_budget: int = 8000,
    ) -> AnalysisContext:
        """
        Prepare complete context for an analysis task.

        Orchestrates retrieval from all tiers with token budget management.
        """
        used_tokens = 0

        # Tier 1: Always load principles
        principles = self.get_principles(domain_name)
        principles_tokens = self._count_tokens(principles)
        used_tokens += principles_tokens

        # Tier 2: Load task rubric
        rubric = self.get_rubric(domain_name, task)
        if rubric:
            rubric_tokens = self._count_tokens(str(rubric))
            used_tokens += rubric_tokens

        # Tier 3: Retrieve examples with remaining budget
        remaining_budget = token_budget - used_tokens
        examples_budget = min(remaining_budget, 4000)  # Cap examples at 4k
        avg_example_tokens = 600

        max_examples = max(1, examples_budget // avg_example_tokens)
        examples = self.get_examples(domain_name, query, limit=max_examples)

        for ex in examples:
            used_tokens += self._count_tokens(str(ex))

        return AnalysisContext(
            principles=principles,
            rubric=rubric,
            examples=examples,
            token_count=used_tokens,
        )

    def _count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return len(self._encoder.encode(text))

    def list_domains(self) -> list[str]:
        """List available domains."""
        domains = []
        for path in self.domains_path.iterdir():
            if path.is_dir() and not path.name.startswith("."):
                if self.domains_enabled is None or path.name in self.domains_enabled:
                    domains.append(path.name)
        return sorted(domains)

    def validate_domain(self, domain_name: str) -> dict[str, Any]:
        """Validate a domain's structure and content."""
        domain = self.load_domain(domain_name)
        issues = []
        warnings = []

        # Check principles
        if not domain.principles_path.exists():
            issues.append("Missing principles.md")
        elif len(domain.principles) == 0:
            warnings.append("principles.md exists but no principles parsed")
        elif len(domain.principles) < 3:
            warnings.append(f"Only {len(domain.principles)} principles (recommend 3-7)")

        # Check rubrics
        if not domain.rubrics_path.exists():
            warnings.append("No rubrics directory")
        elif len(domain.rubrics) == 0:
            warnings.append("No rubrics found")

        # Check examples
        if not domain.examples_path.exists():
            warnings.append("No examples directory")
        else:
            example_count = sum(1 for _ in domain.examples_path.rglob("*.md"))
            if example_count == 0:
                warnings.append("No example files found")
            elif example_count < 10:
                warnings.append(f"Only {example_count} examples (recommend 10+)")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "stats": {
                "principles": len(domain.principles),
                "rubrics": len(domain.rubrics),
                "examples": sum(1 for _ in domain.examples_path.rglob("*.md")) if domain.examples_path.exists() else 0,
            },
        }
