#!/usr/bin/env python3
"""
Open Grace CLI - Command-line interface for the Open Grace platform.

Usage:
    grace --help
    grace status
    grace task "Organize my downloads"
    grace agents list
    grace vault list
"""

import asyncio
import sys
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from open_grace.kernel.orchestrator import GraceOrchestrator, get_orchestrator
from open_grace.security.vault import get_vault
from open_grace.model_router.router import get_router, RoutingStrategy
from open_grace.cli import knowledge


app = typer.Typer(
    name="grace",
    help="Open Grace TaskForge AI - A Local AI Operating System",
    rich_markup_mode="rich"
)
console = Console()


@app.callback()
def main(
    version: bool = typer.Option(False, "--version", "-v", help="Show version"),
):
    """Open Grace TaskForge AI - Local AI Operating System."""
    if version:
        console.print("[bold blue]Open Grace[/bold blue] version [green]0.3.0[/green]")
        raise typer.Exit()


@app.command()
def status():
    """Show system status."""
    async def _show_status():
        orchestrator = await get_orchestrator()
        status = await orchestrator.get_system_status()
        
        # Main status panel
        console.print(Panel.fit(
            f"[bold blue]Open Grace[/bold blue] Instance: [cyan]{status['instance_id']}[/cyan]\n"
            f"Initialized: [green]{'Yes' if status['initialized'] else 'No'}[/green]\n"
            f"Agents: [yellow]{status['agents']['total']}[/yellow] total\n"
            f"Tasks: [yellow]{status['tasks']['total']}[/yellow] total\n"
            f"Queue: [yellow]{status['queue_size']}[/yellow] pending",
            title="System Status",
            border_style="blue"
        ))
        
        # Provider status table
        if status['providers']:
            table = Table(title="AI Model Providers", box=box.ROUNDED)
            table.add_column("Provider", style="cyan")
            table.add_column("Available", style="green")
            table.add_column("Model", style="yellow")
            table.add_column("Cost/1K", style="magenta")
            
            for provider, info in status['providers'].items():
                available = "[green]✓[/green]" if info['available'] else "[red]✗[/red]"
                cost = f"${info['cost_per_1k_input'] + info['cost_per_1k_output']:.4f}"
                table.add_row(provider, available, info['model'], cost)
            
            console.print(table)
    
    asyncio.run(_show_status())


@app.command()
def task(
    description: str = typer.Argument(..., help="Task description"),
    agent: Optional[str] = typer.Option(None, "--agent", "-a", help="Agent type to use"),
    priority: int = typer.Option(5, "--priority", "-p", help="Task priority (1-10)"),
    wait: bool = typer.Option(True, "--wait/--no-wait", help="Wait for task completion"),
):
    """Submit a task for execution."""
    async def _submit_task():
        orchestrator = await get_orchestrator()
        
        with console.status("[bold green]Submitting task..."):
            task_id = await orchestrator.submit_task(
                description=description,
                agent_type=agent,
                priority=priority
            )
        
        console.print(f"[green]Task submitted:[/green] [cyan]{task_id}[/cyan]")
        
        if wait:
            with console.status("[bold yellow]Executing task..."):
                try:
                    result = await orchestrator.get_task_result(task_id, timeout=300)
                    if result:
                        console.print(Panel(
                            str(result.get('content', result)),
                            title=f"[green]Task Result[/green]",
                            border_style="green"
                        ))
                    else:
                        console.print("[yellow]Task completed with no result[/yellow]")
                except Exception as e:
                    console.print(f"[red]Task failed:[/red] {e}")
    
    asyncio.run(_submit_task())


@app.command()
def ask(
    prompt: str = typer.Argument(..., help="Question or prompt"),
    strategy: str = typer.Option("hybrid", "--strategy", "-s", 
                                help="Routing strategy: local_only, cost_optimized, quality_first, hybrid"),
):
    """Ask the AI a question."""
    async def _ask():
        router = get_router()
        
        with console.status("[bold green]Thinking..."):
            try:
                strategy_enum = RoutingStrategy(strategy)
                response = router.generate(prompt, strategy=strategy_enum)
                
                console.print(Panel(
                    response.content,
                    title=f"[green]{response.provider.value} / {response.model}[/green]",
                    subtitle=f"Latency: {response.latency_ms:.0f}ms",
                    border_style="blue"
                ))
            except Exception as e:
                console.print(f"[red]Error:[/red] {e}")
    
    asyncio.run(_ask())


