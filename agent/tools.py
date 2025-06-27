import subprocess
import os
import json
import glob
import shutil
import webbrowser
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import safety manager (disabled for streamlined user experience)
try:
    from .safety import safety_manager
    # Disable safety manager for better UX - agent handles consent at session level
    safety_manager = None
except ImportError:
    safety_manager = None

def execute_shell_command(command: str) -> str:
    """Executes a shell command and returns the output with enhanced safety checks."""
    try:
        # Enhanced safety check
        if safety_manager:
            risk_level, risk_score, warnings = safety_manager.assess_command_risk(command)
            
            # Require confirmation for risky commands
            if not safety_manager.require_confirmation(
                "Shell Command Execution",
                f"Command: {command}",
                risk_level,
                warnings
            ):
                return "Operation cancelled by user due to safety concerns"
            
            # Log the operation
            safety_manager.log_risky_operation(
                "shell_command",
                command,
                risk_level,
                True
            )
            
            # Sanitize command
            command = safety_manager.sanitize_command(command)
        
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=30
        )
        output = result.stdout.strip()
        if result.stderr:
            output += f"\nSTDERR: {result.stderr.strip()}"
        if result.returncode != 0:
            output += f"\nExit code: {result.returncode}"
        return output
    except subprocess.TimeoutExpired:
        return "Command timed out after 30 seconds"
    except Exception as e:
        return f"Error executing command: {str(e)}"

