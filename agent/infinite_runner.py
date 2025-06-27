"""
Infinite runner system for the Ollama agent.
Provides continuous operation, self-monitoring, and adaptive learning.
"""

import time
import threading
import signal
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json
import os

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
from rich.prompt import Prompt, Confirm

from .agent import Agent
from .memory import MemoryManager
from .testing import AgentTester


class InfiniteRunner:
    """Manages infinite operation of the agent with self-monitoring."""
    
    def __init__(self, agent: Agent, console: Console = None):
        self.agent = agent
        self.console = console or Console()
        self.tester = AgentTester(self.console)
        self.running = False
        self.stats = {
            "start_time": None,
            "goals_completed": 0,
            "errors_encountered": 0,
            "self_tests_passed": 0,
            "self_tests_failed": 0,
            "uptime": 0,
            "last_health_check": None,
            "performance_score": 100.0
        }
        self.task_queue = []
        self.monitoring_thread = None
        self.auto_tasks = [
            "Analyze the current directory structure and identify areas for improvement",
            "Check for any configuration files that might need optimization",
            "Look for any TODO comments or unfinished work in code files",
            "Verify all tools are working correctly by running a quick test",
            "Clean up any temporary files or organize the workspace",
            "Generate a summary of recent activities and suggest next steps"
        ]
        self.current_task_index = 0
        
    def start_infinite_mode(self, initial_goal: str = None):
        """Start the infinite running mode."""
        self.console.print(Panel(
            "🚀 Starting Infinite Agent Mode\n\n"
            "The agent will continuously:\n"
            "• Process queued tasks\n"
            "• Monitor its own health\n"
            "• Learn from experiences\n"
            "• Suggest and execute improvements\n"
            "• Run self-tests periodically\n\n"
            "Press Ctrl+C to stop gracefully",
            title="🤖 Infinite Mode Activated",
            border_style="green"
        ))
        
        self.running = True
        self.stats["start_time"] = datetime.now()
        
        # Set up signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        
        # Add initial goal if provided
        if initial_goal:
            self.task_queue.append({
                "goal": initial_goal,
                "priority": "high",
                "type": "user",
                "added_at": datetime.now().isoformat()
            })
        
        # Start monitoring thread
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        # Run comprehensive initial tests
        self._run_initial_tests()
        
        # Main execution loop
        self._main_loop()
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        self.console.print("\n[yellow]🛑 Shutdown signal received. Stopping gracefully...[/]")
        self.running = False
    
    def _run_initial_tests(self):
        """Run comprehensive tests before starting infinite mode."""
        self.console.print("[cyan]🧪 Running initial comprehensive tests...[/]")
        
        report = self.tester.run_comprehensive_tests(self.agent)
        
        if report["success_rate"] >= 80:
            self.console.print("[green]✅ Initial tests passed. Agent is ready for infinite mode.[/]")
            self.stats["self_tests_passed"] += 1
        else:
            self.console.print(f"[yellow]⚠️  Some tests failed ({report['success_rate']:.1f}% success rate)[/]")
            self.stats["self_tests_failed"] += 1
            
            if report["success_rate"] < 50:
                self.console.print("[red]❌ Critical failures detected. Consider fixing issues before infinite mode.[/]")
                if not Confirm.ask("Continue anyway?", default=False):
                    return
        
        # Store test results in memory (convert any non-serializable objects)
        serializable_report = self._make_serializable(report)
        self.agent.memory.store_memory(
            "system_test",
            {"test_report": serializable_report, "test_type": "initial_comprehensive"},
            importance=0.9,
            tags=["testing", "health_check"],
            success=report["success_rate"] >= 80
        )
    
    def _main_loop(self):
        """Main execution loop for infinite mode."""
        last_auto_task = datetime.now()
        last_self_test = datetime.now()
        
        while self.running:
            try:
                # Update uptime
                if self.stats["start_time"]:
                    self.stats["uptime"] = (datetime.now() - self.stats["start_time"]).total_seconds()
                
                # Process queued tasks
                if self.task_queue:
                    self._process_next_task()
                else:
                    # Add automatic tasks if queue is empty
                    if datetime.now() - last_auto_task > timedelta(minutes=10):
                        self._add_automatic_task()
                        last_auto_task = datetime.now()
                
                # Run periodic self-tests
                if datetime.now() - last_self_test > timedelta(minutes=30):
                    self._run_periodic_self_test()
                    last_self_test = datetime.now()
                
                # Brief pause to prevent excessive CPU usage
                time.sleep(5)
                
            except Exception as e:
                self.console.print(f"[red]❌ Error in main loop: {e}[/]")
                self.stats["errors_encountered"] += 1
                self.agent.memory.learn_from_error(
                    "main_loop_error", 
                    str(e), 
                    "Continue execution with error logging",
                    0.5
                )
                time.sleep(10)  # Longer pause after error
        
        self._shutdown_gracefully()
    
    def _process_next_task(self):
        """Process the next task in the queue."""
        if not self.task_queue:
            return
        
        task = self.task_queue.pop(0)
        
        self.console.print(Panel(
            f"🎯 Processing Task:\n{task['goal']}\n\n"
            f"Priority: {task['priority']}\n"
            f"Type: {task['type']}\n"
            f"Added: {task['added_at']}",
            title="Current Task",
            border_style="blue"
        ))
        
        try:
            # Execute the task
            start_time = datetime.now()
            self.agent.execute(task["goal"])
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Record successful completion
            self.stats["goals_completed"] += 1
            self.agent.memory.store_memory(
                "task_completion",
                {
                    "goal": task["goal"],
                    "execution_time": execution_time,
                    "priority": task["priority"],
                    "type": task["type"]
                },
                importance=0.7,
                tags=["task", "completion"],
                success=True
            )
            
            self.console.print("[green]✅ Task completed successfully![/]")
            
        except Exception as e:
            self.console.print(f"[red]❌ Task failed: {e}[/]")
            self.stats["errors_encountered"] += 1
            self.agent.memory.learn_from_error(
                "task_execution_error",
                f"Goal: {task['goal']}, Error: {str(e)}",
                "Review task requirements and try alternative approach",
                0.3
            )
    
    def _add_automatic_task(self):
        """Add an automatic maintenance task."""
        if self.current_task_index >= len(self.auto_tasks):
            self.current_task_index = 0
        
        task_goal = self.auto_tasks[self.current_task_index]
        self.current_task_index += 1
        
        # Enhance task with current context
        memory_stats = self.agent.memory.get_memory_stats()
        enhanced_goal = f"{task_goal}\n\nCurrent context:\n"
        enhanced_goal += f"- {memory_stats['total_memories']} memories stored\n"
        enhanced_goal += f"- {self.stats['goals_completed']} goals completed\n"
        enhanced_goal += f"- Uptime: {self.stats['uptime']//60:.0f} minutes"
        
        self.task_queue.append({
            "goal": enhanced_goal,
            "priority": "low",
            "type": "automatic",
            "added_at": datetime.now().isoformat()
        })
        
        self.console.print(f"[cyan]🔄 Added automatic task: {task_goal[:50]}...[/]")
    
    def _run_periodic_self_test(self):
        """Run periodic self-tests to ensure health."""
        self.console.print("[cyan]🔍 Running periodic health check...[/]")
        
        healthy, issues = self.tester.validate_agent_health(self.agent)
        
        if healthy:
            self.console.print("[green]✅ Health check passed[/]")
            self.stats["self_tests_passed"] += 1
            self.stats["last_health_check"] = datetime.now().isoformat()
        else:
            self.console.print("[red]❌ Health issues detected:[/]")
            for issue in issues:
                self.console.print(f"  • {issue}")
            self.stats["self_tests_failed"] += 1
            
            # Try to auto-fix common issues
            self._attempt_auto_fix(issues)
        
        # Update performance score
        success_rate = (self.stats["self_tests_passed"] / 
                       max(1, self.stats["self_tests_passed"] + self.stats["self_tests_failed"]))
        self.stats["performance_score"] = success_rate * 100
    
    def _attempt_auto_fix(self, issues: List[str]):
        """Attempt to automatically fix common issues."""
        for issue in issues:
            if "memory" in issue.lower():
                try:
                    # Try to reinitialize memory system
                    self.agent.memory = MemoryManager()
                    self.console.print("[yellow]🔧 Attempted memory system reset[/]")
                except Exception as e:
                    self.console.print(f"[red]❌ Auto-fix failed: {e}[/]")
            
            elif "tool" in issue.lower():
                try:
                    # Try to reload tools
                    from . import tools
                    self.console.print("[yellow]🔧 Attempted tool system reload[/]")
                except Exception as e:
                    self.console.print(f"[red]❌ Auto-fix failed: {e}[/]")
    
    def _monitoring_loop(self):
        """Background monitoring loop."""
        while self.running:
            try:
                # Clean up old memories periodically
                if self.stats["uptime"] % 3600 == 0:  # Every hour
                    self.agent.memory.cleanup_old_memories(days=7)
                    self.console.print("[cyan]🧹 Cleaned up old memories[/]")
                
                # Display live stats
                self._update_live_display()
                
                time.sleep(30)  # Update every 30 seconds
                
            except Exception as e:
                self.console.print(f"[red]Monitoring error: {e}[/]")
                time.sleep(60)
    
    def _update_live_display(self):
        """Update the live status display."""
        stats_table = Table(title="🤖 Agent Status")
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Value", style="white")
        
        uptime_str = f"{self.stats['uptime']//3600:.0f}h {(self.stats['uptime']%3600)//60:.0f}m"
        
        stats_table.add_row("Status", "[green]Running[/]" if self.running else "[red]Stopped[/]")
        stats_table.add_row("Uptime", uptime_str)
        stats_table.add_row("Goals Completed", str(self.stats["goals_completed"]))
        stats_table.add_row("Tasks in Queue", str(len(self.task_queue)))
        stats_table.add_row("Errors", str(self.stats["errors_encountered"]))
        stats_table.add_row("Performance Score", f"{self.stats['performance_score']:.1f}%")
        
        memory_stats = self.agent.memory.get_memory_stats()
        stats_table.add_row("Total Memories", str(memory_stats["total_memories"]))
        stats_table.add_row("Working Memory", str(memory_stats["working_memory_size"]))
        
        # Only print occasionally to avoid spam
        if int(self.stats["uptime"]) % 60 == 0:  # Every minute
            self.console.print(stats_table)
    
    def add_task(self, goal: str, priority: str = "medium"):
        """Add a new task to the queue."""
        self.task_queue.append({
            "goal": goal,
            "priority": priority,
            "type": "user",
            "added_at": datetime.now().isoformat()
        })
        self.console.print(f"[green]✅ Added task: {goal[:50]}...[/]")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of the infinite runner."""
        return {
            **self.stats,
            "running": self.running,
            "queue_size": len(self.task_queue),
            "memory_stats": self.agent.memory.get_memory_stats()
        }
    
    def _shutdown_gracefully(self):
        """Perform graceful shutdown."""
        self.console.print("[yellow]🛑 Shutting down infinite mode...[/]")
        
        # Save final state
        final_report = {
            "session_stats": self.stats,
            "final_memory_stats": self.agent.memory.get_memory_stats(),
            "shutdown_time": datetime.now().isoformat()
        }
        
        # Store session summary in memory
        self.agent.memory.store_memory(
            "session_summary",
            final_report,
            importance=0.9,
            tags=["session", "summary", "infinite_mode"],
            success=True
        )
        
        self.console.print(Panel(
            f"📊 Session Summary\n\n"
            f"Uptime: {self.stats['uptime']//3600:.0f}h {(self.stats['uptime']%3600)//60:.0f}m\n"
            f"Goals Completed: {self.stats['goals_completed']}\n"
            f"Errors Encountered: {self.stats['errors_encountered']}\n"
            f"Performance Score: {self.stats['performance_score']:.1f}%\n"
            f"Final Memory Count: {self.agent.memory.get_memory_stats()['total_memories']}",
            title="🏁 Session Complete",
            border_style="green"
        ))
        
        self.console.print("[cyan]👋 Goodbye! The agent has been shut down gracefully.[/]")
    
    def _make_serializable(self, obj: Any) -> Any:
        """Convert objects to JSON-serializable format."""
        if hasattr(obj, 'to_dict'):
            return obj.to_dict()
        elif isinstance(obj, list):
            return [self._make_serializable(item) for item in obj]
        elif isinstance(obj, dict):
            return {key: self._make_serializable(value) for key, value in obj.items()}
        elif hasattr(obj, '__dict__'):
            # Handle objects with __dict__ by converting to dict
            return {key: self._make_serializable(value) for key, value in obj.__dict__.items()}
        else:
            # Return as-is for basic types (str, int, float, bool, None)
            return obj