# Agent commands
agents_app = typer.Typer(help="Agent management commands")
app.add_typer(agents_app, name="agents")


@agents_app.command("list")
def list_agents():
    """List registered agents."""
    async def _list():
        orchestrator = await get_orchestrator()
        agents = await orchestrator.list_agents()
        
        if not agents:
            console.print("[yellow]No agents registered[/yellow]")
            return
        
        table = Table(title="Registered Agents", box=box.ROUNDED)
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Type", style="yellow")
        table.add_column("Status", style="magenta")
        table.add_column("Tasks", style="blue")
        
        for agent in agents:
            table.add_row(
                agent.id,
                agent.name,
                agent.agent_type,
                agent.status.value,
                str(agent.task_count)
            )
        
        console.print(table)
    
    asyncio.run(_list())


# Vault commands
vault_app = typer.Typer(help="Secret vault management")
app.add_typer(vault_app, name="vault")


@vault_app.command("list")
def list_secrets(
    category: Optional[str] = typer.Option(None, "--category", "-c", help="Filter by category"),
):
    """List secrets in the vault."""
    vault = get_vault()
    secrets = vault.list_secrets(category=category)
    
    if not secrets:
        console.print("[yellow]No secrets found[/yellow]")
        return
    
    table = Table(title="Vault Secrets", box=box.ROUNDED)
    table.add_column("Key", style="cyan")
    table.add_column("Category", style="green")
    table.add_column("Description", style="yellow")
    
    for key in secrets:
        entry = vault.get_secret_entry(key)
        if entry:
            table.add_row(key, entry.category, entry.description)
    
    console.print(table)


@vault_app.command("set")
def set_secret(
    key: str = typer.Argument(..., help="Secret key"),
    value: str = typer.Argument(..., help="Secret value"),
    category: str = typer.Option("general", "--category", "-c", help="Secret category"),
    description: str = typer.Option("", "--description", "-d", help="Description"),
):
    """Store a secret in the vault."""
    vault = get_vault()
    vault.set_secret(key, value, category=category, description=description)
    console.print(f"[green]Secret stored:[/green] [cyan]{key}[/cyan]")


@vault_app.command("delete")
def delete_secret(key: str = typer.Argument(..., help="Secret key to delete")):
    """Delete a secret from the vault."""
    vault = get_vault()
    if vault.delete_secret(key):
        console.print(f"[green]Secret deleted:[/green] [cyan]{key}[/cyan]")
    else:
        console.print(f"[red]Secret not found:[/red] [cyan]{key}[/cyan]")


# Router commands
router_app = typer.Typer(help="Model router management")
app.add_typer(router_app, name="router")


@router_app.command("providers")
def list_providers():
    """List available model providers."""
    router = get_router()
    providers = router.get_provider_status()
    
    table = Table(title="Model Providers", box=box.ROUNDED)
    table.add_column("Provider", style="cyan")
    table.add_column("Available", style="green")
    table.add_column("Model", style="yellow")
    table.add_column("Input Cost", style="magenta")
    table.add_column("Output Cost", style="magenta")
    
    for provider, info in providers.items():
        available = "[green]✓[/green]" if info['available'] else "[red]✗[/red]"
        table.add_row(
            provider,
            available,
            info['model'],
            f"${info['cost_per_1k_input']:.4f}",
            f"${info['cost_per_1k_output']:.4f}"
        )
    
    console.print(table)


@router_app.command("add-key")
def add_api_key(
    provider: str = typer.Argument(..., help="Provider name (openai, anthropic, gemini, deepseek)"),
    api_key: str = typer.Argument(..., help="API key"),
):
    """Add an API key for a provider."""
    from open_grace.model_router.clients import ModelProvider
    
    router = get_router()
    try:
        provider_enum = ModelProvider(provider)
        router.add_api_key(provider_enum, api_key)
        console.print(f"[green]API key added for {provider}[/green]")
    except ValueError:
        console.print(f"[red]Invalid provider: {provider}[/red]")
        console.print("Valid providers: openai, anthropic, gemini, deepseek")


# Knowledge commands
app.add_typer(knowledge.app, name="knowledge")


if __name__ == "__main__":
    app()