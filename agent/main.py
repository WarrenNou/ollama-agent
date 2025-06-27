from .agent import Agent
import click
import sys
import os
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.markdown import Markdown


def show_welcome():
    """Display welcome message and instructions."""
    console = Console()
    
    welcome_text = """
# 🤖 Ollama CLI Agent

Welcome to the Ollama CLI Agent! This AI agent can help you execute various tasks through natural language commands.

## Available Capabilities:
- **File Operations**: Read, write, copy, move, delete files and directories
- **Shell Commands**: Execute system commands safely with confirmations
- **File Search**: Find files by name or search content within files
- **Directory Navigation**: List, navigate, and manage directories
- **Content Analysis**: Analyze file contents and structures

## Safety Features:
- Interactive confirmations for destructive operations
- Dangerous command detection and warnings
- File diff previews before modifications
- Step-by-step execution with user control

## Examples:
- "Create a Python script that prints hello world"
- "Find all .py files in this directory"
- "Search for TODO comments in my code"
- "Backup all my config files to a backup directory"
- "Analyze the structure of this project"

Support the project by starring the repository on GitHub and sharing it with your friends https://github.com/WarrenNou!
    """
    
    console.print(Panel(Markdown(welcome_text), title="🚀 Getting Started", border_style="blue"))


def check_ollama_connection(model: str, console: Console) -> bool:
    """Check if Ollama is running and the model is available."""
    import requests
    
    try:
        # Check if Ollama is running
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        response.raise_for_status()
        
        # Check if the model is available
        data = response.json()
        available_models = [m["name"] for m in data.get("models", [])]
        
        if model not in available_models:
            console.print(f"[yellow]⚠️  Model '{model}' not found.[/]")
            console.print(f"[cyan]Available models:[/] {', '.join(available_models)}")
            return False
        
        return True
        
    except requests.exceptions.ConnectionError:
        console.print("[red]❌ Cannot connect to Ollama. Make sure Ollama is running.[/]")
        console.print("[cyan]Start Ollama with:[/] ollama serve")
        return False
    except requests.exceptions.RequestException as e:
        console.print(f"[red]❌ Error connecting to Ollama: {e}[/]")
        return False