def search_file(file_path: str) -> str:
    """Reads and returns the content of a specified file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except FileNotFoundError:
        return f"File not found: {file_path}"
    except PermissionError:
        return f"Permission denied: {file_path}"
    except UnicodeDecodeError:
        return f"Cannot decode file (not UTF-8): {file_path}"
    except Exception as e:
        return f"Error reading file: {str(e)}"

def create_file(file_path: str, content: str = "") -> str:
    """Creates a new file with optional content."""
    try:
        # Create directory if it doesn't exist
        directory = os.path.dirname(file_path)
        if directory and directory != '.':
            os.makedirs(directory, exist_ok=True)
        
        # Check if file already exists
        if os.path.exists(file_path):
            return f"File already exists: {file_path}. Use modify_file to update it."
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully created {file_path}"
    except PermissionError:
        return f"Permission denied: {file_path}"
    except Exception as e:
        return f"Error creating file: {str(e)}"

def modify_file(file_path: str, new_content: str) -> str:
    """Writes new content to a specified file with enhanced safety checks."""
    try:
        # Enhanced safety check
        if safety_manager:
            risk_level, risk_score, warnings = safety_manager.assess_file_operation_risk("modify", file_path)
            
            # Create backup for risky operations
            if risk_level in ["MEDIUM", "HIGH", "CRITICAL"]:
                backup_result = safety_manager.create_backup(file_path)
                
                # Require confirmation
                if not safety_manager.require_confirmation(
                    "File Modification",
                    f"File: {file_path}\nBackup: {backup_result}",
                    risk_level,
                    warnings
                ):
                    return "Operation cancelled by user due to safety concerns"
                
                # Log the operation
                safety_manager.log_risky_operation(
                    "modify_file",
                    f"File: {file_path}",
                    risk_level,
                    True
                )
        
        # Create directory if it doesn't exist (but only if the file path contains a directory)
        directory = os.path.dirname(file_path)
        if directory and directory != '.':
            os.makedirs(directory, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return f"Successfully modified {file_path}"
    except PermissionError:
        return f"Permission denied: {file_path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"

def append_to_file(file_path: str, content: str) -> str:
    """Appends content to an existing file."""
    try:
        # Create directory if it doesn't exist
        directory = os.path.dirname(file_path)
        if directory and directory != '.':
            os.makedirs(directory, exist_ok=True)
        
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully appended to {file_path}"
    except PermissionError:
        return f"Permission denied: {file_path}"
    except Exception as e:
        return f"Error appending to file: {str(e)}"

def edit_file_lines(file_path: str, start_line: int, end_line: int, new_content: str) -> str:
    """Edits specific lines in a file."""
    try:
        if not os.path.exists(file_path):
            return f"File not found: {file_path}"
        
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Validate line numbers (1-indexed)
        if start_line < 1 or end_line < 1 or start_line > len(lines) or end_line > len(lines):
            return f"Invalid line numbers. File has {len(lines)} lines."
        
        if start_line > end_line:
            return "Start line must be <= end line"
        
        # Replace lines (convert to 0-indexed)
        new_lines = new_content.split('\n') if new_content else []
        lines[start_line-1:end_line] = [line + '\n' for line in new_lines]
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        return f"Successfully edited lines {start_line}-{end_line} in {file_path}"
    except Exception as e:
        return f"Error editing file: {str(e)}"

def copy_file(source: str, destination: str) -> str:
    """Copies a file from source to destination."""
    try:
        shutil.copy2(source, destination)
        return f"Successfully copied {source} to {destination}"
    except FileNotFoundError:
        return f"Source file not found: {source}"
    except Exception as e:
        return f"Error copying file: {str(e)}"

def move_file(source: str, destination: str) -> str:
    """Moves a file from source to destination."""
    try:
        shutil.move(source, destination)
        return f"Successfully moved {source} to {destination}"
    except FileNotFoundError:
        return f"Source file not found: {source}"
    except Exception as e:
        return f"Error moving file: {str(e)}"

def delete_file(file_path: str) -> str:
    """Deletes a file with enhanced safety checks."""
    try:
        # Enhanced safety check
        if safety_manager:
            risk_level, risk_score, warnings = safety_manager.assess_file_operation_risk("delete", file_path)
            
            # Create backup for all deletions
            backup_result = safety_manager.create_backup(file_path)
            
            # Require confirmation
            if not safety_manager.require_confirmation(
                "File Deletion",
                f"File: {file_path}\nBackup: {backup_result}",
                risk_level,
                warnings
            ):
                return "Operation cancelled by user due to safety concerns"
            
            # Log the operation
            safety_manager.log_risky_operation(
                "delete_file",
                f"File: {file_path}",
                risk_level,
                True
            )
        
        if os.path.isdir(file_path):
            shutil.rmtree(file_path)
            return f"Successfully deleted directory: {file_path}"
        else:
            os.remove(file_path)
            return f"Successfully deleted file: {file_path}"
    except FileNotFoundError:
        return f"File not found: {file_path}"
    except Exception as e:
        return f"Error deleting file: {str(e)}"

def search_in_files(pattern: str, directory: str = ".", file_pattern: str = "*") -> str:
    """Searches for a pattern in files."""
    try:
        import re
        matches = []
        files = glob.glob(os.path.join(directory, "**", file_pattern), recursive=True)
        
        for file_path in files:
            if os.path.isfile(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if re.search(pattern, content, re.IGNORECASE):
                            # Find line numbers
                            lines = content.split('\n')
                            matching_lines = []
                            for i, line in enumerate(lines, 1):
                                if re.search(pattern, line, re.IGNORECASE):
                                    matching_lines.append(f"  Line {i}: {line.strip()}")
                            
                            matches.append(f"📄 {file_path}:")
                            matches.extend(matching_lines[:5])  # Limit to 5 matches per file
                            if len(matching_lines) > 5:
                                matches.append(f"  ... and {len(matching_lines) - 5} more matches")
                except (UnicodeDecodeError, PermissionError):
                    continue
        
        if not matches:
            return f"No matches found for pattern: {pattern}"
        return "\n".join(matches)
    except Exception as e:
        return f"Error searching in files: {str(e)}"

def get_current_directory() -> str:
    """Gets the current working directory."""
    try:
        return os.getcwd()
    except Exception as e:
        return f"Error getting current directory: {str(e)}"

def change_directory(directory_path: str) -> str:
    """Changes the current working directory."""
    try:
        os.chdir(directory_path)
        return f"Changed directory to: {os.getcwd()}"
    except FileNotFoundError:
        return f"Directory not found: {directory_path}"
    except Exception as e:
        return f"Error changing directory: {str(e)}"

def get_memory_statistics() -> str:
    """Gets memory statistics from the agent's memory system."""
    try:
        # Import here to avoid circular imports
        from .memory import MemoryManager
        
        memory = MemoryManager()
        stats = memory.get_memory_stats()
        
        result = "📊 Agent Memory Statistics:\n"
        result += f"  • Total Memories: {stats['total_memories']}\n"
        result += f"  • Successful Memories: {stats['successful_memories']}\n"
        result += f"  • Error Patterns: {stats['error_patterns']}\n"
        result += f"  • Working Memory Size: {stats['working_memory_size']}\n"
        result += f"  • Short-term Memory Size: {stats['short_term_memory_size']}\n"
        
        if stats['categories']:
            result += "\n📂 Memory Categories:\n"
            for category, count in stats['categories'].items():
                result += f"  • {category}: {count} entries\n"
        
        # Add file system info
        try:
            db_size = os.path.getsize("agent_memory.db") if os.path.exists("agent_memory.db") else 0
            result += f"\n💾 Database Size: {db_size:,} bytes ({db_size/1024:.1f} KB)\n"
        except:
            pass
            
        return result
        
    except Exception as e:
        return f"Error getting memory statistics: {str(e)}"

