"""
CLI tool for domain expertise management.

Commands:
    expertise init <domain>       - Create new domain structure
    expertise validate <domain>   - Validate domain files
    expertise index <domain>      - Index examples for search
    expertise query <domain> <q>  - Test semantic search
    expertise list                - List available domains
    expertise stats <domain>      - Show domain statistics
"""

import os
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax

from .engine import ExpertiseEngine
from .parser import parse_example
from .types import ExpertiseConfig

console = Console()


def get_engine(domains_path: str = "./domains") -> ExpertiseEngine:
    """Create engine from environment or defaults."""
    # Check for Supabase config
    supabase_url = os.environ.get("EXPERTISE_SUPABASE_URL")
    supabase_key = os.environ.get("EXPERTISE_SUPABASE_KEY")

    if supabase_url and supabase_key:
        vector_store = {
            "type": "supabase",
            "url": supabase_url,
            "key": supabase_key,
        }
    else:
        vector_store = {
            "type": "sqlite",
            "path": "./cache/embeddings.db",
        }

    config = ExpertiseConfig(
        domains_path=Path(domains_path),
        vector_store=vector_store,
    )

    return ExpertiseEngine.from_config(config)


@click.group()
@click.option(
    "--domains-path",
    "-d",
    default="./domains",
    help="Path to domains directory",
)
@click.pass_context
def main(ctx, domains_path):
    """Domain Expertise CLI - Manage domain knowledge for AI agents."""
    ctx.ensure_object(dict)
    ctx.obj["domains_path"] = domains_path


@main.command()
@click.argument("domain")
@click.pass_context
def init(ctx, domain):
    """Initialize a new domain with template files."""
    domains_path = Path(ctx.obj["domains_path"])
    domain_path = domains_path / domain

    if domain_path.exists():
        console.print(f"[red]Error: Domain '{domain}' already exists[/red]")
        raise SystemExit(1)

    # Create directory structure
    (domain_path / "rubrics").mkdir(parents=True)
    (domain_path / "examples" / "general").mkdir(parents=True)
    (domain_path / "frameworks").mkdir(parents=True)

    # Create domain.yaml
    domain_yaml = f"""# Domain Configuration
id: {domain}
name: {domain.replace('_', ' ').title()}
description: Domain expertise for {domain}

# Rubric triggers - maps tasks to rubric files
rubric_triggers:
  general_analysis:
    - analyze
    - review
    - evaluate

# Example categories
example_categories:
  - general
"""
    (domain_path / "domain.yaml").write_text(domain_yaml)

    # Create principles.md template
    principles_md = f"""# Core Principles: {domain.replace('_', ' ').title()}

## 1. [Principle Title]

[2-3 sentence explanation of this principle.]

Why this matters: [Why this is non-negotiable in this domain.]

## 2. [Principle Title]

[Explanation.]

Why this matters: [Importance.]

## 3. [Principle Title]

[Explanation.]

Why this matters: [Importance.]
"""
    (domain_path / "principles.md").write_text(principles_md)

    # Create example rubric template
    rubric_md = """# Rubric: General Analysis

Evaluation framework for analyzing content in this domain.

## Scoring

### 5 - Exceptional
- Exceeds all quality criteria
- Demonstrates deep understanding
- Would be used as a positive example

### 3 - Adequate
- Meets basic requirements
- No major issues
- Room for improvement

### 1 - Slop
- Fails to meet basic criteria
- Contains clear problems
- Needs significant revision

## Red Flags
- [Warning sign 1]
- [Warning sign 2]

## Evaluation Questions
1. [Key question to ask when evaluating?]
2. [Another evaluation question?]
"""
    (domain_path / "rubrics" / "general-analysis.md").write_text(rubric_md)

    # Create example contrast template
    example_md = f"""---
id: {domain}-contrast-001
domain: {domain}
category: general
tags: [example, template]
---

# [Pattern Name]

## WEAK
"[The weak example - actual text or realistic example]"

### Why it's weak:
- [Specific reason tied to principles]
- [Another reason]

## STRONG
"[The strong example - actual text or realistic example]"

### Why it works:
- [Specific reason tied to principles]
- [Another reason]

## Teaching Point
[One sentence insight that captures the key lesson.]

## When to Apply
[Context for when to use this pattern.]
"""
    (domain_path / "examples" / "general" / "contrast-001.md").write_text(example_md)

    console.print(f"[green]Created domain '{domain}' at {domain_path}[/green]")
    console.print("\nFiles created:")
    console.print(f"  - {domain_path}/domain.yaml")
    console.print(f"  - {domain_path}/principles.md")
    console.print(f"  - {domain_path}/rubrics/general-analysis.md")
    console.print(f"  - {domain_path}/examples/general/contrast-001.md")
    console.print("\n[dim]Edit these files to add your domain expertise.[/dim]")


