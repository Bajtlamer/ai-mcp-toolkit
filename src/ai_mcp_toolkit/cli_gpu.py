"""GPU monitoring and optimization CLI commands for AI MCP Toolkit."""

import asyncio
import json
import time
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.live import Live
from rich.layout import Layout
from rich.text import Text

from .utils.config import Config
from .utils.gpu_monitor import get_gpu_monitor, check_gpu_health
from .models.ollama_client import quick_completion

console = Console()
app = typer.Typer(name="gpu", help="GPU monitoring and optimization commands")


@app.command("status")
def gpu_status():
    """Show current GPU status and health information."""
    async def _show_status():
        console.print("\n🔍 [bold blue]Checking GPU Status...[/bold blue]\n")
        
        with console.status("[bold green]Gathering GPU information..."):
            health_info = await check_gpu_health()
            gpu_monitor = get_gpu_monitor()
            await gpu_monitor.update_metrics()
            recommendations = await gpu_monitor.get_optimization_recommendations()
        
        # Create status table
        table = Table(title="🎯 GPU Status Report", show_header=True, header_style="bold magenta")
        table.add_column("Metric", style="cyan", no_wrap=True)
        table.add_column("Value", style="green")
        table.add_column("Status", justify="center")
        
        # Add GPU information
        table.add_row(
            "GPU Available", 
            "Yes" if health_info["gpu_available"] else "No",
            "✅" if health_info["gpu_available"] else "❌"
        )
        
        if health_info["gpu_available"]:
            table.add_row("GPU Name", health_info["gpu_name"] or "Unknown", "ℹ️")
            table.add_row(
                "GPU Utilization", 
                f"{health_info['gpu_utilization']}%",
                "🔥" if health_info['gpu_utilization'] > 80 else "⚡" if health_info['gpu_utilization'] > 30 else "💤"
            )
            table.add_row("GPU Memory", health_info["gpu_memory_usage"], "📊")
            
            if health_info["gpu_temperature"]:
                temp = health_info["gpu_temperature"]
                temp_status = "🌡️" if temp > 80 else "❄️" if temp < 40 else "🌡️"
                table.add_row("GPU Temperature", f"{temp}°C", temp_status)
        
        # Add Ollama information
        table.add_row(
            "Ollama GPU Accelerated",
            "Yes" if health_info["ollama_gpu_accelerated"] else "No",
            "✅" if health_info["ollama_gpu_accelerated"] else "⚠️"
        )
        
        if health_info["ollama_model"]:
            table.add_row("Active Model", health_info["ollama_model"], "🤖")
            table.add_row("Ollama Memory", health_info["ollama_memory_usage"], "💾")
        
        console.print(table)
        
        # Show recommendations
        if recommendations:
            console.print(f"\n💡 [bold yellow]Optimization Recommendations:[/bold yellow]\n")
            for i, rec in enumerate(recommendations, 1):
                console.print(f"{i}. {rec}")
        
        console.print()
    
    asyncio.run(_show_status())


@app.command("monitor")
def gpu_monitor(
    duration: int = typer.Option(30, "--duration", "-d", help="Monitoring duration in seconds"),
    interval: float = typer.Option(2.0, "--interval", "-i", help="Update interval in seconds")
):
    """Start real-time GPU monitoring."""
    async def _monitor():
        gpu_monitor = get_gpu_monitor()
        
        console.print(f"🎯 [bold green]Starting GPU monitoring for {duration} seconds...[/bold green]\n")
        console.print("Press Ctrl+C to stop early\n")
        
        # Create layout
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3)
        )
        
        start_time = time.time()
        
        try:
            with Live(layout, refresh_per_second=1/interval, screen=True):
                while time.time() - start_time < duration:
                    # Update metrics
                    await gpu_monitor.update_metrics()
                    current = gpu_monitor.current_metrics
                    
                    # Update header
                    elapsed = int(time.time() - start_time)
                    layout["header"].update(Panel(
                        f"🔥 [bold]GPU Monitor[/bold] - Elapsed: {elapsed}s / {duration}s",
                        style="bold blue"
                    ))
                    
                    # Create metrics table
                    table = Table(show_header=True, header_style="bold magenta")
                    table.add_column("Metric", style="cyan")
                    table.add_column("Current Value", style="green")
                    table.add_column("Trend", justify="center")
                    
                    table.add_row("GPU Utilization", f"{current.gpu_utilization:.1f}%", "📈")
                    table.add_row("GPU Memory Usage", f"{current.gpu_memory_usage:.1f}%", "💾")
                    table.add_row("Ollama Memory", f"{current.ollama_memory_usage} MB", "🧠")
                    table.add_row("Inference Speed", f"{current.inference_speed:.1f} tok/s", "⚡")
                    table.add_row("Total Requests", str(current.request_count), "📊")
                    table.add_row("Tokens Processed", str(current.total_tokens_processed), "🔤")
                    table.add_row("Avg Response Time", f"{current.average_response_time:.3f}s", "⏱️")
                    
                    layout["body"].update(table)
                    
                    # Update footer
                    layout["footer"].update(Panel(
                        "Use 'ai-mcp-toolkit gpu test' to run performance tests",
                        style="dim"
                    ))
                    
                    await asyncio.sleep(interval)
        
        except KeyboardInterrupt:
            console.print("\n\n⚠️ Monitoring stopped by user")
        
        console.print(f"\n✅ [bold green]Monitoring completed![/bold green]\n")
        
        # Show final summary
        summary = gpu_monitor.get_performance_summary()
        console.print("📊 [bold yellow]Final Performance Summary:[/bold yellow]")
        console.print(json.dumps(summary, indent=2))
    
    asyncio.run(_monitor())


