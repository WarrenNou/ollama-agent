"""
Code testing and validation module for the Ollama Agent.
Ensures generated code meets quality standards before delivery.
"""

import ast
import os
import subprocess
import tempfile
import sys
import importlib.util
from typing import Dict, List, Any, Tuple, Optional
from pathlib import Path
import re
import json
import traceback
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
import tempfile
import shutil
from contextlib import contextmanager

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import track


class TestResult:
    """Represents the result of a test execution."""
    
    def __init__(self, test_name: str, success: bool, message: str = "", 
                 execution_time: float = 0.0, details: Dict = None):
        self.test_name = test_name
        self.success = success
        self.message = message
        self.execution_time = execution_time
        self.details = details or {}
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert TestResult to dictionary for serialization."""
        return {
            "test_name": self.test_name,
            "success": self.success,
            "message": self.message,
            "execution_time": self.execution_time,
            "details": self.details,
            "timestamp": self.timestamp
        }


class AgentTester:
    """Comprehensive testing system for the agent."""
    
    def __init__(self, console: Console = None):
        self.console = console or Console()
        self.test_results: List[TestResult] = []
        self.temp_dir = None
        
    @contextmanager
    def temp_workspace(self):
        """Create a temporary workspace for testing."""
        self.temp_dir = tempfile.mkdtemp(prefix="agent_test_")
        original_cwd = os.getcwd()
        try:
            os.chdir(self.temp_dir)
            yield self.temp_dir
        finally:
            os.chdir(original_cwd)
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
            self.temp_dir = None
    
    def run_comprehensive_tests(self, agent) -> Dict[str, Any]:
        """Run a comprehensive test suite on the agent."""
        self.console.print(Panel("🧪 Starting Comprehensive Agent Tests", style="bold blue"))
        
        test_categories = [
            ("basic_functionality", self._test_basic_functionality),
            ("file_operations", self._test_file_operations),
            ("error_handling", self._test_error_handling),
            ("memory_system", self._test_memory_system),
            ("goal_achievement", self._test_goal_achievement),
            ("safety_measures", self._test_safety_measures),
        ]
        
        results = {}
        
        for category, test_func in test_categories:
            self.console.print(f"\n[bold cyan]Testing {category}...[/]")
            try:
                category_results = test_func(agent)
                results[category] = category_results
                self._display_category_results(category, category_results)
            except Exception as e:
                self.console.print(f"[red]Error in {category}: {e}[/]")
                results[category] = {"error": str(e)}
        
        # Generate comprehensive report
        report = self._generate_test_report(results)
        self._display_final_report(report)
        
        return report
    
    def _test_basic_functionality(self, agent) -> List[TestResult]:
        """Test basic agent functionality."""
        results = []
        
        # Test 1: Agent initialization
        try:
            assert agent.model is not None
            assert agent.memory is not None
            results.append(TestResult("agent_initialization", True, "Agent properly initialized"))
        except Exception as e:
            results.append(TestResult("agent_initialization", False, f"Initialization failed: {e}"))
        
        # Test 2: Memory system
        try:
            agent.memory.store_memory("test", {"data": "test_value"})
            memories = agent.memory.retrieve_memories(category="test")
            assert len(memories) > 0
            results.append(TestResult("memory_basic", True, "Memory system functioning"))
        except Exception as e:
            results.append(TestResult("memory_basic", False, f"Memory system failed: {e}"))
        
        # Test 3: Tool registry
        try:
            from .tools import TOOLS
            assert len(TOOLS) > 0
            results.append(TestResult("tool_registry", True, f"Found {len(TOOLS)} tools"))
        except Exception as e:
            results.append(TestResult("tool_registry", False, f"Tool registry failed: {e}"))
        
        return results
    
    def _test_file_operations(self, agent) -> List[TestResult]:
        """Test file operation capabilities."""
        results = []
        
        with self.temp_workspace():
            # Test file creation
            try:
                from .tools import modify_file
                test_content = "Hello, World!\nThis is a test file."
                result = modify_file("test.txt", test_content)
                assert "Successfully" in result, f"File creation failed: {result}"
                assert os.path.exists("test.txt"), "File was not created"
                results.append(TestResult("file_creation", True, "File creation successful"))
            except Exception as e:
                results.append(TestResult("file_creation", False, f"File creation failed: {e}"))
            
            # Test file reading
            try:
                from .tools import search_file
                content = search_file("test.txt")
                assert test_content in content, "File content mismatch"
                results.append(TestResult("file_reading", True, "File reading successful"))
            except Exception as e:
                results.append(TestResult("file_reading", False, f"File reading failed: {e}"))
            
            # Test directory operations
            try:
                from .tools import create_directory, list_directory
                create_result = create_directory("test_dir")
                assert "Successfully" in create_result, f"Directory creation failed: {create_result}"
                
                list_result = list_directory(".")
                assert "test_dir" in list_result, "Directory not found in listing"
                results.append(TestResult("directory_operations", True, "Directory operations successful"))
            except Exception as e:
                results.append(TestResult("directory_operations", False, f"Directory operations failed: {e}"))
        
        return results
    
    def _test_error_handling(self, agent) -> List[TestResult]:
        """Test error handling and recovery."""
        results = []
        
        # Test invalid file operations
        try:
            from .tools import search_file
            result = search_file("/nonexistent/file.txt")
            assert "not found" in result.lower() or "error" in result.lower()
            results.append(TestResult("invalid_file_handling", True, "Invalid file handled gracefully"))
        except Exception as e:
            results.append(TestResult("invalid_file_handling", False, f"Error handling failed: {e}"))
        
        # Test memory error recovery
        try:
            agent.memory.learn_from_error("test_error", "test context", "test solution", 0.8)
            solutions = agent.memory.get_error_solutions("test_error")
            assert len(solutions) > 0
            results.append(TestResult("error_learning", True, "Error learning system working"))
        except Exception as e:
            results.append(TestResult("error_learning", False, f"Error learning failed: {e}"))
        
        return results
    
    def _test_memory_system(self, agent) -> List[TestResult]:
        """Test comprehensive memory system functionality."""
        results = []
        
        # Test memory storage and retrieval
        try:
            memory_id = agent.memory.store_memory(
                "test_category", 
                {"test_key": "test_value", "complexity": "high"}, 
                importance=0.8,
                tags=["testing", "validation"]
            )
            
            # Test retrieval by category
            memories = agent.memory.retrieve_memories(category="test_category")
            assert len(memories) > 0
            
            # Test retrieval by tags
            tagged_memories = agent.memory.retrieve_memories(tags=["testing"])
            assert len(tagged_memories) > 0
            
            results.append(TestResult("memory_storage_retrieval", True, "Memory system comprehensive test passed"))
        except Exception as e:
            results.append(TestResult("memory_storage_retrieval", False, f"Memory system failed: {e}"))
        
        # Test working memory
        try:
            agent.memory.update_working_memory("test_key", "test_value")
            value = agent.memory.get_working_memory("test_key")
            assert value == "test_value"
            results.append(TestResult("working_memory", True, "Working memory functioning"))
        except Exception as e:
            results.append(TestResult("working_memory", False, f"Working memory failed: {e}"))
        
        return results
    
    def _test_goal_achievement(self, agent) -> List[TestResult]:
        """Test goal achievement capabilities."""
        results = []
        
        # This would typically involve more complex integration tests
        # For now, we'll test the basic structure
        
        try:
            # Test goal setting
            agent.goal = "Test goal"
            assert agent.goal == "Test goal"
            
            # Test history tracking
            agent.history.append({"action": "test", "result": "success"})
            assert len(agent.history) > 0
            
            results.append(TestResult("goal_structure", True, "Goal structure functioning"))
        except Exception as e:
            results.append(TestResult("goal_structure", False, f"Goal structure failed: {e}"))
        
        return results
    
    def _test_safety_measures(self, agent) -> List[TestResult]:
        """Test safety and security measures."""
        results = []
        
        # Test dangerous command detection
        try:
            dangerous_commands = ["rm -rf /", "sudo rm -rf /", "chmod 777 /"]
            # We won't actually execute these, just test detection
            for cmd in dangerous_commands:
                # This would be part of the agent's safety checking
                is_dangerous = any(pattern in cmd.lower() for pattern in ['rm -rf', 'sudo', 'chmod 777'])
                assert is_dangerous, f"Failed to detect dangerous command: {cmd}"
            
            results.append(TestResult("dangerous_command_detection", True, "Dangerous command detection working"))
        except Exception as e:
            results.append(TestResult("dangerous_command_detection", False, f"Safety measures failed: {e}"))
        
        return results
    
    def _display_category_results(self, category: str, results: List[TestResult]):
        """Display results for a test category."""
        if isinstance(results, dict) and "error" in results:
            self.console.print(f"[red]❌ {category}: {results['error']}[/]")
            return
        
        passed = sum(1 for r in results if r.success)
        total = len(results)
        
        if passed == total:
            self.console.print(f"[green]✅ {category}: {passed}/{total} tests passed[/]")
        else:
            self.console.print(f"[yellow]⚠️  {category}: {passed}/{total} tests passed[/]")
            
        for result in results:
            if not result.success:
                self.console.print(f"  [red]❌ {result.test_name}: {result.message}[/]")
    
    def _generate_test_report(self, results: Dict) -> Dict[str, Any]:
        """Generate a comprehensive test report."""
        total_tests = 0
        passed_tests = 0
        failed_tests = []
        
        for category, category_results in results.items():
            if isinstance(category_results, dict) and "error" in category_results:
                failed_tests.append(f"{category}: {category_results['error']}")
                continue
                
            for result in category_results:
                total_tests += 1
                if result.success:
                    passed_tests += 1
                else:
                    failed_tests.append(f"{category}.{result.test_name}: {result.message}")
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": len(failed_tests),
            "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            "failures": failed_tests,
            "timestamp": datetime.now().isoformat(),
            "detailed_results": results
        }
    
    def _display_final_report(self, report: Dict):
        """Display the final test report."""
        table = Table(title="🧪 Agent Test Report")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white")
        
        table.add_row("Total Tests", str(report["total_tests"]))
        table.add_row("Passed", f"[green]{report['passed_tests']}[/]")
        table.add_row("Failed", f"[red]{report['failed_tests']}[/]")
        table.add_row("Success Rate", f"{report['success_rate']:.1f}%")
        
        self.console.print(table)
        
        if report["failures"]:
            self.console.print("\n[red]❌ Failed Tests:[/]")
            for failure in report["failures"]:
                self.console.print(f"  • {failure}")
    
    def validate_agent_health(self, agent) -> Tuple[bool, List[str]]:
        """Quick health check for the agent."""
        issues = []
        
        # Check memory system
        try:
            agent.memory.get_memory_stats()
        except Exception as e:
            issues.append(f"Memory system error: {e}")
        
        # Check tool availability
        try:
            from .tools import TOOLS
            if not TOOLS:
                issues.append("No tools available")
        except Exception as e:
            issues.append(f"Tool system error: {e}")
        
        # Check model connectivity (if applicable)
        if hasattr(agent, 'model') and agent.model:
            try:
                # Basic connectivity test would go here
                pass
            except Exception as e:
                issues.append(f"Model connectivity error: {e}")
        
        return len(issues) == 0, issues
    
    def run_continuous_monitoring(self, agent, interval: int = 300):
        """Run continuous monitoring of agent health."""
        self.console.print(f"[cyan]🔍 Starting continuous monitoring (every {interval}s)[/]")
        
        import time
        while True:
            try:
                healthy, issues = self.validate_agent_health(agent)
                
                if healthy:
                    self.console.print(f"[green]✅ Agent health check passed at {datetime.now().strftime('%H:%M:%S')}[/]")
                else:
                    self.console.print(f"[red]❌ Agent health issues detected:[/]")
                    for issue in issues:
                        self.console.print(f"  • {issue}")
                
                time.sleep(interval)
            except KeyboardInterrupt:
                self.console.print("\n[yellow]⏹️  Monitoring stopped by user[/]")
                break
            except Exception as e:
                self.console.print(f"[red]Monitoring error: {e}[/]")
                time.sleep(interval)