@main.command()
@click.argument("domain")
@click.pass_context
def validate(ctx, domain):
    """Validate a domain's structure and content."""
    engine = get_engine(ctx.obj["domains_path"])

    try:
        result = engine.validate_domain(domain)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise SystemExit(1)

    # Display results
    if result["valid"]:
        console.print(f"[green]Domain '{domain}' is valid[/green]")
    else:
        console.print(f"[red]Domain '{domain}' has issues[/red]")

    # Stats table
    table = Table(title="Domain Statistics")
    table.add_column("Component", style="cyan")
    table.add_column("Count", style="green")
    table.add_row("Principles", str(result["stats"]["principles"]))
    table.add_row("Rubrics", str(result["stats"]["rubrics"]))
    table.add_row("Examples", str(result["stats"]["examples"]))
    console.print(table)

    # Issues
    if result["issues"]:
        console.print("\n[red]Issues (must fix):[/red]")
        for issue in result["issues"]:
            console.print(f"  - {issue}")

    # Warnings
    if result["warnings"]:
        console.print("\n[yellow]Warnings:[/yellow]")
        for warning in result["warnings"]:
            console.print(f"  - {warning}")


@main.command()
@click.argument("domain")
@click.option("--force", "-f", is_flag=True, help="Re-index all examples")
@click.pass_context
def index(ctx, domain, force):
    """Index domain examples for semantic search."""
    engine = get_engine(ctx.obj["domains_path"])

    try:
        domain_obj = engine.load_domain(domain)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise SystemExit(1)

    # Find all example files
    examples_path = domain_obj.examples_path
    if not examples_path.exists():
        console.print(f"[red]No examples directory found at {examples_path}[/red]")
        raise SystemExit(1)

    example_files = list(examples_path.rglob("*.md"))
    if not example_files:
        console.print("[yellow]No example files found[/yellow]")
        return

    console.print(f"Found {len(example_files)} example files")

    # Delete existing if force
    if force:
        deleted = engine.vector_store.delete_domain(domain)
        console.print(f"[dim]Deleted {deleted} existing examples[/dim]")

    # Parse and index examples
    examples = []
    with console.status("Parsing examples..."):
        for file_path in example_files:
            try:
                content = file_path.read_text()
                example = parse_example(content, file_path.stem)
                example.domain = domain  # Ensure domain is set
                if not example.category:
                    # Get category from parent directory
                    example.category = file_path.parent.name
                examples.append(example)
            except Exception as e:
                console.print(f"[yellow]Warning: Could not parse {file_path}: {e}[/yellow]")

    console.print(f"Parsed {len(examples)} examples")

    # Index with progress
    with console.status("Indexing examples (generating embeddings)..."):
        indexed = engine.vector_store.index(examples)

    console.print(f"[green]Indexed {indexed} examples[/green]")

    # Show indexed count
    total = engine.vector_store.count(domain)
    console.print(f"Total examples in store for '{domain}': {total}")


@main.command()
@click.argument("domain")
@click.argument("query")
@click.option("--limit", "-n", default=5, help="Number of results")
@click.option("--category", "-c", help="Filter by category")
@click.pass_context
def query(ctx, domain, query, limit, category):
    """Search for relevant examples."""
    engine = get_engine(ctx.obj["domains_path"])

    examples = engine.get_examples(
        domain_name=domain,
        query=query,
        category=category,
        limit=limit,
    )

    if not examples:
        console.print("[yellow]No examples found[/yellow]")
        return

    console.print(f"Found {len(examples)} relevant examples:\n")

    for i, ex in enumerate(examples, 1):
        similarity = f"{ex.similarity:.2f}" if ex.similarity else "N/A"
        console.print(Panel(
            f"[bold]WEAK:[/bold] {ex.weak_content[:100]}...\n\n"
            f"[bold]STRONG:[/bold] {ex.strong_content[:100]}...\n\n"
            f"[bold]Teaching:[/bold] {ex.teaching_point}",
            title=f"[{i}] {ex.id} (similarity: {similarity})",
            subtitle=f"category: {ex.category} | tags: {', '.join(ex.tags)}",
        ))


@main.command("list")
@click.pass_context
def list_domains(ctx):
    """List available domains."""
    engine = get_engine(ctx.obj["domains_path"])
    domains = engine.list_domains()

    if not domains:
        console.print("[yellow]No domains found[/yellow]")
        return

    table = Table(title="Available Domains")
    table.add_column("Domain", style="cyan")
    table.add_column("Indexed", style="green")

    for domain in domains:
        count = engine.vector_store.count(domain)
        table.add_row(domain, str(count))

    console.print(table)