@app.command("test")
def gpu_performance_test(
    iterations: int = typer.Option(5, "--iterations", "-n", help="Number of test iterations"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Model to test with")
):
    """Run GPU performance tests."""
    async def _test():
        config = Config()
        test_model = model or config.ollama_model
        
        console.print(f"\n🧪 [bold blue]Running GPU Performance Test[/bold blue]")
        console.print(f"Model: {test_model}")
        console.print(f"Iterations: {iterations}\n")
        
        gpu_monitor = get_gpu_monitor()
        results = []
        
        test_prompts = [
            "What is artificial intelligence?",
            "Explain machine learning in simple terms.",
            "Write a short story about a robot.",
            "Describe the benefits of GPU acceleration.",
            "What are the applications of natural language processing?"
        ]
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            for i in range(iterations):
                task = progress.add_task(f"Running test {i+1}/{iterations}...", total=1)
                
                prompt = test_prompts[i % len(test_prompts)]
                
                # Record initial metrics
                await gpu_monitor.update_metrics()
                initial_tokens = gpu_monitor.current_metrics.total_tokens_processed
                
                # Run inference
                start_time = time.time()
                result = await quick_completion(
                    prompt, 
                    system="Be concise and informative.",
                    config=config
                )
                duration = time.time() - start_time
                
                # Record final metrics
                await gpu_monitor.update_metrics()
                final_tokens = gpu_monitor.current_metrics.total_tokens_processed
                tokens_generated = final_tokens - initial_tokens
                
                results.append({
                    "iteration": i + 1,
                    "prompt": prompt,
                    "response_length": len(result),
                    "duration": duration,
                    "tokens_generated": tokens_generated,
                    "tokens_per_second": tokens_generated / duration if duration > 0 else 0
                })
                
                progress.update(task, completed=1)
                
                # Small delay between tests
                await asyncio.sleep(1)
        
        # Display results
        console.print("\n📊 [bold green]Performance Test Results:[/bold green]\n")
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Test", justify="center")
        table.add_column("Duration (s)", justify="right")
        table.add_column("Response Length", justify="right")
        table.add_column("Tokens Generated", justify="right")
        table.add_column("Speed (tok/s)", justify="right")
        
        total_duration = 0
        total_tokens = 0
        
        for result in results:
            table.add_row(
                str(result["iteration"]),
                f"{result['duration']:.2f}",
                str(result["response_length"]),
                str(result["tokens_generated"]),
                f"{result['tokens_per_second']:.1f}"
            )
            total_duration += result["duration"]
            total_tokens += result["tokens_generated"]
        
        console.print(table)
        
        # Summary statistics
        avg_duration = total_duration / iterations
        avg_speed = total_tokens / total_duration if total_duration > 0 else 0
        
        console.print(f"\n📈 [bold yellow]Summary Statistics:[/bold yellow]")
        console.print(f"• Average Duration: {avg_duration:.2f}s")
        console.print(f"• Average Speed: {avg_speed:.1f} tokens/second")
        console.print(f"• Total Tokens: {total_tokens}")
        console.print(f"• Total Duration: {total_duration:.2f}s")
        
        console.print(f"\n✅ [bold green]Performance test completed![/bold green]\n")
    
    asyncio.run(_test())


@app.command("benchmark")
def gpu_benchmark():
    """Run comprehensive GPU benchmark tests."""
    async def _benchmark():
        console.print("\n🏆 [bold blue]Running Comprehensive GPU Benchmark...[/bold blue]\n")
        
        gpu_monitor = get_gpu_monitor()
        
        # Test different model sizes if available
        models_to_test = ["llama3.1:8b", "llama3.2:3b"]
        benchmark_results = {}
        
        for model in models_to_test:
            console.print(f"🧪 Testing model: {model}")
            
            try:
                config = Config()
                config.ollama_model = model
                
                # Warm up
                console.print("  Warming up...")
                await quick_completion("Hello", config=config)
                
                # Benchmark test
                start_time = time.time()
                result = await quick_completion(
                    "Write a detailed explanation of neural networks, covering their structure, training process, and applications in modern AI systems.",
                    config=config
                )
                duration = time.time() - start_time
                
                await gpu_monitor.update_metrics()
                
                benchmark_results[model] = {
                    "duration": duration,
                    "response_length": len(result),
                    "words": len(result.split()),
                    "estimated_tokens": len(result) // 4,  # Rough estimation
                    "words_per_second": len(result.split()) / duration if duration > 0 else 0
                }
                
                console.print(f"  ✅ Completed in {duration:.2f}s")
                
            except Exception as e:
                console.print(f"  ❌ Failed: {e}")
                continue
        
        # Display benchmark results
        if benchmark_results:
            console.print("\n🏆 [bold green]Benchmark Results:[/bold green]\n")
            
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Model", style="cyan")
            table.add_column("Duration (s)", justify="right")
            table.add_column("Response Length", justify="right")
            table.add_column("Words", justify="right")
            table.add_column("Words/s", justify="right")
            table.add_column("Performance", justify="center")
            
            best_speed = max(r["words_per_second"] for r in benchmark_results.values())
            
            for model, result in benchmark_results.items():
                speed = result["words_per_second"]
                performance = "🥇" if speed == best_speed else "🥈" if speed > best_speed * 0.8 else "🥉"
                
                table.add_row(
                    model,
                    f"{result['duration']:.2f}",
                    str(result["response_length"]),
                    str(result["words"]),
                    f"{speed:.1f}",
                    performance
                )
            
            console.print(table)
        
        console.print(f"\n✅ [bold green]Benchmark completed![/bold green]\n")
    
    asyncio.run(_benchmark())


@app.command("report")
def gpu_report(
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file path")
):
    """Generate detailed GPU performance report."""
    async def _report():
        console.print("\n📄 [bold blue]Generating GPU Performance Report...[/bold blue]\n")
        
        gpu_monitor = get_gpu_monitor()
        
        with console.status("[bold green]Collecting GPU data..."):
            await gpu_monitor.update_metrics()
            
            if not output:
                timestamp = int(time.time())
                output_path = Path(f"gpu_report_{timestamp}.json")
            else:
                output_path = output
            
            await gpu_monitor.save_metrics_report(output_path)
        
        console.print(f"✅ [bold green]Report saved to: {output_path}[/bold green]")
        
        # Show summary
        health_info = await check_gpu_health()
        recommendations = await gpu_monitor.get_optimization_recommendations()
        
        console.print("\n📊 [bold yellow]Report Summary:[/bold yellow]")
        console.print(f"• GPU Available: {'Yes' if health_info['gpu_available'] else 'No'}")
        if health_info['gpu_available']:
            console.print(f"• GPU Name: {health_info['gpu_name']}")
            console.print(f"• GPU Utilization: {health_info['gpu_utilization']}%")
            console.print(f"• Ollama Accelerated: {'Yes' if health_info['ollama_gpu_accelerated'] else 'No'}")
        
        console.print(f"\n💡 [bold yellow]Recommendations: {len(recommendations)}[/bold yellow]")
        for i, rec in enumerate(recommendations[:3], 1):  # Show top 3
            console.print(f"{i}. {rec}")
        
        if len(recommendations) > 3:
            console.print(f"   ... and {len(recommendations) - 3} more in the full report")
        
        console.print()
    
    asyncio.run(_report())


if __name__ == "__main__":
    app()