def check_and_setup_ollama(console: Console) -> bool:
    """Check if Ollama is properly set up, and run setup if needed."""
    import subprocess
    import sys
    
    # Check if Ollama is installed
    try:
        result = subprocess.run(["ollama", "--version"], capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            raise FileNotFoundError("Ollama not found")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        console.print("[yellow]⚠️  Ollama not found. Running automatic setup...[/]")
        
        try:
            # Try automatic setup first
            from .setup import automatic_setup
            if automatic_setup():
                console.print("[green]✅ Ollama setup completed automatically![/]")
                return True
        except:
            pass
        
        # If automatic setup fails, ask user
        if not Confirm.ask("Automatic setup failed. Would you like to run the interactive setup?", default=True):
            console.print("[red]❌ Ollama is required. You can install it manually from: https://ollama.ai/[/]")
            console.print("[cyan]Or run: ollama-agent-setup[/]")
            return False
        
        try:
            # Run the interactive setup script
            from .setup import main as setup_main
            if setup_main():
                console.print("[green]✅ Ollama setup completed successfully![/]")
                return True
            else:
                console.print("[red]❌ Setup failed. Please install manually or run: ollama-agent-setup[/]")
                return False
        except Exception as e:
            console.print(f"[red]❌ Setup failed: {e}[/]")
            console.print("[cyan]You can run setup manually with: ollama-agent-setup[/]")
            return False
    
    # Check if Ollama service is running
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            return True
    except ImportError:
        console.print("[yellow]⚠️  requests library not available for service check[/]")
    except:
        pass
    
    # Try to start Ollama service
    console.print("[yellow]⚠️  Ollama service not running. Attempting to start...[/]")
    try:
        subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        import time
        time.sleep(3)  # Wait for service to start
        
        # Check again
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                console.print("[green]✅ Ollama service started successfully![/]")
                return True
        except ImportError:
            # If requests isn't available, assume it started
            console.print("[green]✅ Ollama service started (unable to verify)[/]")
            return True
        except:
            pass
    except:
        pass
    
    console.print("[red]❌ Could not start Ollama service automatically.[/]")
    console.print("[cyan]Please run: ollama serve[/]")
    console.print("[cyan]Or run the setup again: ollama-agent-setup[/]")
    return False


@click.command()
@click.argument("goal", required=False)
@click.option("-m", "--model", default="llama3:latest", show_default=True, help="Ollama model to use.")
@click.option("-n", "--max-steps", default=50, show_default=True, type=int, help="Maximum number of reasoning steps.")
@click.option("--adaptive-steps/--no-adaptive-steps", default=True, help="Enable adaptive step calculation based on task complexity.")
@click.option("--timeout", default=None, type=int, help="Per-request timeout in seconds.")
@click.option("-v", "--verbose", is_flag=True, help="Verbose mode: dump prompts and raw responses.")
@click.option("-s", "--stream", is_flag=True, help="Stream tokens from the model in real time.")
@click.option("-i", "--interactive", is_flag=True, help="Interactive mode: continue with new goals after completion.")
@click.option("--infinite", is_flag=True, help="Infinite mode: run continuously with self-monitoring and testing.")
@click.option("--test", is_flag=True, help="Run comprehensive tests and exit.")
@click.option("--monitor", is_flag=True, help="Run continuous health monitoring.")
@click.option("--no-confirm", is_flag=True, help="Skip confirmations for operations (use with caution).")
@click.option("--show-tools", is_flag=True, help="Show available tools and exit.")
def main(goal, model, max_steps, adaptive_steps, timeout, verbose, stream, interactive, infinite, test, monitor, no_confirm, show_tools):
    """🤖 Ollama CLI Agent - An AI agent that executes tasks through natural language.
    
    GOAL: Optional goal to execute immediately. If not provided, you'll be prompted.
    """
    console = Console()
    
    # Show available tools and exit
    if show_tools:
        show_available_tools(console)
        return
    
    # Show welcome message if no goal provided
    if not goal:
        show_welcome()
    
    # Check and setup Ollama
    if not check_and_setup_ollama(console):
        sys.exit(1)
    
    # Check Ollama connection
    if not check_ollama_connection(model, console):
        sys.exit(1)
    
    console.print(f"[bold cyan]🤖 Using model:[/] {model}")
    console.print(f"[dim]Current directory:[/] {os.getcwd()}")
    
    # Create agent
    agent = Agent(
        model=model,
        max_steps=max_steps,
        timeout=timeout,
        verbose=verbose,
        stream=stream,
        console=console,
        adaptive_steps=adaptive_steps,
        no_confirm=no_confirm,
    )
    
    # Show warning if no-confirm mode is enabled
    if no_confirm:
        console.print("[yellow]⚠️  Running in no-confirmation mode![/]")
    
    try:
        if test:
            # Run comprehensive tests and exit
            from .testing import AgentTester
            tester = AgentTester(console)
            console.print("[bold cyan]🧪 Running comprehensive agent tests...[/]")
            report = tester.run_comprehensive_tests(agent)
            
            if report["success_rate"] >= 80:
                console.print("[bold green]✅ All tests passed! Agent is ready for use.[/]")
                sys.exit(0)
            else:
                console.print(f"[bold red]❌ Some tests failed ({report['success_rate']:.1f}% success rate)[/]")
                sys.exit(1)
        
        elif monitor:
            # Run continuous health monitoring
            from .testing import AgentTester
            tester = AgentTester(console)
            tester.run_continuous_monitoring(agent)
        
        elif infinite:
            # Infinite mode with self-monitoring and testing
            from .infinite_runner import InfiniteRunner
            runner = InfiniteRunner(agent, console)
            runner.start_infinite_mode(goal)
        
        elif interactive:
            # Interactive mode - keep asking for new goals
            console.print("[bold green]🔄 Interactive mode enabled. Type 'exit' or 'quit' to stop.[/]")
            
            while True:
                if not goal:
                    goal = console.input("\n[bold green]What is your goal? [/]")
                
                if goal.lower() in ['exit', 'quit', 'q']:
                    console.print("[cyan]👋 Goodbye![/]")
                    break
                
                if goal.strip():
                    console.print(f"\n[bold blue]🎯 Goal:[/] {goal}")
                    agent.execute(goal)
                    
                    if not Confirm.ask("\n[bold green]Continue with another task?[/]", default=True):
                        console.print("[cyan]👋 Goodbye![/]")
                        break
                
                goal = None  # Reset for next iteration
        else:
            # Single execution mode
            if not goal:
                goal = console.input("[bold green]What is your goal? [/]")
            
            if goal.strip():
                console.print(f"\n[bold blue]🎯 Goal:[/] {goal}")
                agent.execute(goal)
            else:
                console.print("[yellow]No goal provided.[/]")
                
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  Interrupted by user.[/]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]❌ Unexpected error: {e}[/]")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        sys.exit(1)


def show_available_tools(console: Console):
    """Display all available tools in a formatted table."""
    from .tools import TOOLS
    
    table = Table(title="🛠️  Available Tools")
    table.add_column("Tool", style="cyan")
    table.add_column("Description", style="white")
    table.add_column("Safety", style="yellow")
    
    tool_info = {
        "execute_shell_command": ("Execute shell commands", "⚠️  Requires confirmation"),
        "search_file": ("Read file contents", "✅ Safe"),
        "modify_file": ("Write/modify files", "⚠️  Shows diff, requires confirmation"),
        "list_directory": ("List directory contents", "✅ Safe"),
        "find_files": ("Find files by pattern", "✅ Safe"),
        "get_file_info": ("Get file metadata", "✅ Safe"),
        "create_directory": ("Create directories", "✅ Safe"),
        "copy_file": ("Copy files", "✅ Safe"),
        "move_file": ("Move/rename files", "⚠️  Requires confirmation"),
        "delete_file": ("Delete files/directories", "🚨 Requires confirmation"),
        "search_in_files": ("Search text in files", "✅ Safe"),
        "get_current_directory": ("Get current directory", "✅ Safe"),
        "change_directory": ("Change directory", "✅ Safe"),
    }
    
    for tool_name in TOOLS.keys():
        if tool_name in tool_info:
            desc, safety = tool_info[tool_name]
            table.add_row(tool_name, desc, safety)
    
    console.print(table)
    console.print("\n[dim]Use --help for more CLI options[/]")


if __name__ == "__main__":
    main()