@main.command()
@click.argument("domain")
@click.pass_context
def stats(ctx, domain):
    """Show detailed statistics for a domain."""
    engine = get_engine(ctx.obj["domains_path"])

    try:
        domain_obj = engine.load_domain(domain)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise SystemExit(1)

    # Validate to get stats
    result = engine.validate_domain(domain)

    # Show principles
    console.print("\n[bold]Principles:[/bold]")
    for p in domain_obj.principles:
        console.print(f"  - {p.title}")

    # Show rubrics
    console.print("\n[bold]Rubrics:[/bold]")
    for r in domain_obj.rubrics:
        console.print(f"  - {r.name}")

    # Show example categories
    console.print("\n[bold]Example Categories:[/bold]")
    if domain_obj.examples_path.exists():
        for cat_dir in domain_obj.examples_path.iterdir():
            if cat_dir.is_dir():
                count = len(list(cat_dir.glob("*.md")))
                console.print(f"  - {cat_dir.name}: {count} examples")

    # Indexed count
    indexed = engine.vector_store.count(domain)
    console.print(f"\n[bold]Indexed examples:[/bold] {indexed}")


@main.command()
@click.argument("domain")
@click.argument("task")
@click.argument("query")
@click.option("--budget", "-b", default=8000, help="Token budget")
@click.pass_context
def context(ctx, domain, task, query, budget):
    """Prepare full analysis context (what an agent would receive)."""
    engine = get_engine(ctx.obj["domains_path"])

    try:
        analysis_context = engine.prepare_analysis_context(
            domain_name=domain,
            task=task,
            query=query,
            token_budget=budget,
        )
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise SystemExit(1)

    console.print(Panel(
        f"[bold]Token count:[/bold] {analysis_context.token_count}",
        title="Analysis Context",
    ))

    # Show principles
    console.print("\n[bold cyan]═══ PRINCIPLES ═══[/bold cyan]")
    console.print(analysis_context.principles[:500] + "..." if len(analysis_context.principles) > 500 else analysis_context.principles)

    # Show rubric
    if analysis_context.rubric:
        console.print(f"\n[bold cyan]═══ RUBRIC: {analysis_context.rubric.name} ═══[/bold cyan]")
        console.print(f"Description: {analysis_context.rubric.description}")
        console.print(f"Red flags: {', '.join(analysis_context.rubric.red_flags[:3])}...")

    # Show examples
    console.print(f"\n[bold cyan]═══ EXAMPLES ({len(analysis_context.examples)}) ═══[/bold cyan]")
    for ex in analysis_context.examples:
        console.print(f"\n[dim]{ex.id}[/dim]")
        console.print(f"WEAK: {ex.weak_content[:80]}...")
        console.print(f"STRONG: {ex.strong_content[:80]}...")


@main.command()
@click.argument("domain_id")
@click.argument("domain_name")
@click.option("--source", "-s", type=click.Path(exists=True), help="Path to source documents")
@click.option("--tasks", "-t", multiple=True, help="Tasks for rubrics (can specify multiple)")
@click.option("--categories", "-c", multiple=True, help="Example categories (can specify multiple)")
@click.option("--examples", "-e", default=3, help="Examples per category")
@click.pass_context
def author(ctx, domain_id, domain_name, source, tasks, categories, examples):
    """Create a new domain from source documents using AI.

    This command uses Claude to analyze source documents and generate
    a complete domain with principles, rubrics, and contrast examples.

    Example:
        expertise author copywriting "Direct Response Copywriting" -s ./sources/
    """
    from .authoring import DomainAuthoringAgent

    domains_path = Path(ctx.obj["domains_path"])
    output_path = domains_path / domain_id

    if output_path.exists():
        console.print(f"[red]Error: Domain '{domain_id}' already exists[/red]")
        raise SystemExit(1)

    # Check for API key
    if not os.environ.get("ANTHROPIC_API_KEY"):
        console.print("[red]Error: ANTHROPIC_API_KEY environment variable not set[/red]")
        raise SystemExit(1)

    agent = DomainAuthoringAgent()

    def progress(msg):
        console.print(f"[dim]{msg}[/dim]")

    console.print(f"\n[bold]Creating domain: {domain_name}[/bold]\n")

    try:
        stats = agent.create_domain(
            domain_id=domain_id,
            domain_name=domain_name,
            output_path=output_path,
            source_path=source,
            tasks=list(tasks) if tasks else None,
            categories=list(categories) if categories else None,
            examples_per_category=examples,
            progress_callback=progress,
        )
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise SystemExit(1)

    # Show results
    console.print(f"\n[green]Domain '{domain_id}' created successfully![/green]")
    console.print(f"\nTokens used: {stats['tokens_used']:,}")
    console.print(f"Files created: {len(stats['files_created'])}")

    table = Table(title="Created Files")
    table.add_column("File", style="cyan")
    for f in stats["files_created"]:
        table.add_row(str(Path(f).relative_to(output_path.parent)))
    console.print(table)

    console.print(f"\n[dim]Next: Review and edit the generated files, then run:[/dim]")
    console.print(f"  expertise validate {domain_id}")
    console.print(f"  expertise index {domain_id}")


