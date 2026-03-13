"""
Knowledge Management CLI - Feed external data to your LLM.

This module provides commands to:
- Index documents (PDF, TXT, MD, code files)
- Index entire directories
- Query your knowledge base
- Manage indexed documents

Usage:
    grace knowledge index-file document.pdf
    grace knowledge index-dir ./docs --pattern "*.md"
    grace knowledge query "What is the architecture?"
    grace knowledge list
    grace knowledge delete doc_id
"""

import os
import typer
from typing import Optional, List
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from open_grace.memory.rag_engine import RAGEngine, get_rag_engine
from open_grace.memory.vector_store import get_vector_store
from open_grace.memory.document_processor import get_document_processor


app = typer.Typer(help="Knowledge management - Feed data to your LLM")
console = Console()


@app.command("index-file")
def index_file(
    file_path: str = typer.Argument(..., help="Path to file to index"),
    doc_id: Optional[str] = typer.Option(None, "--id", help="Custom document ID"),
    category: Optional[str] = typer.Option(None, "--category", "-c", help="Document category")
):
    """Index a single file into the knowledge base.
    
    Supported formats: PDF, DOCX, DOC, XLSX, XLS, CSV, TXT, MD, HTML, and code files
    """
    path = Path(file_path)
    
    if not path.exists():
        console.print(f"[red]Error: File not found: {file_path}[/red]")
        raise typer.Exit(1)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task(f"Indexing {path.name}...", total=None)
        
        try:
            rag = get_rag_engine()
            metadata = {"category": category} if category else {}
            
            rag.index_file(str(path), doc_id=doc_id, metadata=metadata)
            
            progress.update(task, completed=True)
            console.print(f"[green]✓ Indexed: {path.name}[/green]")
            console.print(f"  [dim]Size: {path.stat().st_size:,} bytes[/dim]")
            
            # Show extraction info if available
            processor = get_document_processor()
            extracted = processor.extract(str(path))
            if extracted.pages:
                console.print(f"  [dim]Pages: {extracted.pages}[/dim]")
            if extracted.sheets:
                console.print(f"  [dim]Sheets: {', '.join(extracted.sheets)}[/dim]")
            
        except Exception as e:
            console.print(f"[red]Error indexing file: {e}[/red]")
            raise typer.Exit(1)


@app.command("index-dir")
def index_directory(
    dir_path: str = typer.Argument(..., help="Directory to index"),
    pattern: str = typer.Option("*.txt", "--pattern", "-p", help="File pattern to match"),
    recursive: bool = typer.Option(True, "--recursive/--no-recursive", "-r/-R", help="Search recursively"),
    category: Optional[str] = typer.Option(None, "--category", "-c", help="Document category")
):
    """Index all matching files in a directory."""
    path = Path(dir_path)
    
    if not path.exists():
        console.print(f"[red]Error: Directory not found: {dir_path}[/red]")
        raise typer.Exit(1)
    
    if not path.is_dir():
        console.print(f"[red]Error: Not a directory: {dir_path}[/red]")
        raise typer.Exit(1)
    
    console.print(f"[blue]Indexing files from {path}...[/blue]")
    console.print(f"[dim]Pattern: {pattern}, Recursive: {recursive}[/dim]\n")
    
    try:
        rag = get_rag_engine()
        
        # Find files
        if recursive:
            files = list(path.rglob(pattern))
        else:
            files = list(path.glob(pattern))
        
        if not files:
            console.print("[yellow]No files found matching the pattern.[/yellow]")
            return
        
        console.print(f"Found {len(files)} files to index\n")
        
        # Index files
        success_count = 0
        failed_files = []
        
        with Progress(console=console) as progress:
            task = progress.add_task("Indexing...", total=len(files))
            
            for file_path in files:
                try:
                    metadata = {"category": category} if category else {}
                    rag.index_file(str(file_path), metadata=metadata)
                    success_count += 1
                except Exception as e:
                    failed_files.append((file_path.name, str(e)))
                
                progress.advance(task)
        
        # Results
        console.print(f"\n[green]✓ Successfully indexed: {success_count}/{len(files)} files[/green]")
        
        if failed_files:
            console.print(f"\n[yellow]Failed to index {len(failed_files)} files:[/yellow]")
            for name, error in failed_files[:5]:
                console.print(f"  [dim]- {name}: {error}[/dim]")
            if len(failed_files) > 5:
                console.print(f"  [dim]... and {len(failed_files) - 5} more[/dim]")
                
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command("index-text")
def index_text(
    content: str = typer.Argument(..., help="Text content to index"),
    doc_id: str = typer.Argument(..., help="Document ID"),
    category: Optional[str] = typer.Option(None, "--category", "-c", help="Document category")
):
    """Index raw text content."""
    try:
        rag = get_rag_engine()
        metadata = {"category": category} if category else {}
        
        rag.index_document(doc_id, content, metadata=metadata)
        
        console.print(f"[green]✓ Indexed text as: {doc_id}[/green]")
        console.print(f"  [dim]Length: {len(content):,} characters[/dim]")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command("query")
