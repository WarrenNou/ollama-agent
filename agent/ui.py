"""
Enhanced UI system for the Ollama CLI Agent.
Provides beautiful, modern, and interactive visual feedback.
"""

import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

from rich.console import Console, Group
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn
from rich.table import Table
from rich.layout import Layout
from rich.live import Live
from rich.text import Text
from rich.columns import Columns
from rich.align import Align
from rich.rule import Rule
from rich.status import Status
from rich.spinner import Spinner
from rich.box import ROUNDED, DOUBLE, SIMPLE
from rich.tree import Tree
from rich.markup import escape


class UITheme(Enum):
    """UI theme colors and styles."""
    PRIMARY = "bright_blue"
    SUCCESS = "bright_green"
    WARNING = "bright_yellow" 
    ERROR = "bright_red"
    INFO = "cyan"
    ACCENT = "magenta"
    MUTED = "dim white"
    BACKGROUND = "on grey11"


@dataclass
class AgentStats:
    """Agent execution statistics."""
    start_time: datetime
    current_step: int = 0
    max_steps: int = 50
    goals_completed: int = 0
    tools_used: int = 0
    errors_encountered: int = 0
    memory_entries: int = 0
    success_rate: float = 0.0
    current_tool: Optional[str] = None
    current_goal: Optional[str] = None


