"""Command Line Interface for AI MCP Toolkit."""

import asyncio
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

from .utils.config import Config, load_config, create_default_config
from .utils.logger import configure_logging
from .server.http_server import HTTPServer, run_http_server
from .models.ollama_client import OllamaClient

app = typer.Typer(
    name="ai-mcp-toolkit",
    help="AI-powered text processing toolkit with MCP protocol support",
    no_args_is_help=True
)

console = Console()


@app.command()
def serve(
    host: str = typer.Option("localhost", "--host", "-h", help="Server host"),
    port: int = typer.Option(8000, "--port", "-p", help="Server port"),
    config_file: Optional[Path] = typer.Option(None, "--config", "-c", help="Configuration file path"),
    log_level: str = typer.Option("INFO", "--log-level", "-l", help="Logging level")
):
    """Start the MCP server."""
    try:
        # Load configuration
        config = load_config(config_file)
        config.host = host
        config.port = port
        config.log_level = log_level.upper()
        
        # Configure logging
        configure_logging(config.log_level, config.log_file)
        
        console.print(Panel.fit(
            f"[bold green]Starting AI MCP Toolkit Server[/bold green]\n\n"
            f"Host: {host}\n"
            f"Port: {port}\n"
            f"Model: {config.ollama_model}\n"
            f"Log Level: {log_level}",
            title="Server Configuration"
        ))
        
        # Run HTTP server
        asyncio.run(run_http_server(host, port, config))
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Server stopped by user[/yellow]")
    except Exception as e:
        console.print(f"[red]Error starting server: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def ui(
    host: str = typer.Option("localhost", "--host", "-h", help="UI host"),
    port: int = typer.Option(5173, "--port", "-p", help="UI port"),
    config_file: Optional[Path] = typer.Option(None, "--config", "-c", help="Configuration file path")
):
    """Launch the web UI (Svelte development server)."""
    try:
        config = load_config(config_file)
        
        # Find the UI directory
        ui_dir = Path(__file__).parent.parent.parent / "ui"
        
        if not ui_dir.exists():
            console.print("[red]UI directory not found. Make sure you're running from the project root.[/red]")
            console.print(f"[yellow]Looking for: {ui_dir}[/yellow]")
            raise typer.Exit(1)
        
        console.print(f"[green]Starting Svelte UI development server...[/green]")
        console.print(f"[yellow]UI will be available at: http://{host}:{port}[/yellow]")
        console.print("[yellow]Note: Make sure the MCP server is running on port 8000![/yellow]")
        
        # Check if node_modules exists
        if not (ui_dir / "node_modules").exists():
            console.print("[yellow]Installing UI dependencies...[/yellow]")
            result = subprocess.run(["npm", "install"], cwd=ui_dir, capture_output=True, text=True)
            if result.returncode != 0:
                console.print(f"[red]Failed to install dependencies: {result.stderr}[/red]")
                raise typer.Exit(1)
        
        # Set environment variables
        env = os.environ.copy()
        env['HOST'] = host
        env['PORT'] = str(port)
        
        # Start the Svelte dev server
        console.print("[blue]Starting development server... (Press Ctrl+C to stop)[/blue]")
        subprocess.run(["npm", "run", "dev", "--", "--host", host, "--port", str(port)], 
                      cwd=ui_dir, env=env)
        
    except KeyboardInterrupt:
        console.print("\n[yellow]UI server stopped by user[/yellow]")
    except FileNotFoundError:
        console.print("[red]Node.js/npm not found. Please install Node.js to run the UI.[/red]")
        console.print("[yellow]Visit: https://nodejs.org/[/yellow]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error starting UI: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def status(
    config_file: Optional[Path] = typer.Option(None, "--config", "-c", help="Configuration file path")
):
    """Check system status and health."""
    async def check_status():
        config = load_config(config_file)
        
        table = Table(title="AI MCP Toolkit Status")
        table.add_column("Component", style="cyan", no_wrap=True)
        table.add_column("Status", style="magenta")
        table.add_column("Details", style="green")
        
        # Check Ollama connection
        try:
            async with OllamaClient(config) as client:
                health = await client.health_check()
                if health:
                    models = await client.list_models()
                    table.add_row("Ollama", "✅ Connected", f"Models: {len(models)}")
                else:
                    table.add_row("Ollama", "❌ Disconnected", f"Check {config.get_ollama_url()}")
        except Exception as e:
            table.add_row("Ollama", "❌ Error", str(e))
        
        # Check MCP server
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://{config.host}:{config.port}/health") as response:
                    if response.status == 200:
                        table.add_row("MCP Server", "✅ Running", f"{config.host}:{config.port}")
                    else:
                        table.add_row("MCP Server", "❌ Error", f"Status: {response.status}")
        except Exception:
            table.add_row("MCP Server", "❌ Not Running", f"Start with: ai-mcp-toolkit serve")
        
        # Configuration info
        table.add_row("Config", "📋 Loaded", f"Model: {config.ollama_model}")
        
        console.print(table)
    
    asyncio.run(check_status())