def query_knowledge(
    question: str = typer.Argument(..., help="Question to ask"),
    top_k: int = typer.Option(5, "--top-k", "-k", help="Number of documents to retrieve"),
    show_context: bool = typer.Option(False, "--show-context", help="Show retrieved context")
):
    """Query your knowledge base."""
    try:
        rag = get_rag_engine()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Searching knowledge base...", total=None)
            
            response = rag.query(question)
            progress.update(task, completed=True)
        
        # Display answer
        console.print(f"\n[bold blue]Answer:[/bold blue]")
        console.print(response.answer)
        
        # Display sources
        if response.sources:
            console.print(f"\n[bold green]Sources:[/bold green]")
            for source in response.sources:
                score_pct = int(source['score'] * 100)
                console.print(f"  • {source['id']} [dim](relevance: {score_pct}%)[/dim]")
        
        # Show context if requested
        if show_context:
            console.print(f"\n[bold yellow]Retrieved Context:[/bold yellow]")
            console.print(response.context.context_text[:2000] + "...")
        
        # Stats
        console.print(f"\n[dim]Model: {response.model_used} | Latency: {response.latency_ms:.0f}ms[/dim]")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command("list")
def list_documents(
    category: Optional[str] = typer.Option(None, "--category", "-c", help="Filter by category")
):
    """List all indexed documents."""
    try:
        store = get_vector_store()
        docs = store.list_documents()
        
        if not docs:
            console.print("[yellow]No documents indexed yet.[/yellow]")
            console.print("[dim]Use 'grace knowledge index-file' or 'grace knowledge index-dir' to add documents.[/dim]")
            return
        
        # Filter by category if specified
        if category:
            docs = [d for d in docs if d.metadata.get('category') == category]
        
        # Create table
        table = Table(title="Indexed Documents")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Category", style="green")
        table.add_column("Source", style="dim")
        table.add_column("Indexed", style="dim")
        
        for doc in docs:
            cat = doc.metadata.get('category', '-')
            source = doc.metadata.get('filename', doc.id[:50])
            indexed = doc.metadata.get('indexed_at', 'Unknown')[:10]
            
            table.add_row(
                doc.id[:40],
                cat,
                source,
                indexed
            )
        
        console.print(table)
        console.print(f"\n[dim]Total: {len(docs)} documents[/dim]")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command("delete")