class EnhancedUI:
    """Enhanced UI system for beautiful CLI display."""
    
    def __init__(self, console: Console = None):
        self.console = console or Console()
        self.stats = AgentStats(start_time=datetime.now())
        self.live_display: Optional[Live] = None
        self.layout = Layout()
        self.progress: Optional[Progress] = None
        self.main_task_id: Optional[int] = None
        self.tool_history: List[Dict[str, Any]] = []
        self.status_messages: List[str] = []
        self.max_status_messages = 10
        
    def show_startup_banner(self, model: str, directory: str):
        """Display beautiful startup banner."""
        banner_text = f"""
[bold {UITheme.PRIMARY.value}]🤖 Ollama CLI Agent[/]
[{UITheme.MUTED.value}]Powered by AI • Enhanced with Intelligence[/]

[bold]Configuration:[/]
• Model: [{UITheme.INFO.value}]{model}[/]
• Directory: [{UITheme.MUTED.value}]{directory}[/]
• Started: [{UITheme.MUTED.value}]{datetime.now().strftime('%H:%M:%S')}[/]

[{UITheme.ACCENT.value}]Ready to execute your goals with precision and style![/]
        """
        
        panel = Panel(
            banner_text.strip(),
            title="🚀 Welcome",
            border_style=UITheme.PRIMARY.value,
            box=ROUNDED,
            padding=(1, 2)
        )
        
        self.console.print()
        self.console.print(panel)
        self.console.print()
    
    def show_goal_analysis(self, analysis: Dict[str, Any]):
        """Display goal analysis with visual indicators."""
        complexity = analysis.get('complexity_score', 0)
        estimated_steps = analysis.get('estimated_steps', 'Unknown')
        
        # Create complexity bar
        complexity_bar = "█" * min(int(complexity * 10), 10)
        complexity_color = UITheme.SUCCESS.value if complexity < 0.5 else UITheme.WARNING.value if complexity < 0.8 else UITheme.ERROR.value
        
        analysis_content = Group(
            Text(f"Complexity: [{complexity_color}]{complexity_bar}[/] ({complexity:.2f})", style="bold"),
            Text(f"Estimated Steps: {estimated_steps}", style=UITheme.INFO.value),
            Text("Recommendations:", style="bold underline"),
            *[Text(f"  • {rec}", style=UITheme.MUTED.value) for rec in analysis.get('recommendations', [])]
        )
        
        panel = Panel(
            analysis_content,
            title="🧠 Task Analysis",
            border_style=UITheme.INFO.value,
            box=SIMPLE
        )
        
        self.console.print(panel)
    
    def start_execution_display(self, goal: str, max_steps: int):
        """Start the live execution display."""
        self.stats.current_goal = goal
        self.stats.max_steps = max_steps
        
        # Create progress tracker
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=self.console,
            transient=False
        )
        
        self.main_task_id = self.progress.add_task(
            f"[{UITheme.PRIMARY.value}]Executing: {goal[:50]}...[/]",
            total=max_steps
        )
        
        # Setup layout
        self._setup_live_layout()
        
        # Start live display
        self.live_display = Live(
            self.layout,
            console=self.console,
            refresh_per_second=2,
            transient=False
        )
        self.live_display.start()
    
    def _setup_live_layout(self):
        """Setup the live display layout."""
        self.layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=8)
        )
        
        self.layout["main"].split_row(
            Layout(name="left", ratio=2),
            Layout(name="right", ratio=1)
        )
        
        self._update_layout()
    
    def _update_layout(self):
        """Update the live layout with current information."""
        # Header
        uptime = datetime.now() - self.stats.start_time
        uptime_str = str(uptime).split('.')[0]  # Remove microseconds
        
        header_text = Text.assemble(
            ("🤖 Agent Status: ", "bold"),
            ("RUNNING", f"bold {UITheme.SUCCESS.value}"),
            (" • Uptime: ", UITheme.MUTED.value),
            (uptime_str, UITheme.INFO.value),
            (" • Step: ", UITheme.MUTED.value),
            (f"{self.stats.current_step}/{self.stats.max_steps}", UITheme.ACCENT.value)
        )
        
        self.layout["header"].update(
            Panel(Align.center(header_text), box=SIMPLE, style=UITheme.BACKGROUND.value)
        )
        
        # Main content (progress)
        if self.progress:
            self.layout["left"].update(
                Panel(
                    self.progress,
                    title="Progress",
                    border_style=UITheme.PRIMARY.value
                )
            )
        
        # Stats panel
        stats_table = self._create_stats_table()
        self.layout["right"].update(
            Panel(
                stats_table,
                title="Statistics",
                border_style=UITheme.INFO.value
            )
        )
        
        # Footer (recent activity)
        activity_content = self._create_activity_display()
        self.layout["footer"].update(
            Panel(
                activity_content,
                title="Recent Activity",
                border_style=UITheme.ACCENT.value
            )
        )
    
    def _create_stats_table(self) -> Table:
        """Create statistics table."""
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Metric", style=UITheme.MUTED.value)
        table.add_column("Value", style="bold")
        
        table.add_row("Tools Used", str(self.stats.tools_used))
        table.add_row("Goals Completed", str(self.stats.goals_completed))
        table.add_row("Errors", str(self.stats.errors_encountered))
        table.add_row("Memory Entries", str(self.stats.memory_entries))
        table.add_row("Success Rate", f"{self.stats.success_rate:.1f}%")
        
        if self.stats.current_tool:
            table.add_row("Current Tool", self.stats.current_tool)
        
        return table
    
    def _create_activity_display(self) -> Group:
        """Create recent activity display."""
        if not self.status_messages:
            return Text("No recent activity", style=UITheme.MUTED.value)
        
        messages = []
        for msg in self.status_messages[-5:]:  # Show last 5 messages
            messages.append(Text(f"• {msg}", style="white"))
        
        return Group(*messages)
    
    def update_step(self, step: int, tool: str = None, thought: str = None):
        """Update current step information."""
        self.stats.current_step = step
        if tool:
            self.stats.current_tool = tool
            self.stats.tools_used += 1
        
        if self.progress and self.main_task_id is not None:
            self.progress.update(self.main_task_id, completed=step)
        
        # Add to activity
        if tool:
            timestamp = datetime.now().strftime('%H:%M:%S')
            self.status_messages.append(f"[{timestamp}] Executing: {tool}")
            if len(self.status_messages) > self.max_status_messages:
                self.status_messages.pop(0)
        
        if thought:
            self.add_status_message(f"💭 {thought[:80]}...")
        
        if self.live_display:
            self._update_layout()
    
    def add_status_message(self, message: str):
        """Add a status message to the activity feed."""
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.status_messages.append(f"[{timestamp}] {message}")
        if len(self.status_messages) > self.max_status_messages:
            self.status_messages.pop(0)
        
        if self.live_display:
            self._update_layout()
    
    def show_tool_execution(self, tool: str, args: Dict[str, Any], result: str):
        """Display tool execution with beautiful formatting."""
        self.tool_history.append({
            'tool': tool,
            'args': args,
            'result': result,
            'timestamp': datetime.now()
        })
        
        # Create tool display
        args_text = ", ".join([f"{k}={v}" for k, v in args.items()])
        
        tool_panel = Panel(
            Group(
                Text(f"🔧 {tool}", style=f"bold {UITheme.PRIMARY.value}"),
                Text(f"Args: {args_text}", style=UITheme.MUTED.value),
                Rule(style=UITheme.MUTED.value),
                Text("Result:", style="bold"),
                Text(result[:200] + "..." if len(result) > 200 else result, style=UITheme.SUCCESS.value)
            ),
            title=f"Tool Execution #{len(self.tool_history)}",
            border_style=UITheme.SUCCESS.value,
            box=SIMPLE
        )
        
        self.add_status_message(f"✅ {tool} completed")
        
        if not self.live_display:
            self.console.print(tool_panel)
    
    def show_error(self, error: str, suggestion: str = None):
        """Display error with optional suggestion."""
        self.stats.errors_encountered += 1
        
        error_content = Group(
            Text("❌ Error occurred:", style=f"bold {UITheme.ERROR.value}"),
            Text(error, style=UITheme.ERROR.value)
        )
        
        if suggestion:
            error_content.renderables.extend([
                Text(""),
                Text("💡 Suggestion:", style=f"bold {UITheme.INFO.value}"),
                Text(suggestion, style=UITheme.INFO.value)
            ])
        
        panel = Panel(
            error_content,
            title="Error",
            border_style=UITheme.ERROR.value,
            box=DOUBLE
        )
        
        self.add_status_message(f"❌ Error: {error[:50]}...")
        
        if not self.live_display:
            self.console.print(panel)
    
    def show_success(self, message: str, details: str = None):
        """Display success message."""
        self.stats.goals_completed += 1
        
        success_content = Group(
            Text("🎉 Success!", style=f"bold {UITheme.SUCCESS.value}"),
            Text(message, style=UITheme.SUCCESS.value)
        )
        
        if details:
            success_content.renderables.extend([
                Text(""),
                Text("Details:", style="bold"),
                Text(details, style=UITheme.MUTED.value)
            ])
        
        panel = Panel(
            success_content,
            title="Goal Achieved",
            border_style=UITheme.SUCCESS.value,
            box=DOUBLE
        )
        
        self.add_status_message(f"🎉 Goal completed: {message[:50]}...")
        
        if not self.live_display:
            self.console.print(panel)
    
    def show_thinking(self, thought: str):
        """Display agent's thinking process."""
        thinking_panel = Panel(
            Text(f"💭 {thought}", style=UITheme.ACCENT.value),
            title="Agent Thinking",
            border_style=UITheme.ACCENT.value,
            box=SIMPLE
        )
        
        if not self.live_display:
            self.console.print(thinking_panel)
    
    def show_confirmation_dialog(self, action: str, details: str = None) -> bool:
        """Show a beautiful confirmation dialog."""
        from rich.prompt import Confirm
        
        content = Group(
            Text(f"⚠️  About to execute: {action}", style=f"bold {UITheme.WARNING.value}"),
        )
        
        if details:
            content.renderables.append(Text(details, style=UITheme.MUTED.value))
        
        panel = Panel(
            content,
            title="Confirmation Required",
            border_style=UITheme.WARNING.value,
            box=DOUBLE
        )
        
        self.console.print(panel)
        return Confirm.ask("Do you want to proceed?", default=False)
    
    def show_tool_help(self, tools: Dict[str, str]):
        """Display available tools in a beautiful format."""
        table = Table(title="🛠️  Available Tools", box=ROUNDED)
        table.add_column("Tool", style=UITheme.PRIMARY.value, no_wrap=True)
        table.add_column("Description", style="white")
        table.add_column("Safety", style=UITheme.WARNING.value, justify="center")
        
        safety_indicators = {
            "execute_shell_command": "⚠️",
            "delete_file": "🚨",
            "move_file": "⚠️",
            "modify_file": "⚠️"
        }
        
        for tool_name, description in tools.items():
            safety = safety_indicators.get(tool_name, "✅")
            table.add_row(tool_name, description, safety)
        
        self.console.print(table)
    
    def show_memory_stats(self, stats: Dict[str, Any]):
        """Display memory statistics."""
        self.stats.memory_entries = stats.get('total_memories', 0)
        
        memory_table = Table(title="🧠 Memory Statistics", box=ROUNDED)
        memory_table.add_column("Category", style=UITheme.INFO.value)
        memory_table.add_column("Count", style="bold", justify="right")
        
        for category, count in stats.get('categories', {}).items():
            memory_table.add_row(category.title(), str(count))
        
        self.console.print(memory_table)
    
    def finish_execution(self, success: bool = True, message: str = None):
        """Finish the execution display."""
        if self.live_display:
            self.live_display.stop()
            self.live_display = None
        
        # Calculate final statistics
        duration = datetime.now() - self.stats.start_time
        self.stats.success_rate = (self.stats.goals_completed / max(1, self.stats.current_step)) * 100
        
        # Show final summary
        self._show_execution_summary(success, message, duration)
    
    def _show_execution_summary(self, success: bool, message: str, duration: timedelta):
        """Show execution summary."""
        status_text = "✅ COMPLETED" if success else "❌ FAILED"
        status_color = UITheme.SUCCESS.value if success else UITheme.ERROR.value
        
        summary_table = Table(show_header=False, box=None, padding=(0, 2))
        summary_table.add_column("Metric", style=UITheme.MUTED.value)
        summary_table.add_column("Value", style="bold")
        
        summary_table.add_row("Status", f"[{status_color}]{status_text}[/]")
        summary_table.add_row("Duration", str(duration).split('.')[0])
        summary_table.add_row("Steps Executed", f"{self.stats.current_step}/{self.stats.max_steps}")
        summary_table.add_row("Tools Used", str(self.stats.tools_used))
        summary_table.add_row("Success Rate", f"{self.stats.success_rate:.1f}%")
        
        if message:
            summary_table.add_row("Result", message)
        
        panel = Panel(
            summary_table,
            title="🏁 Execution Summary",
            border_style=status_color,
            box=DOUBLE
        )
        
        self.console.print()
        self.console.print(panel)
        self.console.print()
    
    def create_progress_spinner(self, description: str) -> Status:
        """Create a progress spinner for long operations."""
        return Status(
            f"[{UITheme.PRIMARY.value}]{description}[/]",
            spinner="dots",
            console=self.console
        )
    
    def show_interactive_prompt(self, prompt: str) -> str:
        """Show an enhanced interactive prompt."""
        from rich.prompt import Prompt
        
        prompt_panel = Panel(
            Text(prompt, style=f"bold {UITheme.PRIMARY.value}"),
            title="Input Required",
            border_style=UITheme.PRIMARY.value,
            box=SIMPLE
        )
        
        self.console.print(prompt_panel)
        return Prompt.ask("", default="")
    
    def clear_screen(self):
        """Clear the screen with style."""
        self.console.clear()
        
    def print_divider(self, text: str = None):
        """Print a stylized divider."""
        if text:
            self.console.rule(f"[{UITheme.ACCENT.value}]{text}[/]", style=UITheme.MUTED.value)
        else:
            self.console.rule(style=UITheme.MUTED.value)


# Global UI instance
ui = EnhancedUI()