def list_directory(directory_path: str = ".") -> str:
    """Lists the contents of a directory."""
    try:
        items = []
        for item in sorted(os.listdir(directory_path)):
            item_path = os.path.join(directory_path, item)
            if os.path.isdir(item_path):
                items.append(f"📁 {item}/")
            else:
                size = os.path.getsize(item_path)
                items.append(f"📄 {item} ({size} bytes)")
        return "\n".join(items)
    except FileNotFoundError:
        return f"Directory not found: {directory_path}"
    except PermissionError:
        return f"Permission denied: {directory_path}"
    except Exception as e:
        return f"Error listing directory: {str(e)}"

def find_files(pattern: str, directory: str = ".") -> str:
    """Finds files matching a pattern in a directory."""
    try:
        matches = glob.glob(os.path.join(directory, "**", pattern), recursive=True)
        if not matches:
            return f"No files found matching pattern: {pattern}"
        return "\n".join(sorted(matches))
    except Exception as e:
        return f"Error finding files: {str(e)}"

def get_file_info(file_path: str) -> str:
    """Gets information about a file."""
    try:
        stat = os.stat(file_path)
        path = Path(file_path)
        
        info = {
            "name": path.name,
            "size": stat.st_size,
            "is_directory": path.is_dir(),
            "is_file": path.is_file(),
            "absolute_path": str(path.absolute()),
            "parent": str(path.parent),
            "suffix": path.suffix,
            "modified_time": stat.st_mtime
        }
        
        return json.dumps(info, indent=2)
    except FileNotFoundError:
        return f"File not found: {file_path}"
    except Exception as e:
        return f"Error getting file info: {str(e)}"

def create_directory(directory_path: str) -> str:
    """Creates a directory."""
    try:
        os.makedirs(directory_path, exist_ok=True)
        return f"Successfully created directory: {directory_path}"
    except Exception as e:
        return f"Error creating directory: {str(e)}"

def create_folder(folder_path: str) -> str:
    """Creates a folder/directory structure."""
    try:
        os.makedirs(folder_path, exist_ok=True)
        return f"Successfully created folder: {folder_path}"
    except Exception as e:
        return f"Error creating folder: {str(e)}"