@app.command()
def config(
    action: str = typer.Argument(..., help="Action: create, show, edit"),
    config_file: Optional[Path] = typer.Option(None, "--file", "-f", help="Configuration file path")
):
    """Manage configuration."""
    if action == "create":
        create_default_config()
        console.print("[green]Default configuration created![/green]")
        
    elif action == "show":
        config = load_config(config_file)
        
        table = Table(title="Current Configuration")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")
        
        config_dict = config.to_dict()
        for key, value in config_dict.items():
            table.add_row(key, str(value))
        
        console.print(table)
        
    elif action == "edit":
        config_path = config_file or Path("~/.ai-mcp-toolkit/config.yaml").expanduser()
        console.print(f"[yellow]Edit configuration file: {config_path}[/yellow]")
        console.print("Use your favorite text editor to modify the configuration.")
        
    else:
        console.print(f"[red]Unknown action: {action}[/red]")
        console.print("Available actions: create, show, edit")


@app.command()
def analyze(
    text: str = typer.Argument(..., help="Text to analyze"),
    output: str = typer.Option("table", "--output", "-o", help="Output format: table, json"),
    config_file: Optional[Path] = typer.Option(None, "--config", "-c", help="Configuration file path")
):
    """Analyze text using the text analyzer agent."""
    async def analyze_text():
        config = load_config(config_file)
        
        # Import and use the text analyzer
        from .agents.text_analyzer import TextAnalyzerAgent
        
        agent = TextAnalyzerAgent(config)
        result = await agent.execute_tool("analyze_text_basic", {"text": text})
        
        if output == "json":
            console.print(result)
        else:
            # Parse and display as table
            import json
            data = json.loads(result)
            
            table = Table(title="Text Analysis Results")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            
            for category, stats in data.items():
                if isinstance(stats, dict):
                    for key, value in stats.items():
                        table.add_row(f"{category.replace('_', ' ').title()}: {key.replace('_', ' ').title()}", str(value))
                else:
                    table.add_row(category.replace('_', ' ').title(), str(stats))
            
            console.print(table)
    
    asyncio.run(analyze_text())


@app.command()
def clean(
    text: str = typer.Argument(..., help="Text to clean"),
    config_file: Optional[Path] = typer.Option(None, "--config", "-c", help="Configuration file path")
):
    """Clean text using the text cleaner agent."""
    async def clean_text():
        config = load_config(config_file)
        
        from .agents.text_cleaner import TextCleanerAgent
        
        agent = TextCleanerAgent(config)
        result = await agent.execute_tool("clean_text", {"text": text})
        
        console.print(Panel(result, title="Cleaned Text", border_style="green"))
    
    asyncio.run(clean_text())


@app.command()
def remove_diacritics(
    text: str = typer.Argument(..., help="Text to process"),
    config_file: Optional[Path] = typer.Option(None, "--config", "-c", help="Configuration file path")
):
    """Remove diacritics from text."""
    async def remove_diacritics_text():
        config = load_config(config_file)
        
        from .agents.diacritic_remover import DiacriticRemoverAgent
        
        agent = DiacriticRemoverAgent(config)
        result = await agent.execute_tool("remove_diacritics", {"text": text})
        
        console.print(Panel(result, title="Text without Diacritics", border_style="green"))
    
    asyncio.run(remove_diacritics_text())


@app.command()
def anonymize(
    text: str = typer.Argument(..., help="Text to anonymize"),
    level: str = typer.Option("standard", "--level", "-l", help="Anonymization level: basic, standard, aggressive"),
    smart: bool = typer.Option(False, "--smart", help="Use AI-powered smart anonymization"),
    config_file: Optional[Path] = typer.Option(None, "--config", "-c", help="Configuration file path")
):
    """Anonymize sensitive information in text."""
    async def anonymize_text():
        config = load_config(config_file)
        
        from .agents.text_anonymizer import TextAnonymizerAgent
        
        agent = TextAnonymizerAgent(config)
        
        if smart:
            result = await agent.execute_tool("smart_anonymize", {"text": text})
        else:
            result = await agent.execute_tool("anonymize_text", {
                "text": text,
                "anonymization_level": level
            })
        
        console.print(Panel(result, title="Anonymized Text", border_style="yellow"))
    
    asyncio.run(anonymize_text())


@app.command()
def agents():
    """List all available agents and their tools."""
    async def list_agents():
        config = load_config()
        from .server.mcp_server import MCPServer
        server = MCPServer(config)
        
        table = Table(title="Available AI Agents")
        table.add_column("Agent", style="cyan", no_wrap=True)
        table.add_column("Description", style="green")
        table.add_column("Tools", style="magenta")
        
        stats = server.get_server_stats()
        
        for agent_name, agent_info in stats["agents"].items():
            tools = ", ".join(agent_info["tools"])
            table.add_row(
                agent_name.replace("_", " ").title(),
                agent_info["description"],
                tools
            )
        
        console.print(table)
        console.print(f"\n[bold]Total: {stats['agents_count']} agents, {stats['total_tools']} tools[/bold]")
    
    asyncio.run(list_agents())


@app.command()
def version():
    """Show version information."""
    from . import __version__
    
    rprint(f"[bold green]AI MCP Toolkit v{__version__}[/bold green]")
    rprint("A comprehensive AI-powered text processing toolkit")
    rprint("Built with ❤️  for the AI community")


def main():
    """Main entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