def delete_document(
    doc_id: str = typer.Argument(..., help="Document ID to delete"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation")
):
    """Delete a document from the knowledge base."""
    try:
        store = get_vector_store()
        
        # Check if exists
        doc = store.get_document(doc_id)
        if not doc:
            console.print(f"[red]Document not found: {doc_id}[/red]")
            raise typer.Exit(1)
        
        # Confirm deletion
        if not force:
            confirm = typer.confirm(f"Delete document '{doc_id}'?")
            if not confirm:
                console.print("[dim]Cancelled.[/dim]")
                return
        
        # Delete
        store.delete_document(doc_id)
        console.print(f"[green]✓ Deleted: {doc_id}[/green]")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command("stats")
def knowledge_stats():
    """Show knowledge base statistics."""
    try:
        store = get_vector_store()
        docs = store.list_documents()
        
        # Calculate stats
        total_docs = len(docs)
        categories = {}
        file_types = {}
        total_size = 0
        
        for doc in docs:
            cat = doc.metadata.get('category', 'Uncategorized')
            categories[cat] = categories.get(cat, 0) + 1
            
            ftype = doc.metadata.get('file_type', 'Unknown')
            file_types[ftype] = file_types.get(ftype, 0) + 1
            
            total_size += doc.metadata.get('file_size', 0)
        
        # Display
        console.print("[bold blue]Knowledge Base Statistics[/bold blue]\n")
        console.print(f"Total Documents: {total_docs}")
        console.print(f"Total Size: {total_size / 1024 / 1024:.2f} MB")
        
        if categories:
            console.print("\n[bold]Categories:[/bold]")
            for cat, count in sorted(categories.items()):
                console.print(f"  {cat}: {count}")
        
        if file_types:
            console.print("\n[bold]File Types:[/bold]")
            for ftype, count in sorted(file_types.items()):
                console.print(f"  {ftype}: {count}")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command("formats")
def list_formats():
    """List supported document formats."""
    processor = get_document_processor()
    formats = processor.get_supported_formats()
    
    console.print("[bold blue]Supported Document Formats[/bold blue]\n")
    
    format_groups = {
        "Documents": ['.pdf', '.docx', '.doc'],
        "Spreadsheets": ['.xlsx', '.xls', '.csv'],
        "Text": ['.txt', '.md', '.rst'],
        "Web": ['.html', '.htm'],
        "Data": ['.json', '.xml'],
    }
    
    for group, extensions in format_groups.items():
        console.print(f"[bold]{group}:[/bold]")
        supported = [ext for ext in extensions if ext in formats]
        for ext in supported:
            console.print(f"  {ext}")
        console.print()
    
    console.print("[dim]Note: Additional formats may be supported as plain text.[/dim]")
    console.print("[dim]Install optional dependencies for better support:[/dim]")
    console.print("  [dim]pip install PyPDF2 python-docx pandas openpyxl beautifulsoup4[/dim]")


@app.command("import-web")
def import_webpage(
    url: str = typer.Argument(..., help="URL to import"),
    doc_id: Optional[str] = typer.Option(None, "--id", help="Custom document ID"),
    category: str = typer.Option("web", "--category", "-c", help="Document category")
):
    """Import a webpage into the knowledge base (requires requests and beautifulsoup4)."""
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError:
        console.print("[red]Error: This feature requires 'requests' and 'beautifulsoup4'[/red]")
        console.print("[dim]Install with: pip install requests beautifulsoup4[/dim]")
        raise typer.Exit(1)
    
    try:
        console.print(f"[blue]Fetching {url}...[/blue]")
        
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract text (remove scripts, styles)
        for script in soup(["script", "style"]):
            script.decompose()
        
        text = soup.get_text(separator='\n', strip=True)
        
        # Clean up whitespace
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        text = '\n'.join(lines)
        
        # Index
        rag = get_rag_engine()
        doc_id = doc_id or f"web_{hash(url) % 10000000}"
        
        metadata = {
            "category": category,
            "source_url": url,
            "title": soup.title.string if soup.title else "Untitled"
        }
        
        rag.index_document(doc_id, text, metadata=metadata)
        
        console.print(f"[green]✓ Imported webpage: {doc_id}[/green]")
        console.print(f"  [dim]Title: {metadata['title']}[/dim]")
        console.print(f"  [dim]Content length: {len(text):,} characters[/dim]")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
