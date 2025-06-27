import os
import re
import json
import difflib
import requests

from rich.console import Console
from rich.prompt import Prompt, Confirm

from . import tools
from .memory import MemoryManager
from .prompt_engine import PromptEngine, ResponseValidator

class Agent:
    def __init__(
        self,
        model: str = "llama3",
        max_steps: int = 50,  # Increased default
        timeout: int | None = None,
        verbose: bool = False,
        stream: bool = False,
        console: Console | None = None,
        adaptive_steps: bool = True,
        auto_test: bool = True,  # Enable automatic testing
        no_confirm: bool = False,  # Skip confirmations for operations
    ):
        self.model = model
        self.max_steps = max_steps
        self.timeout = timeout
        self.verbose = verbose
        self.stream = stream
        self.console = console or Console()
        self.history: list[dict] = []
        self.goal = ""
        self.memory = MemoryManager()
        self.adaptive_steps = adaptive_steps
        self.task_complexity_score = 1.0
        self.prompt_engine = PromptEngine(self.console)
        self.response_validator = ResponseValidator()
        self.auto_test = auto_test
        self.quality_threshold = 0.8  # Minimum quality score for generated code
        self.no_confirm = no_confirm
        self.session_consent_given = False  # Track if user has given session-wide consent

    def _get_ollama_response(self, prompt: str) -> str:
        url = "http://localhost:11434/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": self.stream,
            "format": "json",
        }
        try:
            response = requests.post(
                url,
                json=payload,
                stream=self.stream,
                timeout=self.timeout,
            )
        except requests.exceptions.RequestException as e:
            return json.dumps({"error": "RequestException", "details": str(e)})

        if self.stream:
            text = ""
            for line in response.iter_lines(decode_unicode=True):
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    token = data.get("token", line)
                except json.JSONDecodeError:
                    token = line
                self.console.print(token, end="")
                text += token
            self.console.print()  # newline after stream
            return text

        try:
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")
        except requests.exceptions.RequestException as e:
            return json.dumps({"error": "RequestException", "details": str(e)})
        except json.JSONDecodeError as e:
            return json.dumps({"error": "JSONDecodeError", "details": str(e)})


    def execute(self, goal: str) -> None:
        """Main loop: iteratively ask the model for next actions until finish or max_steps."""
        self.history.clear()
        self.goal = goal
        
        # Enhanced intelligence: Analyze task before execution
        try:
            from .intelligence_tools import analyze_task_intelligence
            analysis_result = analyze_task_intelligence(goal, "adaptive")
            analysis_data = json.loads(analysis_result)
            self.console.print(f"[cyan]🧠 Task Analysis:[/]")
            self.console.print(f"  • Complexity Score: {analysis_data.get('complexity_score', 0):.2f}")
            self.console.print(f"  • Estimated Steps: {analysis_data.get('estimated_steps', 'Unknown')}")
            if analysis_data.get('recommendations'):
                self.console.print("  • Recommendations:")
                for rec in analysis_data['recommendations']:
                    self.console.print(f"    - {rec}")
        except Exception as e:
            if self.verbose:
                self.console.print(f"[dim]Task analysis unavailable: {e}[/]")
        
        # Request session consent for operations (unless in no-confirm mode)
        if not self.no_confirm and not self.session_consent_given:
            if not self.get_session_consent():
                self.console.print("[red]Cannot proceed without session permissions.[/]")
                return
        
        # Calculate adaptive max steps based on task complexity
        if self.adaptive_steps:
            self.max_steps = self._calculate_adaptive_steps(goal)
            self.console.print(f"[dim]Adaptive max steps: {self.max_steps}[/]")

        for step in range(1, self.max_steps + 1):
            self.console.rule(f"Step {step}/{self.max_steps}")

            # Create enhanced prompt with context
            relevant_context = self.memory.get_relevant_context(goal)
            available_tools = list(tools.TOOLS.keys()) + ["no_op", "finish"]
            
            prompt = self.prompt_engine.create_enhanced_prompt(
                goal=goal,
                history=self.history,
                available_tools=available_tools,
                context=relevant_context
            )
            
            if self.verbose:
                self.console.print("[cyan]Enhanced prompt sent to model:[/]")
                self.console.print(prompt)

            response_text = self._get_ollama_response(prompt)
            if self.verbose and not self.stream:
                self.console.print("[cyan]Raw model response:[/]")
                self.console.print(response_text)

            # Record memory
            self.memory.store_memory("execution", {"goal": goal, "step": step, "response": response_text})

            # Enhanced response parsing
            parsed_response, parsing_errors = self.prompt_engine.parse_response(response_text)
            
            if parsed_response is None:
                self.console.print("[red]Failed to parse model response.[/]")
                if parsing_errors:
                    self.console.print("[yellow]Parsing errors:[/]")
                    for error in parsing_errors:
                        self.console.print(f"  • {error}")
                
                # Use recovery action
                recovery_action = self.prompt_engine.suggest_recovery_action(goal, self.history, parsing_errors)
                self.console.print(f"[cyan]Using recovery action: {recovery_action['tool']}[/]")
                parsed_response = recovery_action

            tool = parsed_response.get("tool")
            args = parsed_response.get("args", {})
            thought = parsed_response.get("thought", "")
            
            # Validate tool exists and suggest corrections
            if tool not in available_tools:
                suggested_tool = self.response_validator.suggest_tool_correction(tool, available_tools)
                if suggested_tool:
                    self.console.print(f"[yellow]Unknown tool '{tool}', did you mean '{suggested_tool}'?[/]")
                    tool = suggested_tool
                else:
                    self.console.print(f"[red]Unknown tool '{tool}', using no_op instead[/]")
                    tool = "no_op"
                    args = {"reason": f"Unknown tool attempted: {tool}"}
            
            # Validate tool arguments
            args_valid, arg_errors = self.response_validator.validate_tool_args(tool, args)
            if not args_valid:
                self.console.print("[yellow]Tool argument validation errors:[/]")
                for error in arg_errors:
                    self.console.print(f"  • {error}")

            if thought:
                self.console.print(f"[yellow]Thought:[/] {thought}")

            # if model did not return a valid tool, ask for clarification
            if not tool:
                self.console.print("[yellow]Agent: did not receive a valid action from the model.[/]")
                self.console.print(f"[cyan]Model response:[/] {response_text}")
                clar = Prompt.ask("Please clarify your goal or press Enter to exit", default="")
                if clar:
                    self.goal += f"\n{clar}"
                    continue
                self.console.print("[red]No clarification provided; ending execution.[/]")
                break

            # handle finish
            if tool == "finish":
                reason = args.get("reason", "")
                self.console.print("[bold green]Goal achieved![/]")
                if reason:
                    self.console.print(reason)
                # Mark task success in memory
                self.memory.store_memory("goal_accomplished", {"goal": self.goal, "reason": reason}, success=True)
                break

            # handle explicit no-op
            if tool == "no_op":
                reason = args.get("reason", "")
                self.console.print(f"[yellow]No-op:[/] {reason}")
                # Store no-op in memory
                self.memory.store_memory("no_op", {"goal": self.goal, "reason": reason}, success=False)
                response = Prompt.ask("Provide clarification or press Enter to exit", default="")
                if response:
                    self.goal += f"\n{response}"
                    continue
                self.console.print("[red]No clarification provided; ending execution.[/]")
                break

            # execute tools
            result = self._execute_tool(tool, args)
            self.memory.store_memory("tool_usage", {"tool": tool, "args": args, "result": result})
            self.console.print(f"[blue]Action:[/] {tool} [blue]Args:[/]{args}")
            self.console.print(f"[green]Result:[/] {result}")
            self.history.append({"action": tool, "args": args, "result": result})
            
            # Perform self-testing and iteration at regular intervals
            if self._should_self_test(step):
                if not self._iterate_and_improve():
                    # If self-test suggests stopping, ask user
                    if not Confirm.ask("Continue despite low progress?", default=True):
                        break

        else:
            # loop did not break
            self.console.print(f"[red]Max steps ({self.max_steps}) reached; ending execution.[/]")

    def _execute_tool(self, tool_name: str, args: dict) -> str:
        """Execute tool with session-level consent instead of per-operation confirmations."""
        return self._invoke_tool_with_consent(tool_name, args)

    def _create_prompt(self) -> str:
        """Construct the prompt for the model including goal, tools, and history."""
        return (
            f"You are an autonomous agent that achieves goals by executing tools.\n\n"
            f"Goal: {self.goal}\n\n"
            "Available tools:\n"
            "1. execute_shell_command(command): Executes a shell command\n"
            "2. search_file(file_path): Reads the content of a file\n"
            "3. modify_file(file_path, new_content): Writes new content to a file (creates if doesn't exist)\n"
            "4. list_directory(directory_path): Lists contents of a directory (default: current)\n"
            "5. find_files(pattern, directory): Finds files matching a pattern\n"
            "6. get_file_info(file_path): Gets detailed information about a file\n"
            "7. create_directory(directory_path): Creates a directory\n"
            "8. copy_file(source, destination): Copies a file\n"
            "9. move_file(source, destination): Moves/renames a file\n"
            "10. delete_file(file_path): Deletes a file or directory\n"
            "11. search_in_files(pattern, directory, file_pattern): Searches for text patterns in files\n"
            "12. get_current_directory(): Gets the current working directory\n"
            "13. change_directory(directory_path): Changes the working directory\n"
            "14. get_memory_statistics(): Gets detailed memory system statistics\n"
            "15. no_op(reason): If the goal is unclear or conversational. Provide a reason\n"
            "16. finish(reason): Call when the goal is achieved\n\n"
            "Example response format:\n"
            '{"thought": "I need to list the current directory to see what files are available", "tool": "list_directory", "args": {"directory_path": "."}}\n\n'
            "History of previous actions:\n"
            f"{json.dumps(self.history, indent=2)}\n\n"
            "Important guidelines:\n"
            "- Always think step by step and explain your reasoning\n"
            "- Use appropriate tools for the task at hand\n"
            "- Be careful with destructive operations (delete, move, execute_shell_command)\n"
            "- Check directory contents before performing file operations\n"
            "- When you have gathered enough information to complete the goal, use 'finish' with a summary\n"
            "- Avoid repeating the same action multiple times\n"
            "- Your response MUST be valid JSON with 'thought', 'tool', and 'args' keys\n\n"
            "Based on the goal and history, decide on the next single action:"
        )
    
    def _calculate_adaptive_steps(self, goal: str) -> int:
        """Calculate adaptive max steps based on task complexity."""
        base_steps = 20
        complexity_indicators = [
            ('create', 5), ('analyze', 10), ('comprehensive', 15), ('test', 8),
            ('implement', 12), ('generate', 8), ('optimize', 15), ('refactor', 12),
            ('document', 10), ('backup', 6), ('migrate', 15), ('deploy', 12),
            ('multiple', 8), ('all', 6), ('entire', 10), ('complex', 15),
            ('advanced', 12), ('detailed', 8), ('thorough', 10)
        ]
        
        goal_lower = goal.lower()
        complexity_score = 1.0
        
        for indicator, weight in complexity_indicators:
            if indicator in goal_lower:
                complexity_score += weight * 0.1
        
        # Check for multiple tasks or conjunctions
        conjunctions = ['and', 'then', 'also', 'additionally', 'furthermore']
        for conj in conjunctions:
            complexity_score += goal_lower.count(conj) * 0.3
        
        # Estimate based on goal length (longer goals tend to be more complex)
        word_count = len(goal.split())
        if word_count > 20:
            complexity_score += (word_count - 20) * 0.05
        
        self.task_complexity_score = complexity_score
        adaptive_steps = int(base_steps * complexity_score)
        
        # Cap between reasonable bounds
        return max(20, min(adaptive_steps, 200))
    
    def _should_self_test(self, step: int) -> bool:
        """Determine if self-testing should be triggered."""
        # Test every 10 steps, or when approaching max steps
        return (step % 10 == 0) or (step >= self.max_steps * 0.8)
    
    def _perform_self_test(self) -> dict:
        """Perform self-testing to validate current progress."""
        self.console.print("[cyan]🔍 Performing self-test...[/]")
        
        test_results = {
            "progress_score": self._evaluate_progress(),
            "goal_alignment": self._check_goal_alignment(),
            "quality_check": self._check_output_quality(),
            "next_steps": self._suggest_next_steps()
        }
        
        # Store self-test results in memory
        self.memory.store_memory(
            "self_test",
            test_results,
            importance=0.8,
            tags=["self_test", "validation"],
            success=test_results["progress_score"] > 0.5
        )
        
        return test_results
    
    def _evaluate_progress(self) -> float:
        """Evaluate progress towards the goal (0.0 to 1.0)."""
        if not self.history:
            return 0.0
        
        successful_actions = sum(1 for h in self.history if "error" not in str(h.get("result", "")).lower())
        total_actions = len(self.history)
        
        # Basic progress score based on successful actions
        base_score = successful_actions / total_actions if total_actions > 0 else 0.0
        
        # Bonus for diverse action types (indicates comprehensive work)
        unique_actions = len(set(h.get("action", "") for h in self.history))
        diversity_bonus = min(unique_actions * 0.1, 0.3)
        
        return min(base_score + diversity_bonus, 1.0)
    
    def _check_goal_alignment(self) -> float:
        """Check how well recent actions align with the goal (0.0 to 1.0)."""
        if not self.history:
            return 0.5  # Neutral if no history
        
        goal_keywords = set(self.goal.lower().split())
        recent_actions = self.history[-5:]  # Check last 5 actions
        
        alignment_score = 0.0
        for action in recent_actions:
            action_text = f"{action.get('action', '')} {str(action.get('args', ''))} {str(action.get('result', ''))}"
            action_keywords = set(action_text.lower().split())
            
            # Calculate keyword overlap
            overlap = len(goal_keywords.intersection(action_keywords))
            alignment_score += overlap / max(len(goal_keywords), 1)
        
        return min(alignment_score / len(recent_actions), 1.0) if recent_actions else 0.5
    
    def _check_output_quality(self) -> dict:
        """Check the quality of outputs produced so far."""
        quality_metrics = {
            "files_created": 0,
            "files_modified": 0,
            "errors_encountered": 0,
            "successful_operations": 0
        }
        
        for action in self.history:
            action_name = action.get("action", "")
            result = str(action.get("result", ""))
            
            if "error" in result.lower() or "failed" in result.lower():
                quality_metrics["errors_encountered"] += 1
            elif "successfully" in result.lower() or "created" in result.lower():
                quality_metrics["successful_operations"] += 1
            
            if action_name == "modify_file" and "successfully" in result.lower():
                if "created" in result.lower():
                    quality_metrics["files_created"] += 1
                else:
                    quality_metrics["files_modified"] += 1
        
        return quality_metrics
    
    def _suggest_next_steps(self) -> list:
        """Suggest next steps based on current progress and goal."""
        suggestions = []
        
        # Analyze what's been done
        actions_taken = [h.get("action", "") for h in self.history]
        
        # Check if fundamental steps are missing
        if "list_directory" not in actions_taken:
            suggestions.append("Consider listing directory contents to understand the workspace")
        
        if "search_file" not in actions_taken and "analyze" in self.goal.lower():
            suggestions.append("Search and read key files to understand the codebase")
        
        if "modify_file" not in actions_taken and any(word in self.goal.lower() for word in ["create", "generate", "write"]):
            suggestions.append("Consider creating or modifying files to achieve the goal")
        
        # Check for testing if the goal involves creation
        if any(word in self.goal.lower() for word in ["create", "implement", "generate"]) and "test" not in self.goal.lower():
            if not any("test" in str(h.get("result", "")).lower() for h in self.history):
                suggestions.append("Consider testing your work to ensure quality")
        
        # Generic suggestions based on progress
        progress = self._evaluate_progress()
        if progress < 0.3:
            suggestions.append("Focus on understanding the current state before making changes")
        elif progress < 0.7:
            suggestions.append("Continue making progress towards the goal with concrete actions")
        else:
            suggestions.append("Consider reviewing and testing your work before finishing")
        
        return suggestions
    
    def _iterate_and_improve(self) -> bool:
        """Iterate and improve based on self-test results."""
        test_results = self._perform_self_test()
        
        self.console.print(f"[cyan]Progress Score: {test_results['progress_score']:.2f}[/]")
        self.console.print(f"[cyan]Goal Alignment: {test_results['goal_alignment']:.2f}[/]")
        
        quality = test_results['quality_check']
        self.console.print(f"[cyan]Quality Metrics:[/]")
        for metric, value in quality.items():
            self.console.print(f"  {metric}: {value}")
        
        if test_results['next_steps']:
            self.console.print("[yellow]Suggested next steps:[/]")
            for suggestion in test_results['next_steps']:
                self.console.print(f"  • {suggestion}")
        
        # Decide whether to continue or adjust approach
        if test_results['progress_score'] < 0.3 and len(self.history) > 5:
            self.console.print("[yellow]⚠️  Low progress detected. Consider adjusting approach.[/]")
            return False
        
        return True

    def _test_and_improve_code(self, file_path: str, code_type: str = "python") -> dict:
        """Test generated code and improve it if quality is below threshold."""
        if not self.auto_test:
            return {"tested": False, "improved": False}
            
        try:
            # Test the generated code
            if "test_generated_code" in tools.TOOLS:
                test_result = tools.TOOLS["test_generated_code"](file_path, code_type)
                
                # Parse test results
                if isinstance(test_result, str):
                    try:
                        test_data = json.loads(test_result)
                    except:
                        test_data = {"overall_score": 0.5, "issues": [test_result]}
                else:
                    test_data = test_result
                
                quality_score = test_data.get("overall_score", 0.5)
                
                # If quality is below threshold, try to improve
                if quality_score < self.quality_threshold:
                    self.console.print(f"[yellow]Code quality score: {quality_score:.2f} (below threshold {self.quality_threshold})[/]")
                    self.console.print("[yellow]Attempting to improve code...[/]")
                    
                    # Attempt automatic improvement
                    if code_type == "python" and "snake" in file_path.lower():
                        if "improve_snake_game" in tools.TOOLS:
                            improved_code = tools.TOOLS["improve_snake_game"](file_path)
                            if improved_code and not improved_code.startswith("Error"):
                                # Write improved code back
                                with open(file_path, 'w') as f:
                                    f.write(improved_code)
                                self.console.print("[green]Code improved successfully![/]")
                                return {"tested": True, "improved": True, "quality_score": quality_score}
                    
                    # Generic improvement attempt
                    self.console.print("[yellow]Manual review recommended for further improvements[/]")
                    return {"tested": True, "improved": False, "quality_score": quality_score}
                else:
                    self.console.print(f"[green]Code quality score: {quality_score:.2f} (meets threshold)[/]")
                    return {"tested": True, "improved": False, "quality_score": quality_score}
                    
        except Exception as e:
            self.console.print(f"[red]Error during code testing: {e}[/]")
            return {"tested": False, "improved": False, "error": str(e)}
        
        return {"tested": False, "improved": False}

    def get_session_consent(self):
        """Ask for session-wide consent for file operations and commands."""
        if self.no_confirm or self.session_consent_given:
            return True
            
        self.console.print("\n[yellow]🔒 Session Permissions[/]")
        self.console.print("This agent may need to:")
        self.console.print("• Create, modify, and delete files")
        self.console.print("• Execute shell commands")
        self.console.print("• Make changes to your project")
        
        if Confirm.ask("\nDo you give permission for these operations during this session?", default=True):
            self.session_consent_given = True
            self.console.print("[green]✅ Session permissions granted![/]")
            return True
        else:
            self.console.print("[red]❌ Session permissions denied. Agent will run in read-only mode.[/]")
            return False

    def _invoke_tool_with_consent(self, tool_name: str, args: dict) -> str:
        """Invoke tool with session-level consent instead of per-operation confirmations."""
        # Import tools here to avoid circular imports
        from . import tools
        TOOLS = tools.TOOLS
        
        # Check if tool exists
        if tool_name not in TOOLS:
            return f"Unknown tool: {tool_name}"
        
        # For write operations, check session consent
        write_operations = ["execute_shell_command", "modify_file", "delete_file", "move_file"]
        
        if tool_name in write_operations and not self.session_consent_given and not self.no_confirm:
            if not self.get_session_consent():
                return "❌ Operation cancelled - insufficient permissions"
        
        # Handle tools that traditionally needed confirmation
        if tool_name == "execute_shell_command":
            cmd = args.get("command", "")
            # Check for potentially dangerous commands
            dangerous_patterns = ['rm -rf', 'sudo', 'chmod 777', 'mkfs', 'dd if=', '> /dev/']
            is_dangerous = any(pattern in cmd.lower() for pattern in dangerous_patterns)
            
            if is_dangerous and not self.no_confirm:
                self.console.print("[red]⚠️  DANGEROUS COMMAND DETECTED![/]")
                if not Confirm.ask(f"Are you SURE you want to execute? [cyan]{cmd}[/]", default=False):
                    return "[skipped - dangerous command]"
            
            return TOOLS[tool_name](cmd)
        
        elif tool_name == "modify_file":
            path = args.get("file_path", "")
            new_content = args.get("new_content", "")
            try:
                old_content = tools.search_file(path) if os.path.exists(path) else ""
            except Exception:
                old_content = ""
            
            # Show diff for file modifications only if verbose or first time
            if self.verbose or not self.session_consent_given:
                diff_text = "\n".join(
                    difflib.unified_diff(
                        old_content.splitlines(),
                        new_content.splitlines(),
                        fromfile=path, tofile=path,
                        lineterm="",
                    )
                )
                if diff_text:
                    self.console.print("[magenta]Preview diff:[/]")
                    self.console.print(diff_text)
            
            return TOOLS[tool_name](path, new_content)
        
        # For other tools that previously required confirmation, just execute with session consent
        elif tool_name in ["delete_file", "move_file"]:
            return TOOLS[tool_name](**args)
        
        # For safe tools, execute directly
        else:
            try:
                # Get the function and call it with the arguments
                func = TOOLS[tool_name]
                return func(**args)
            except Exception as e:
                return f"Error calling {tool_name}: {str(e)}"