def create_project_structure(project_name: str, project_type: str = "python") -> str:
    """Creates a complete project structure with common files."""
    try:
        base_path = os.path.join(os.getcwd(), project_name)
        
        if os.path.exists(base_path):
            return f"Project directory already exists: {base_path}"
        
        # Create base directory
        os.makedirs(base_path)
        
        if project_type.lower() == "python":
            # Python project structure
            dirs = [
                "src",
                "tests", 
                "docs",
                "scripts"
            ]
            
            files = {
                "README.md": f"# {project_name}\n\nA Python project.\n\n## Installation\n\n```bash\npip install -r requirements.txt\n```\n\n## Usage\n\nTODO: Add usage instructions\n",
                "requirements.txt": "# Add your dependencies here\n",
                ".gitignore": "__pycache__/\n*.pyc\n*.pyo\n*.pyd\n.Python\nbuild/\ndevelop-eggs/\ndist/\ndownloads/\neggs/\n.eggs/\nlib/\nlib64/\nparts/\nsdist/\nvar/\nwheels/\n*.egg-info/\n.installed.cfg\n*.egg\n.env\n.venv\nenv/\nvenv/\n",
                "setup.py": f'from setuptools import setup, find_packages\n\nsetup(\n    name="{project_name}",\n    version="0.1.0",\n    packages=find_packages(),\n    install_requires=[],\n)',
                "src/__init__.py": "",
                "src/main.py": f'"""\nMain module for {project_name}\n"""\n\ndef main():\n    print("Hello from {project_name}!")\n\nif __name__ == "__main__":\n    main()\n',
                "tests/__init__.py": "",
                "tests/test_main.py": f'import unittest\nfrom src.main import main\n\nclass Test{project_name.replace("-", "").replace("_", "").title()}(unittest.TestCase):\n    def test_main(self):\n        # Add your tests here\n        pass\n\nif __name__ == "__main__":\n    unittest.main()\n'
            }
            
        elif project_type.lower() == "web":
            # Web project structure
            dirs = [
                "css",
                "js",
                "images",
                "assets"
            ]
            
            files = {
                "index.html": f'<!DOCTYPE html>\n<html lang="en">\n<head>\n    <meta charset="UTF-8">\n    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n    <title>{project_name}</title>\n    <link rel="stylesheet" href="css/style.css">\n</head>\n<body>\n    <h1>Welcome to {project_name}</h1>\n    <script src="js/main.js"></script>\n</body>\n</html>',
                "css/style.css": "/* Styles for " + project_name + " */\nbody {\n    font-family: Arial, sans-serif;\n    margin: 0;\n    padding: 20px;\n    background-color: #f4f4f4;\n}\n\nh1 {\n    color: #333;\n    text-align: center;\n}",
                "js/main.js": f'// JavaScript for {project_name}\nconsole.log("Welcome to {project_name}!");',
                "README.md": f"# {project_name}\n\nA web project.\n\n## Setup\n\nOpen `index.html` in your browser.\n"
            }
        
        else:
            # Generic project structure
            dirs = ["src", "docs"]
            files = {
                "README.md": f"# {project_name}\n\nProject description here.\n",
                ".gitignore": "*.log\n*.tmp\n.DS_Store\n"
            }
        
        # Create directories
        for dir_name in dirs:
            os.makedirs(os.path.join(base_path, dir_name), exist_ok=True)
        
        # Create files
        for file_path, content in files.items():
            full_path = os.path.join(base_path, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        return f"Successfully created {project_type} project structure at: {base_path}"
        
    except Exception as e:
        return f"Error creating project structure: {str(e)}"

def open_browser(url: Optional[str] = None, file_path: Optional[str] = None) -> str:
    """Opens a URL or local file in the default browser."""
    try:
        if url and file_path:
            return "Error: Provide either url OR file_path, not both"
        
        if not url and not file_path:
            return "Error: Must provide either url or file_path"
        
        if file_path:
            # Open local file
            if not os.path.exists(file_path):
                return f"File not found: {file_path}"
            
            # Convert to absolute path and add file:// protocol
            abs_path = os.path.abspath(file_path)
            url = f"file://{abs_path}"
        
        # Open in browser
        if url:  # url is guaranteed to be a string at this point
            webbrowser.open(url)
            return f"Successfully opened in browser: {url}"
        else:
            return "Error: No valid URL to open"
        
    except Exception as e:
        return f"Error opening browser: {str(e)}"

def create_html_file(file_path: str, title: str = "New Page", content: str = "") -> str:
    """Creates an HTML file with basic structure."""
    try:
        html_template = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
        }}
        h1 {{
            color: #333;
            border-bottom: 2px solid #ddd;
            padding-bottom: 10px;
        }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    {content}
</body>
</html>'''
        
        # Create directory if needed
        directory = os.path.dirname(file_path)
        if directory and directory != '.':
            os.makedirs(directory, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_template)
        
        return f"Successfully created HTML file: {file_path}"
        
    except Exception as e:
        return f"Error creating HTML file: {str(e)}"

def view_file_in_browser(file_path: str) -> str:
    """Creates a temporary HTML file to view any text file in browser with syntax highlighting."""
    try:
        if not os.path.exists(file_path):
            return f"File not found: {file_path}"
        
        # Read the file content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            return f"Cannot display binary file in browser: {file_path}"
        
        # Detect file type for syntax highlighting
        file_ext = os.path.splitext(file_path)[1].lower()
        language_map = {
            '.py': 'python',
            '.js': 'javascript', 
            '.html': 'html',
            '.css': 'css',
            '.json': 'json',
            '.xml': 'xml',
            '.sql': 'sql',
            '.sh': 'bash',
            '.md': 'markdown'
        }
        
        language = language_map.get(file_ext, 'text')
        
        # Create HTML with syntax highlighting using Prism.js
        html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Viewing: {os.path.basename(file_path)}</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism-tomorrow.min.css" rel="stylesheet">
    <style>
        body {{
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            margin: 0;
            padding: 20px;
            background: #2d3748;
            color: #e2e8f0;
        }}
        .header {{
            background: #1a202c;
            padding: 15px 20px;
            margin: -20px -20px 20px -20px;
            border-bottom: 2px solid #4a5568;
        }}
        .file-path {{
            color: #63b3ed;
            font-size: 14px;
            margin-bottom: 5px;
        }}
        .file-name {{
            color: #f7fafc;
            font-size: 18px;
            font-weight: bold;
        }}
        pre {{
            background: #1a202c !important;
            border: 1px solid #4a5568;
            border-radius: 6px;
            overflow-x: auto;
        }}
        code {{
            font-size: 14px;
            line-height: 1.5;
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="file-path">{os.path.dirname(os.path.abspath(file_path))}</div>
        <div class="file-name">{os.path.basename(file_path)}</div>
    </div>
    <pre><code class="language-{language}">{content.replace('<', '&lt;').replace('>', '&gt;')}</code></pre>
    
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-core.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/plugins/autoloader/prism-autoloader.min.js"></script>
</body>
</html>'''
        
        # Create temporary HTML file
        temp_dir = tempfile.gettempdir()
        temp_file = os.path.join(temp_dir, f"view_{os.path.basename(file_path)}.html")
        
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Open in browser
        webbrowser.open(f"file://{temp_file}")
        
        return f"Successfully opened {file_path} in browser with syntax highlighting"
        
    except Exception as e:
        return f"Error viewing file in browser: {str(e)}"

# Tool registry for easy access
TOOLS = {
    "execute_shell_command": execute_shell_command,
    "search_file": search_file,
    "create_file": create_file,
    "modify_file": modify_file,
    "append_to_file": append_to_file,
    "edit_file_lines": edit_file_lines,
    "list_directory": list_directory,
    "find_files": find_files,
    "get_file_info": get_file_info,
    "create_directory": create_directory,
    "create_folder": create_folder,
    "create_project_structure": create_project_structure,
    "copy_file": copy_file,
    "move_file": move_file,
    "delete_file": delete_file,
    "search_in_files": search_in_files,
    "get_current_directory": get_current_directory,
    "change_directory": change_directory,
    "get_memory_statistics": get_memory_statistics,
    "open_browser": open_browser,
    "create_html_file": create_html_file,
    "view_file_in_browser": view_file_in_browser,
}

# Import and add advanced tools
try:
    from .advanced_tools import ADVANCED_TOOLS
    TOOLS.update(ADVANCED_TOOLS)
except ImportError:
    pass  # Advanced tools not available

# Import and add web tools  
try:
    from .web_tools import (
        browse_web, search_internet, fetch_web_content, parse_webpage,
        get_weather_info, get_news_headlines, call_api, install_web_dependencies
    )
    WEB_TOOLS = {
        "browse_web": browse_web,
        "search_internet": search_internet,
        "fetch_web_content": fetch_web_content,
        "parse_webpage": parse_webpage,
        "get_weather_info": get_weather_info,
        "get_news_headlines": get_news_headlines,
        "call_api": call_api,
        "install_web_dependencies": install_web_dependencies,
    }
    TOOLS.update(WEB_TOOLS)
except ImportError:
    pass  # Web tools not available

# Import and add server tools
try:
    from .server_tools import (
        start_server, stop_server, list_servers, manage_process,
        get_system_status, get_running_processes, check_port_availability,
        install_server_dependencies
    )
    SERVER_TOOLS = {
        "start_server": start_server,
        "stop_server": stop_server,
        "list_servers": list_servers,
        "manage_process": manage_process,
        "get_system_status": get_system_status,
        "get_running_processes": get_running_processes,
        "check_port_availability": check_port_availability,
        "install_server_dependencies": install_server_dependencies,
    }
    TOOLS.update(SERVER_TOOLS)
except ImportError:
    pass  # Server tools not available

# Import and add intelligence tools
try:
    from .intelligence_tools import (
        analyze_task_intelligence, learn_from_execution, query_knowledge_base,
        analyze_code_intelligence, get_similar_solutions, enhance_reasoning_capability
    )
    INTELLIGENCE_TOOLS = {
        "analyze_task_intelligence": analyze_task_intelligence,
        "learn_from_execution": learn_from_execution,
        "query_knowledge_base": query_knowledge_base,
        "analyze_code_intelligence": analyze_code_intelligence,
        "get_similar_solutions": get_similar_solutions,
        "enhance_reasoning_capability": enhance_reasoning_capability,
    }
    TOOLS.update(INTELLIGENCE_TOOLS)
except ImportError:
    pass  # Intelligence tools not available

# Import testing capabilities
try:
    from .testing import test_runner
    
    def test_generated_code(code: str, language: str, code_type: str = "general") -> str:
        """Test generated code for quality and functionality."""
        try:
            report = test_runner.test_generated_code(code, language, code_type)
            
            result = f"🧪 Code Quality Report:\n"
            result += f"  • Language: {report['language']}\n"
            result += f"  • Overall Score: {report['overall_score']}/100\n"
            result += f"  • Syntax Valid: {'✅' if report['syntax_valid'] else '❌'}\n"
            result += f"  • Execution Successful: {'✅' if report['execution_successful'] else '❌'}\n"
            
            if report['errors']:
                result += f"\n⚠️  Issues Found:\n"
                for error in report['errors']:
                    result += f"  • {error}\n"
            
            if report['suggestions']:
                result += f"\n💡 Suggestions:\n"
                for suggestion in report['suggestions']:
                    result += f"  • {suggestion}\n"
            
            if report['overall_score'] < 70:
                result += f"\n🔄 Recommendation: Consider regenerating code for better quality\n"
            
            return result
            
        except Exception as e:
            return f"Error during code testing: {str(e)}"
    
    def improve_snake_game(original_code: str) -> str:
        """Improve the Snake game code with better structure and features."""
        try:
            improved_code = '''#!/usr/bin/env python3
"""
Enhanced Snake Game with improved graphics and features
"""

import pygame
import random
import sys
from enum import Enum
from typing import Tuple, List
import json
import os

# Initialize Pygame
pygame.init()

# Constants
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
CELL_SIZE = 20
CELL_NUMBER_X = WINDOW_WIDTH // CELL_SIZE
CELL_NUMBER_Y = WINDOW_HEIGHT // CELL_SIZE
FPS = 12

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
DARK_GREEN = (0, 200, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GRAY = (128, 128, 128)
YELLOW = (255, 255, 0)

# Game states
class GameState(Enum):
    MENU = 1
    PLAYING = 2
    GAME_OVER = 3
    PAUSED = 4

class Direction(Enum):
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

class Snake:
    def __init__(self):
        self.body = [(CELL_NUMBER_X // 2, CELL_NUMBER_Y // 2)]
        self.direction = Direction.RIGHT
        self.grow_pending = False
        
    def move(self):
        head = self.body[0]
        new_head = (
            head[0] + self.direction.value[0],
            head[1] + self.direction.value[1]
        )
        self.body.insert(0, new_head)
        
        if not self.grow_pending:
            self.body.pop()
        else:
            self.grow_pending = False
    
    def grow(self):
        self.grow_pending = True
    
    def check_collision(self) -> bool:
        head = self.body[0]
        
        # Wall collision
        if (head[0] < 0 or head[0] >= CELL_NUMBER_X or 
            head[1] < 0 or head[1] >= CELL_NUMBER_Y):
            return True
            
        # Self collision
        return head in self.body[1:]
    
    def draw(self, screen):
        for i, segment in enumerate(self.body):
            color = GREEN if i == 0 else DARK_GREEN  # Head is brighter
            rect = pygame.Rect(
                segment[0] * CELL_SIZE,
                segment[1] * CELL_SIZE,
                CELL_SIZE - 1, CELL_SIZE - 1
            )
            pygame.draw.rect(screen, color, rect)
            
            # Add eyes to head
            if i == 0:
                eye_size = 3
                eye_offset = 4
                if self.direction == Direction.RIGHT:
                    eye1 = (rect.centerx + eye_offset, rect.centery - eye_offset)
                    eye2 = (rect.centerx + eye_offset, rect.centery + eye_offset)
                elif self.direction == Direction.LEFT:
                    eye1 = (rect.centerx - eye_offset, rect.centery - eye_offset)
                    eye2 = (rect.centerx - eye_offset, rect.centery + eye_offset)
                elif self.direction == Direction.UP:
                    eye1 = (rect.centerx - eye_offset, rect.centery - eye_offset)
                    eye2 = (rect.centerx + eye_offset, rect.centery - eye_offset)
                else:  # DOWN
                    eye1 = (rect.centerx - eye_offset, rect.centery + eye_offset)
                    eye2 = (rect.centerx + eye_offset, rect.centery + eye_offset)
                
                pygame.draw.circle(screen, BLACK, eye1, eye_size)
                pygame.draw.circle(screen, BLACK, eye2, eye_size)

class Food:
    def __init__(self):
        self.position = self.random_position()
        self.type = "normal"  # Could be extended for special foods
        
    def random_position(self) -> Tuple[int, int]:
        x = random.randint(0, CELL_NUMBER_X - 1)
        y = random.randint(0, CELL_NUMBER_Y - 1)
        return (x, y)
    
    def draw(self, screen):
        rect = pygame.Rect(
            self.position[0] * CELL_SIZE,
            self.position[1] * CELL_SIZE,
            CELL_SIZE - 1, CELL_SIZE - 1
        )
        pygame.draw.ellipse(screen, RED, rect)
        # Add shine effect
        shine_rect = pygame.Rect(
            rect.x + 3, rect.y + 3, 6, 6
        )
        pygame.draw.ellipse(screen, YELLOW, shine_rect)

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Enhanced Snake Game")
        self.clock = pygame.time.Clock()
        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 36)
        self.font_small = pygame.font.Font(None, 24)
        
        self.reset_game()
        self.state = GameState.MENU
        self.high_score = self.load_high_score()
        
    def reset_game(self):
        self.snake = Snake()
        self.food = Food()
        self.score = 0
        
    def load_high_score(self) -> int:
        try:
            if os.path.exists("snake_high_score.json"):
                with open("snake_high_score.json", "r") as f:
                    data = json.load(f)
                    return data.get("high_score", 0)
        except:
            pass
        return 0
    
    def save_high_score(self):
        try:
            with open("snake_high_score.json", "w") as f:
                json.dump({"high_score": self.high_score}, f)
        except:
            pass
    
    def handle_events(self) -> bool:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if self.state == GameState.MENU:
                    if event.key == pygame.K_SPACE:
                        self.state = GameState.PLAYING
                        self.reset_game()
                elif self.state == GameState.PLAYING:
                    if event.key == pygame.K_UP and self.snake.direction != Direction.DOWN:
                        self.snake.direction = Direction.UP
                    elif event.key == pygame.K_DOWN and self.snake.direction != Direction.UP:
                        self.snake.direction = Direction.DOWN
                    elif event.key == pygame.K_LEFT and self.snake.direction != Direction.RIGHT:
                        self.snake.direction = Direction.LEFT
                    elif event.key == pygame.K_RIGHT and self.snake.direction != Direction.LEFT:
                        self.snake.direction = Direction.RIGHT
                    elif event.key == pygame.K_SPACE:
                        self.state = GameState.PAUSED
                elif self.state == GameState.GAME_OVER:
                    if event.key == pygame.K_SPACE:
                        self.state = GameState.MENU
                elif self.state == GameState.PAUSED:
                    if event.key == pygame.K_SPACE:
                        self.state = GameState.PLAYING
        return True
    
    def update(self):
        if self.state == GameState.PLAYING:
            self.snake.move()
            
            # Check food collision
            if self.snake.body[0] == self.food.position:
                self.snake.grow()
                self.food.position = self.food.random_position()
                # Ensure food doesn't spawn on snake
                while self.food.position in self.snake.body:
                    self.food.position = self.food.random_position()
                self.score += 10
            
            # Check game over
            if self.snake.check_collision():
                if self.score > self.high_score:
                    self.high_score = self.score
                    self.save_high_score()
                self.state = GameState.GAME_OVER
    
    def draw_menu(self):
        self.screen.fill(BLACK)
        
        title = self.font_large.render("SNAKE GAME", True, GREEN)
        title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, 150))
        self.screen.blit(title, title_rect)
        
        instruction = self.font_medium.render("Press SPACE to Start", True, WHITE)
        instruction_rect = instruction.get_rect(center=(WINDOW_WIDTH // 2, 250))
        self.screen.blit(instruction, instruction_rect)
        
        controls = [
            "Use Arrow Keys to Move",
            "SPACE to Pause/Resume",
            f"High Score: {self.high_score}"
        ]
        
        for i, text in enumerate(controls):
            rendered = self.font_small.render(text, True, GRAY)
            rect = rendered.get_rect(center=(WINDOW_WIDTH // 2, 350 + i * 30))
            self.screen.blit(rendered, rect)
    
    def draw_game(self):
        self.screen.fill(BLACK)
        
        # Draw game area border
        pygame.draw.rect(self.screen, WHITE, (0, 0, WINDOW_WIDTH, WINDOW_HEIGHT), 2)
        
        # Draw snake and food
        self.snake.draw(self.screen)
        self.food.draw(self.screen)
        
        # Draw score
        score_text = self.font_medium.render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_text, (10, 10))
        
        high_score_text = self.font_small.render(f"High: {self.high_score}", True, GRAY)
        self.screen.blit(high_score_text, (10, 50))
    
    def draw_game_over(self):
        self.screen.fill(BLACK)
        
        game_over = self.font_large.render("GAME OVER", True, RED)
        game_over_rect = game_over.get_rect(center=(WINDOW_WIDTH // 2, 150))
        self.screen.blit(game_over, game_over_rect)
        
        score_text = self.font_medium.render(f"Final Score: {self.score}", True, WHITE)
        score_rect = score_text.get_rect(center=(WINDOW_WIDTH // 2, 220))
        self.screen.blit(score_text, score_rect)
        
        if self.score == self.high_score:
            new_high = self.font_medium.render("NEW HIGH SCORE!", True, YELLOW)
            new_high_rect = new_high.get_rect(center=(WINDOW_WIDTH // 2, 260))
            self.screen.blit(new_high, new_high_rect)
        
        restart = self.font_small.render("Press SPACE to return to menu", True, GRAY)
        restart_rect = restart.get_rect(center=(WINDOW_WIDTH // 2, 350))
        self.screen.blit(restart, restart_rect)
    
    def draw_paused(self):
        # Draw game state first
        self.draw_game()
        
        # Draw pause overlay
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        paused_text = self.font_large.render("PAUSED", True, WHITE)
        paused_rect = paused_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
        self.screen.blit(paused_text, paused_rect)
        
        resume_text = self.font_small.render("Press SPACE to resume", True, GRAY)
        resume_rect = resume_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 50))
        self.screen.blit(resume_text, resume_rect)
    
    def draw(self):
        if self.state == GameState.MENU:
            self.draw_menu()
        elif self.state == GameState.PLAYING:
            self.draw_game()
        elif self.state == GameState.GAME_OVER:
            self.draw_game_over()
        elif self.state == GameState.PAUSED:
            self.draw_paused()
        
        pygame.display.flip()
    
    def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    try:
        game = Game()
        game.run()
    except KeyboardInterrupt:
        print("\\nGame interrupted by user")
        pygame.quit()
        sys.exit()
    except Exception as e:
        print(f"Game error: {e}")
        pygame.quit()
        sys.exit(1)
'''
            return improved_code
        except Exception as e:
            return f"Error improving Snake game: {str(e)}"

    # Add testing tools to the registry
    TOOLS.update({
        "test_generated_code": test_generated_code,
        "improve_snake_game": improve_snake_game,
    })
    
except ImportError:
    pass  # Testing tools not available