@main.command()
@click.argument("source_path", type=click.Path(exists=True))
@click.option("--recursive/--no-recursive", default=True, help="Search subdirectories")
def load(source_path, recursive):
    """Load and preview source documents.

    Use this to verify documents will be loaded correctly before authoring.
    """
    from .loaders import UnifiedLoader

    loader = UnifiedLoader()
    source_path = Path(source_path)

    if source_path.is_dir():
        docs = loader.load_directory(source_path, recursive=recursive)
    else:
        docs = loader.load(source_path)

    console.print(f"\n[bold]Loaded {len(docs)} documents[/bold]\n")

    table = Table(title="Documents")
    table.add_column("Source", style="cyan", max_width=40)
    table.add_column("Title", style="green", max_width=30)
    table.add_column("Words", style="yellow", justify="right")
    table.add_column("Section", style="dim", max_width=20)

    for doc in docs[:20]:  # Limit display
        source = Path(doc.source).name if doc.source != "text" else doc.source
        table.add_row(
            source,
            doc.title or "-",
            str(doc.word_count),
            doc.section or "-",
        )

    console.print(table)

    if len(docs) > 20:
        console.print(f"\n[dim]... and {len(docs) - 20} more documents[/dim]")

    total_words = sum(d.word_count for d in docs)
    console.print(f"\n[bold]Total words:[/bold] {total_words:,}")
    console.print(f"[bold]Estimated tokens:[/bold] ~{total_words * 1.3:,.0f}")


@main.command()
@click.argument("domain")
@click.argument("content_type", type=click.Choice(["principle", "rubric", "example"]))
@click.argument("output_file", type=click.Path())
@click.option("--pattern", "-p", help="Pattern name (for examples)")
@click.option("--task", "-t", help="Task name (for rubrics)")
@click.option("--category", "-c", help="Category (for examples)")
@click.pass_context
def generate(ctx, domain, content_type, output_file, pattern, task, category):
    """Generate a single piece of domain content.

    Use this for adding individual pieces to an existing domain.

    Examples:
        expertise generate copywriting rubric email-analysis.md -t "Email Analysis"
        expertise generate copywriting example contrast-005.md -p "Social proof" -c headlines
    """
    from .authoring import DomainAuthoringAgent

    if not os.environ.get("ANTHROPIC_API_KEY"):
        console.print("[red]Error: ANTHROPIC_API_KEY environment variable not set[/red]")
        raise SystemExit(1)

    agent = DomainAuthoringAgent()
    domains_path = Path(ctx.obj["domains_path"])

    # Load existing domain for context
    engine = get_engine(ctx.obj["domains_path"])
    try:
        domain_obj = engine.load_domain(domain)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise SystemExit(1)

    # Get principles as context
    principles_text = domain_obj.principles_path.read_text() if domain_obj.principles_path.exists() else ""
    agent._current_analysis = f"Domain: {domain}\n\nPrinciples:\n{principles_text}"

    console.print(f"[dim]Generating {content_type}...[/dim]")

    if content_type == "rubric":
        if not task:
            console.print("[red]Error: --task is required for rubrics[/red]")
            raise SystemExit(1)
        result = agent.extract_rubric(task)

    elif content_type == "example":
        if not pattern:
            console.print("[red]Error: --pattern is required for examples[/red]")
            raise SystemExit(1)
        if not category:
            category = "general"

        example_id = f"{category}-{Path(output_file).stem}"
        result = agent.extract_contrast_example(
            pattern=pattern,
            domain=domain,
            category=category,
            example_id=example_id,
            tags=[category, domain],
        )

    else:  # principle
        result = agent.extract_principles(domain_obj.config.get("name", domain))

    # Write output
    output_path = Path(output_file)
    if not output_path.is_absolute():
        # Put in appropriate subdirectory
        if content_type == "rubric":
            output_path = domains_path / domain / "rubrics" / output_file
        elif content_type == "example":
            output_path = domains_path / domain / "examples" / (category or "general") / output_file
        else:
            output_path = domains_path / domain / output_file

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(result.content)

    console.print(f"[green]Created: {output_path}[/green]")
    console.print(f"Tokens used: {result.tokens_used:,}")


if __name__ == "__main__":
    main()
