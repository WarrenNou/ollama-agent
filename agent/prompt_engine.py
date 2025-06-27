"""
Advanced prompt engineering and response parsing for better agent reliability.
"""

import json
import re
from typing import Dict, List, Any, Optional, Tuple
from rich.console import Console


class PromptEngine:
    """Advanced prompt engineering and response parsing system."""
    
    def __init__(self, console: Console = None):
        self.console = console or Console()
        
    def create_enhanced_prompt(self, goal: str, history: List[Dict], 
                             available_tools: List[str], context: str = "") -> str:
        """Create an enhanced, more reliable prompt."""
        
        # Tool descriptions with clear formatting
        tool_descriptions = {
            "execute_shell_command": "Execute system commands (requires confirmation for dangerous operations)",
            "search_file": "Read and display file contents",
            "create_file": "Create a new file with optional content",
            "modify_file": "Create or modify file contents (shows diff preview)",
            "append_to_file": "Append content to an existing file",
            "edit_file_lines": "Edit specific lines in a file (start_line, end_line, new_content)",
            "list_directory": "List directory contents with file sizes",
            "find_files": "Find files matching patterns recursively",
            "get_file_info": "Get detailed file/directory metadata",
            "create_directory": "Create new directories",
            "create_folder": "Create new folders/directory structures",
            "create_project_structure": "Create complete project templates (python, web, generic)",
            "copy_file": "Copy files from source to destination",
            "move_file": "Move/rename files (requires confirmation)",
            "delete_file": "Delete files/directories (requires confirmation)",
            "search_in_files": "Search for text patterns within files",
            "get_current_directory": "Display current working directory",
            "change_directory": "Change working directory",
            "get_memory_statistics": "Display agent memory system statistics",
            "open_browser": "Open URLs or local files in default browser",
            "create_html_file": "Create HTML files with basic structure",
            "view_file_in_browser": "View any text file in browser with syntax highlighting",
            
            # Advanced development tools
            "generate_code_template": "Generate code templates (language, template_type, name)",
            "create_development_server": "Create and configure development servers",
            "analyze_project_structure": "Analyze project structure and provide insights",
            "setup_git_repository": "Initialize git repository with optional remote",
            "create_docker_setup": "Create Dockerfile and Docker setup for projects",
            "run_code_quality_check": "Run code quality checks (linting, formatting)",
            
            "no_op": "Take no action (explain reasoning)",
            "finish": "Complete the goal (provide summary)"
        }
        
        # Create tools section
        tools_section = "AVAILABLE TOOLS:\n"
        for i, tool in enumerate(available_tools, 1):
            description = tool_descriptions.get(tool, "No description available")
            tools_section += f"{i:2d}. {tool}: {description}\n"
        
        # Create history section
        history_section = "EXECUTION HISTORY:\n"
        if not history:
            history_section += "No previous actions taken.\n"
        else:
            # Show last 5 actions to avoid overwhelming the context
            recent_history = history[-5:] if len(history) > 5 else history
            for i, action in enumerate(recent_history, 1):
                tool = action.get('action', 'unknown')
                args = action.get('args', {})
                result = str(action.get('result', ''))[:100] + "..." if len(str(action.get('result', ''))) > 100 else str(action.get('result', ''))
                history_section += f"{i}. {tool}({args}) -> {result}\n"
        
        # Context section
        context_section = ""
        if context:
            context_section = f"\nRELEVANT CONTEXT:\n{context}\n"
        
        # Main prompt
        prompt = f"""You are an intelligent autonomous agent designed to achieve goals through systematic tool execution.

GOAL: {goal}

{tools_section}
{history_section}{context_section}

RESPONSE FORMAT:
You MUST respond with valid JSON containing exactly these fields:
{{
    "thought": "Your reasoning about what to do next",
    "tool": "exact_tool_name_from_list_above", 
    "args": {{"param1": "value1", "param2": "value2"}}
}}

CRITICAL RULES:
1. Tool name must EXACTLY match one from the available tools list
2. Use proper JSON formatting with double quotes
3. Think step-by-step before acting
4. Avoid repeating failed actions
5. If unsure about tool names, use 'no_op' to explain the issue
6. Use 'finish' when the goal is fully accomplished

EXAMPLES:
- To list files: {{"thought": "I need to see what files are available", "tool": "list_directory", "args": {{"directory_path": "."}}}}
- To read a file: {{"thought": "I should examine this file", "tool": "search_file", "args": {{"file_path": "example.txt"}}}}
- To create directory: {{"thought": "I need to create a directory for my project", "tool": "create_directory", "args": {{"directory_path": "my_project"}}}}
- To create file: {{"thought": "I need to create a Python file", "tool": "create_file", "args": {{"file_path": "main.py", "content": "print('Hello World')"}}}}
- To modify file: {{"thought": "I need to update this file", "tool": "modify_file", "args": {{"file_path": "config.py", "new_content": "config = {{'debug': True}}"}}}}
- To get memory stats: {{"thought": "I need to check memory statistics", "tool": "get_memory_statistics", "args": {{}}}}

What is your next action to achieve the goal?"""

        return prompt
    
    def parse_response(self, response_text: str) -> Tuple[Optional[Dict], List[str]]:
        """Parse model response with enhanced error handling."""
        errors = []
        
        if not response_text or not response_text.strip():
            errors.append("Empty response from model")
            return None, errors
        
        # Try to extract JSON from response
        json_candidates = []
        
        # Method 1: Look for complete JSON objects
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(json_pattern, response_text, re.DOTALL)
        json_candidates.extend(matches)
        
        # Method 2: Look for content between code blocks
        code_block_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
        code_matches = re.findall(code_block_pattern, response_text, re.DOTALL | re.IGNORECASE)
        json_candidates.extend(code_matches)
        
        # Method 3: Try the entire response if it looks like JSON
        if response_text.strip().startswith('{') and response_text.strip().endswith('}'):
            json_candidates.append(response_text.strip())
        
        # Try to parse each candidate
        for candidate in json_candidates:
            try:
                # Clean up common issues
                cleaned = self._clean_json_string(candidate)
                parsed = json.loads(cleaned)
                
                # Validate required fields
                if self._validate_parsed_response(parsed):
                    return parsed, []
                else:
                    errors.append(f"Invalid response structure: {parsed}")
                    
            except json.JSONDecodeError as e:
                errors.append(f"JSON decode error in '{candidate[:50]}...': {e}")
                continue
        
        # If all parsing failed, try to extract components manually
        thought_match = re.search(r'"thought":\s*"([^"]*)"', response_text)
        tool_match = re.search(r'"tool":\s*"([^"]*)"', response_text)
        
        if thought_match and tool_match:
            # Try to reconstruct a valid response
            reconstructed = {
                "thought": thought_match.group(1),
                "tool": tool_match.group(1),
                "args": {}
            }
            
            # Try to extract args
            args_match = re.search(r'"args":\s*(\{[^}]*\})', response_text)
            if args_match:
                try:
                    reconstructed["args"] = json.loads(args_match.group(1))
                except:
                    pass
            
            if self._validate_parsed_response(reconstructed):
                return reconstructed, ["Reconstructed from partial parse"]
        
        errors.append(f"Could not parse any valid JSON from response: {response_text[:200]}...")
        return None, errors
    
    def _clean_json_string(self, json_str: str) -> str:
        """Clean common JSON formatting issues."""
        # Remove leading/trailing whitespace
        cleaned = json_str.strip()
        
        # Remove markdown code block markers
        cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\s*```$', '', cleaned)
        
        # Fix common quote issues
        cleaned = re.sub(r'([{,]\s*)(\w+)(\s*:)', r'\1"\2"\3', cleaned)  # Add quotes to unquoted keys
        
        # Fix trailing commas
        cleaned = re.sub(r',(\s*[}\]])', r'\1', cleaned)
        
        return cleaned
    
    def _validate_parsed_response(self, parsed: Dict) -> bool:
        """Validate that parsed response has required structure."""
        if not isinstance(parsed, dict):
            return False
        
        required_fields = ["thought", "tool"]
        for field in required_fields:
            if field not in parsed:
                return False
            if not isinstance(parsed[field], str):
                return False
        
        # Args is optional but must be dict if present
        if "args" in parsed and not isinstance(parsed["args"], dict):
            return False
        
        return True
    
    def suggest_recovery_action(self, goal: str, history: List[Dict], 
                               errors: List[str]) -> Dict[str, Any]:
        """Suggest a recovery action when parsing fails."""
        # Analyze the situation and suggest a safe next step
        
        if not history:
            # No history, start with basic exploration
            return {
                "thought": "Starting with directory exploration to understand the workspace",
                "tool": "list_directory",
                "args": {"directory_path": "."}
            }
        
        # Look at recent failed actions
        recent_actions = history[-3:] if len(history) >= 3 else history
        failed_tools = [action.get('action') for action in recent_actions 
                       if 'error' in str(action.get('result', '')).lower() or 
                          'unknown tool' in str(action.get('result', '')).lower()]
        
        # If we've been failing with tool calls, try a no-op to explain
        if len(failed_tools) >= 2:
            return {
                "thought": f"Multiple tool failures detected. Need to clarify available actions. Errors: {'; '.join(errors[:2])}",
                "tool": "no_op",
                "args": {"reason": "Experiencing parsing errors, need user guidance"}
            }
        
        # Try a safe, basic action based on the goal
        goal_lower = goal.lower()
        if "memory" in goal_lower or "statistics" in goal_lower:
            return {
                "thought": "Goal mentions memory/statistics, attempting to get memory statistics",
                "tool": "get_memory_statistics",
                "args": {}
            }
        elif "list" in goal_lower or "show" in goal_lower:
            return {
                "thought": "Goal mentions listing/showing, starting with directory listing",
                "tool": "list_directory", 
                "args": {"directory_path": "."}
            }
        else:
            return {
                "thought": "Taking safe exploratory action to understand current state",
                "tool": "get_current_directory",
                "args": {}
            }


class ResponseValidator:
    """Validates and improves agent responses."""
    
    @staticmethod
    def validate_tool_exists(tool_name: str, available_tools: List[str]) -> bool:
        """Check if tool exists in available tools."""
        return tool_name in available_tools
    
    @staticmethod
    def suggest_tool_correction(attempted_tool: str, available_tools: List[str]) -> Optional[str]:
        """Suggest closest matching tool name."""
        import difflib
        
        # Find closest matches
        close_matches = difflib.get_close_matches(attempted_tool, available_tools, n=1, cutoff=0.6)
        return close_matches[0] if close_matches else None
    
    @staticmethod
    def validate_tool_args(tool_name: str, args: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate tool arguments (basic validation)."""
        errors = []
        
        # Tool-specific argument validation
        if tool_name == "search_file" and "file_path" not in args:
            errors.append("search_file requires 'file_path' argument")
        elif tool_name == "modify_file" and ("file_path" not in args or "new_content" not in args):
            errors.append("modify_file requires 'file_path' and 'new_content' arguments")
        elif tool_name == "execute_shell_command" and "command" not in args:
            errors.append("execute_shell_command requires 'command' argument")
        elif tool_name == "list_directory" and args and "directory_path" not in args:
            errors.append("list_directory expects 'directory_path' argument")
        
        return len(errors) == 0, errors
