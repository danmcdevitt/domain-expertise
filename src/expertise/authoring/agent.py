"""Domain Authoring Agent - Creates domain expertise from source documents."""

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from anthropic import Anthropic

from ..loaders import UnifiedLoader, Document
from .prompts import EXTRACTION_PROMPTS


@dataclass
class AuthoringResult:
    """Result of an authoring operation."""
    content: str
    content_type: str  # "principles", "rubric", "example", "analysis"
    tokens_used: int
    source_count: int


class DomainAuthoringAgent:
    """Agent that creates domain expertise from source documents.
    
    Workflow:
    1. Load source documents (PDFs, DOCs, markdown)
    2. Analyze to understand domain patterns
    3. Extract principles, rubrics, and contrast examples
    4. Optionally refine with human feedback
    """
    
    def __init__(
        self,
        api_key: str | None = None,
        model: str = "claude-sonnet-4-20250514",
    ):
        """Initialize the authoring agent.
        
        Args:
            api_key: Anthropic API key. Defaults to ANTHROPIC_API_KEY env var.
            model: Model to use for generation.
        """
        self.client = Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))
        self.model = model
        self.loader = UnifiedLoader()
        
        # Store conversation context
        self._current_analysis: str | None = None
        self._loaded_documents: list[Document] = []
    
    def load_sources(
        self,
        path: Path | str,
        recursive: bool = True,
    ) -> list[Document]:
        """Load source documents from a file or directory.
        
        Args:
            path: File or directory path.
            recursive: Search subdirectories if path is a directory.
            
        Returns:
            List of loaded documents.
        """
        path = Path(path)
        
        if path.is_dir():
            self._loaded_documents = self.loader.load_directory(path, recursive=recursive)
        else:
            self._loaded_documents = self.loader.load(path)
        
        return self._loaded_documents
    
    def analyze_domain(
        self,
        documents: list[Document] | None = None,
    ) -> AuthoringResult:
        """Analyze source documents to understand domain patterns.
        
        This is typically the first step in authoring a new domain.
        
        Args:
            documents: Documents to analyze. Uses previously loaded if not provided.
            
        Returns:
            AuthoringResult with the analysis.
        """
        docs = documents or self._loaded_documents
        if not docs:
            raise ValueError("No documents loaded. Call load_sources() first.")
        
        # Prepare document text (with truncation for token limits)
        doc_text = self._prepare_documents(docs, max_tokens=50000)
        
        prompt = EXTRACTION_PROMPTS["analyze_sources"].format(documents=doc_text)
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        
        analysis = response.content[0].text
        self._current_analysis = analysis
        
        return AuthoringResult(
            content=analysis,
            content_type="analysis",
            tokens_used=response.usage.input_tokens + response.usage.output_tokens,
            source_count=len(docs),
        )
    
    def extract_principles(
        self,
        domain_name: str,
        analysis: str | None = None,
        documents: list[Document] | None = None,
    ) -> AuthoringResult:
        """Extract core principles from the analysis.
        
        Args:
            domain_name: Name of the domain (e.g., "Direct Response Copywriting")
            analysis: Analysis to base principles on. Uses cached if not provided.
            documents: Additional context documents.
            
        Returns:
            AuthoringResult with principles.md content.
        """
        analysis = analysis or self._current_analysis
        if not analysis:
            raise ValueError("No analysis available. Call analyze_domain() first.")
        
        docs = documents or self._loaded_documents
        doc_text = self._prepare_documents(docs, max_tokens=20000) if docs else ""
        
        prompt = EXTRACTION_PROMPTS["extract_principles"].format(
            analysis=analysis,
            documents=doc_text,
            domain_name=domain_name,
            domain_type=domain_name.lower(),
        )
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        
        # Extract markdown content
        content = self._extract_markdown(response.content[0].text)
        
        return AuthoringResult(
            content=content,
            content_type="principles",
            tokens_used=response.usage.input_tokens + response.usage.output_tokens,
            source_count=len(docs) if docs else 0,
        )
    
    def extract_rubric(
        self,
        task_name: str,
        description: str = "",
        analysis: str | None = None,
        documents: list[Document] | None = None,
    ) -> AuthoringResult:
        """Extract an evaluation rubric for a specific task.
        
        Args:
            task_name: Name of the task (e.g., "Headline Analysis")
            description: Brief description of what the rubric evaluates.
            analysis: Analysis to base rubric on.
            documents: Additional context documents.
            
        Returns:
            AuthoringResult with rubric markdown content.
        """
        analysis = analysis or self._current_analysis
        if not analysis:
            raise ValueError("No analysis available. Call analyze_domain() first.")
        
        docs = documents or self._loaded_documents
        doc_text = self._prepare_documents(docs, max_tokens=20000) if docs else ""
        
        prompt = EXTRACTION_PROMPTS["extract_rubric"].format(
            task_name=task_name,
            description=description,
            analysis=analysis,
            documents=doc_text,
        )
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        
        content = self._extract_markdown(response.content[0].text)
        
        return AuthoringResult(
            content=content,
            content_type="rubric",
            tokens_used=response.usage.input_tokens + response.usage.output_tokens,
            source_count=len(docs) if docs else 0,
        )
    
    def extract_contrast_example(
        self,
        pattern: str,
        domain: str,
        category: str,
        example_id: str,
        tags: list[str],
        context: str = "",
        source_material: str = "",
    ) -> AuthoringResult:
        """Generate a contrast example for a specific pattern.
        
        Args:
            pattern: The pattern to illustrate (e.g., "Problem-agitation headlines")
            domain: Domain name (e.g., "copywriting")
            category: Category (e.g., "headlines")
            example_id: Unique ID for the example
            tags: Tags for searchability
            context: Additional context about when to use this pattern
            source_material: Relevant source text to draw from
            
        Returns:
            AuthoringResult with contrast example markdown.
        """
        prompt = EXTRACTION_PROMPTS["extract_contrast_example"].format(
            pattern=pattern,
            context=context or "General usage",
            source_material=source_material or "No specific source material provided",
            example_id=example_id,
            domain=domain,
            category=category,
            tags=", ".join(tags),
            pattern_name=pattern,
        )
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )
        
        content = self._extract_markdown(response.content[0].text)
        
        return AuthoringResult(
            content=content,
            content_type="example",
            tokens_used=response.usage.input_tokens + response.usage.output_tokens,
            source_count=0,
        )
    
    def suggest_categories(
        self,
        domain_name: str,
        analysis: str | None = None,
    ) -> list[dict]:
        """Suggest example categories for a domain.
        
        Args:
            domain_name: Name of the domain.
            analysis: Analysis to base suggestions on.
            
        Returns:
            List of category dictionaries with name, description, and patterns.
        """
        analysis = analysis or self._current_analysis
        if not analysis:
            raise ValueError("No analysis available. Call analyze_domain() first.")
        
        prompt = EXTRACTION_PROMPTS["suggest_categories"].format(
            analysis=analysis,
            domain_name=domain_name,
        )
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )
        
        # Parse the response into structured data
        categories = self._parse_categories(response.content[0].text)
        return categories
    
    def refine(
        self,
        content: str,
        feedback: str,
    ) -> AuthoringResult:
        """Refine content based on feedback.
        
        Args:
            content: The content to refine.
            feedback: Human feedback on what to improve.
            
        Returns:
            AuthoringResult with refined content.
        """
        prompt = EXTRACTION_PROMPTS["refine_content"].format(
            content=content,
            feedback=feedback,
        )
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        
        refined = self._extract_markdown(response.content[0].text)
        
        return AuthoringResult(
            content=refined,
            content_type="refined",
            tokens_used=response.usage.input_tokens + response.usage.output_tokens,
            source_count=0,
        )
    
    def create_domain(
        self,
        domain_id: str,
        domain_name: str,
        output_path: Path | str,
        source_path: Path | str | None = None,
        tasks: list[str] | None = None,
        categories: list[str] | None = None,
        examples_per_category: int = 3,
        progress_callback: Callable[[str], None] | None = None,
    ) -> dict:
        """Create a complete domain from source documents.
        
        This is the main entry point for creating a new domain.
        
        Args:
            domain_id: Short identifier (e.g., "copywriting")
            domain_name: Full name (e.g., "Direct Response Copywriting")
            output_path: Where to write the domain files.
            source_path: Path to source documents (optional).
            tasks: List of tasks for rubrics (or will be suggested).
            categories: List of example categories (or will be suggested).
            examples_per_category: Number of examples to generate per category.
            progress_callback: Optional callback for progress updates.
            
        Returns:
            Dictionary with paths to created files and statistics.
        """
        output_path = Path(output_path)
        
        def log(msg: str):
            if progress_callback:
                progress_callback(msg)
        
        stats = {
            "domain_id": domain_id,
            "tokens_used": 0,
            "files_created": [],
        }
        
        # Load sources if provided
        if source_path:
            log(f"Loading source documents from {source_path}...")
            docs = self.load_sources(source_path)
            log(f"Loaded {len(docs)} documents")
        
        # Analyze domain
        log("Analyzing domain patterns...")
        analysis_result = self.analyze_domain()
        stats["tokens_used"] += analysis_result.tokens_used
        
        # Create directory structure
        log("Creating directory structure...")
        (output_path / "rubrics").mkdir(parents=True, exist_ok=True)
        (output_path / "examples").mkdir(exist_ok=True)
        (output_path / "frameworks").mkdir(exist_ok=True)
        
        # Create domain.yaml
        log("Creating domain.yaml...")
        domain_yaml = self._create_domain_yaml(domain_id, domain_name, tasks or [])
        (output_path / "domain.yaml").write_text(domain_yaml)
        stats["files_created"].append(str(output_path / "domain.yaml"))
        
        # Extract principles
        log("Extracting core principles...")
        principles_result = self.extract_principles(domain_name)
        stats["tokens_used"] += principles_result.tokens_used
        (output_path / "principles.md").write_text(principles_result.content)
        stats["files_created"].append(str(output_path / "principles.md"))
        
        # Suggest or use provided categories
        if not categories:
            log("Suggesting example categories...")
            category_list = self.suggest_categories(domain_name)
            categories = [c["name"] for c in category_list]
        
        # Create example directories
        for category in categories:
            (output_path / "examples" / category).mkdir(exist_ok=True)
        
        # Extract rubrics for each task
        task_list = tasks or self._extract_tasks_from_analysis(analysis_result.content)
        for task in task_list:
            log(f"Creating rubric for: {task}...")
            rubric_result = self.extract_rubric(task)
            stats["tokens_used"] += rubric_result.tokens_used
            
            filename = task.lower().replace(" ", "-") + ".md"
            (output_path / "rubrics" / filename).write_text(rubric_result.content)
            stats["files_created"].append(str(output_path / "rubrics" / filename))
        
        # Generate contrast examples
        for category in categories:
            patterns = self._get_patterns_for_category(category, analysis_result.content)
            
            for i, pattern in enumerate(patterns[:examples_per_category], start=1):
                log(f"Creating example: {category}/{pattern}...")
                example_id = f"{category}-contrast-{i:03d}"
                
                example_result = self.extract_contrast_example(
                    pattern=pattern,
                    domain=domain_id,
                    category=category,
                    example_id=example_id,
                    tags=[category, domain_id],
                )
                stats["tokens_used"] += example_result.tokens_used
                
                filename = f"contrast-{i:03d}.md"
                (output_path / "examples" / category / filename).write_text(example_result.content)
                stats["files_created"].append(str(output_path / "examples" / category / filename))
        
        log("Domain creation complete!")
        return stats
    
    def _prepare_documents(self, docs: list[Document], max_tokens: int) -> str:
        """Prepare documents for inclusion in prompt."""
        texts = []
        total_chars = 0
        char_limit = max_tokens * 4  # Rough estimate: 4 chars per token
        
        for doc in docs:
            if total_chars >= char_limit:
                break
            
            header = f"=== Source: {doc.source} ==="
            if doc.title:
                header += f"\nTitle: {doc.title}"
            if doc.section:
                header += f"\nSection: {doc.section}"
            
            available = char_limit - total_chars - len(header) - 10
            content = doc.content[:available] if len(doc.content) > available else doc.content
            
            texts.append(f"{header}\n\n{content}")
            total_chars += len(header) + len(content)
        
        return "\n\n---\n\n".join(texts)
    
    def _extract_markdown(self, text: str) -> str:
        """Extract markdown content from response."""
        # Look for ```markdown ... ``` blocks
        match = re.search(r"```markdown\n(.*?)```", text, re.DOTALL)
        if match:
            return match.group(1).strip()
        
        # Look for ``` ... ``` blocks
        match = re.search(r"```\n(.*?)```", text, re.DOTALL)
        if match:
            return match.group(1).strip()
        
        # Return as-is if no code blocks
        return text.strip()
    
    def _parse_categories(self, text: str) -> list[dict]:
        """Parse category suggestions from response."""
        categories = []
        current = None
        
        for line in text.split("\n"):
            line = line.strip()
            
            if line.startswith("category:"):
                if current:
                    categories.append(current)
                current = {
                    "name": line.split(":", 1)[1].strip(),
                    "description": "",
                    "patterns": [],
                }
            elif line.startswith("description:") and current:
                current["description"] = line.split(":", 1)[1].strip()
            elif line.startswith("- ") and current:
                current["patterns"].append(line[2:].strip())
        
        if current:
            categories.append(current)
        
        return categories
    
    def _create_domain_yaml(self, domain_id: str, domain_name: str, tasks: list[str]) -> str:
        """Create domain.yaml content."""
        triggers = {}
        for task in tasks:
            task_id = task.lower().replace(" ", "_")
            triggers[task_id] = [
                task.lower(),
                f"analyze {task.split()[0].lower()}",
                f"review {task.split()[0].lower()}",
            ]
        
        yaml_content = f"""# Domain Configuration: {domain_name}
id: {domain_id}
name: {domain_name}
description: Domain expertise for {domain_name.lower()}

rubric_triggers:
"""
        for task_id, trigger_list in triggers.items():
            yaml_content += f"  {task_id}:\n"
            for trigger in trigger_list:
                yaml_content += f"    - {trigger}\n"
        
        yaml_content += "\nexample_categories:\n"
        # Will be populated based on actual categories created
        
        return yaml_content
    
    def _extract_tasks_from_analysis(self, analysis: str) -> list[str]:
        """Extract task suggestions from analysis."""
        # Look for "Key Tasks" section
        tasks = []
        in_tasks = False
        
        for line in analysis.split("\n"):
            if "Key Tasks" in line or "key tasks" in line:
                in_tasks = True
                continue
            if in_tasks:
                if line.startswith("##") or line.startswith("**"):
                    break
                if line.strip().startswith("-") or line.strip().startswith("*"):
                    task = line.strip().lstrip("-*").strip()
                    if task:
                        tasks.append(task)
        
        return tasks[:5] if tasks else ["General Analysis"]
    
    def _get_patterns_for_category(self, category: str, analysis: str) -> list[str]:
        """Get relevant patterns for a category from analysis."""
        # Simple extraction - could be improved
        patterns = []
        
        # Look for patterns mentioned in context of the category
        for line in analysis.split("\n"):
            if category.lower() in line.lower():
                # Extract anything that looks like a pattern name
                if "-" in line or ":" in line:
                    parts = re.split(r"[-:]", line)
                    for part in parts:
                        part = part.strip()
                        if len(part) > 5 and len(part) < 50:
                            patterns.append(part)
        
        # Default patterns if none found
        if not patterns:
            patterns = [
                f"Strong vs weak {category}",
                f"Common {category} mistakes",
                f"Expert {category} patterns",
            ]
        
        return patterns[:5]
