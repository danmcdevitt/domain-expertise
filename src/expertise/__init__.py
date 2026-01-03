"""
Domain Expertise Engine - Portable domain knowledge for AI agents.

This package provides:
- Tiered domain knowledge (principles, rubrics, examples)
- Semantic search over contrast examples
- CLI tools for authoring and management
- MCP server for agent access
"""

from .engine import ExpertiseEngine
from .types import Domain, Principle, Rubric, ContrastExample

__version__ = "0.1.0"
__all__ = ["ExpertiseEngine", "Domain", "Principle", "Rubric", "ContrastExample"]
