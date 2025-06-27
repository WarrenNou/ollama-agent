"""
Advanced tools for code generation, project management, and development workflows.
"""

import os
import json
import subprocess
import webbrowser
import tempfile
from typing import Dict, List, Any, Optional
from pathlib import Path


def generate_code_template(language: str, template_type: str, name: str = "example") -> str:
    """Generate code templates for common patterns."""
    try:
        templates = {
            "python": {
                "class": f'''class {name.title()}:
    """A sample class."""
    
    def __init__(self, name: str):
        self.name = name
    
    def __str__(self) -> str:
        return f"{{self.__class__.__name__}}(name={{{{self.name}}}})"
    
    def greet(self) -> str:
        """Return a greeting message."""
        return f"Hello from {{{{self.name}}}}!"


# Example usage
if __name__ == "__main__":
    obj = {name.title()}("{name}")
    print(obj.greet())
''',
                
                "function": f'''def {name}(param1: str, param2: int = 0) -> str:
    """
    A sample function that demonstrates best practices.
    
    Args:
        param1: A string parameter
        param2: An integer parameter with default value
    
    Returns:
        A formatted string result
    
    Raises:
        ValueError: If param1 is empty
    """
    if not param1:
        raise ValueError("param1 cannot be empty")
    
    return f"{{{{param1}}}} processed with value {{{{param2}}}}"


# Example usage
if __name__ == "__main__":
    result = {name}("test", 42)
    print(result)
''',
                
                "api": f'''from flask import Flask, jsonify, request
from typing import Dict, Any

app = Flask(__name__)

@app.route('/api/{name}', methods=['GET'])
def get_{name}() -> Dict[str, Any]:
    """Get {name} data."""
    return jsonify({{"message": "Hello from {name} API!", "status": "success"}})

@app.route('/api/{name}', methods=['POST'])
def create_{name}() -> Dict[str, Any]:
    """Create new {name}."""
    data = request.get_json()
    # Process data here
    return jsonify({{"message": "{name} created", "data": data}})

@app.route('/health', methods=['GET'])
def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return jsonify({{"status": "healthy"}})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
''',

                "test": f'''import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add src to path if needed
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

class Test{name.title()}(unittest.TestCase):
    """Test cases for {name}."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        pass
    
    def tearDown(self):
        """Clean up after each test method."""
        pass
    
    def test_{name}_basic(self):
        """Test basic functionality."""
        # Arrange
        expected = "test result"
        
        # Act
        # result = your_function_here()
        
        # Assert
        # self.assertEqual(result, expected)
        pass
    
    @patch('your_module.external_dependency')
    def test_{name}_with_mock(self, mock_dependency):
        """Test with mocked dependencies."""
        # Arrange
        mock_dependency.return_value = "mocked result"
        
        # Act & Assert
        pass
    
    def test_{name}_edge_case(self):
        """Test edge cases."""
        # Test with None, empty strings, edge values
        pass

if __name__ == '__main__':
    unittest.main()
''',
            },
            
            "javascript": {
                "function": f'''/**
 * {name} - A sample JavaScript function
 * @param {{string}} param1 - First parameter
 * @param {{number}} param2 - Second parameter
 * @returns {{string}} Formatted result
 */
function {name}(param1, param2 = 0) {{
    if (!param1) {{
        throw new Error('param1 is required');
    }}
    
    return `${{{{param1}}}} processed with value ${{{{param2}}}}`;
}}

// Example usage
try {{
    const result = {name}('test', 42);
    console.log(result);
}} catch (error) {{
    console.error('Error:', error.message);
}}

module.exports = {name};
''',
                
                "class": f'''/**
 * {name.title()} class
 */
class {name.title()} {{
    constructor(name) {{
        this.name = name;
    }}
    
    greet() {{
        return `Hello from ${{{{this.name}}}}!`;
    }}
    
    toString() {{
        return `{name.title()}(name=${{{{this.name}}}})`;
    }}
}}

// Example usage
const obj = new {name.title()}('{name}');
console.log(obj.greet());

module.exports = {name.title()};
''',
                
                "react": f'''import React, {{ useState, useEffect }} from 'react';

/**
 * {name.title()} component
 */
const {name.title()} = ({{ title = "{name.title()}" }}) => {{
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    
    useEffect(() => {{
        // Fetch data on component mount
        const fetchData = async () => {{
            setLoading(true);
            try {{
                // Replace with actual API call
                const response = await fetch('/api/{name}');
                const result = await response.json();
                setData(result);
            }} catch (err) {{
                setError(err.message);
            }} finally {{
                setLoading(false);
            }}
        }};
        
        fetchData();
    }}, []);
    
    if (loading) return <div>Loading...</div>;
    if (error) return <div>Error: {{error}}</div>;
    
    return (
        <div className="{name}-container">
            <h1>{{title}}</h1>
            {{data && (
                <div className="{name}-content">
                    <pre>{{JSON.stringify(data, null, 2)}}</pre>
                </div>
            )}}
        </div>
    );
}};

export default {name.title()};
''',
            },
            
            "html": {
                "page": f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{name.title()}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
        }}
        .header {{
            background: #f4f4f4;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}
        .content {{
            background: white;
            padding: 20px;
            border: 1px solid #ddd;
            border-radius: 5px;
        }}
        button {{
            background: #007cba;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }}
        button:hover {{
            background: #005a8b;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{name.title()}</h1>
        <p>Welcome to your new page!</p>
    </div>
    
    <div class="content">
        <h2>Getting Started</h2>
        <p>This is a template page. Customize it as needed.</p>
        <button onclick="handleClick()">Click Me</button>
    </div>
    
    <script>
        function handleClick() {{
            alert('Hello from {name}!');
        }}
        
        console.log('{name} page loaded');
    </script>
</body>
</html>
''',
            }
        }
        
        if language not in templates:
            return f"Language '{language}' not supported. Available: {list(templates.keys())}"
        
        if template_type not in templates[language]:
            return f"Template type '{template_type}' not available for {language}. Available: {list(templates[language].keys())}"
        
        return templates[language][template_type]
        
    except Exception as e:
        return f"Error generating template: {str(e)}"


def create_development_server(project_path: str, server_type: str = "python") -> str:
    """Create and start a development server for the project."""
    try:
        if not os.path.exists(project_path):
            return f"Project path not found: {project_path}"
        
        server_commands = {
            "python": "python -m http.server 8000",
            "node": "npx serve -s . -l 3000",
            "php": "php -S localhost:8080",
            "python-flask": "python app.py",
            "live-server": "npx live-server --port=8080"
        }
        
        if server_type not in server_commands:
            return f"Server type '{server_type}' not supported. Available: {list(server_commands.keys())}"
        
        command = server_commands[server_type]
        
        # Create a batch script to run the server
        if os.name == 'nt':  # Windows
            script_path = os.path.join(project_path, "start_server.bat")
            with open(script_path, 'w') as f:
                f.write(f"@echo off\ncd /d {project_path}\n{command}\npause\n")
        else:  # Unix-like
            script_path = os.path.join(project_path, "start_server.sh")
            with open(script_path, 'w') as f:
                f.write(f"#!/bin/bash\ncd {project_path}\n{command}\n")
            os.chmod(script_path, 0o755)
        
        return f"Created server script: {script_path}\\nTo start: Run the script or execute '{command}' in {project_path}"
        
    except Exception as e:
        return f"Error creating development server: {str(e)}"


def analyze_project_structure(project_path: str) -> str:
    """Analyze a project structure and provide insights."""
    try:
        if not os.path.exists(project_path):
            return f"Project path not found: {project_path}"
        
        analysis = {
            "summary": {},
            "files_by_type": {},
            "potential_issues": [],
            "suggestions": []
        }
        
        total_files = 0
        total_size = 0
        
        for root, dirs, files in os.walk(project_path):
            # Skip hidden directories and common build/cache dirs
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'build', 'dist']]
            
            for file in files:
                if file.startswith('.'):
                    continue
                    
                file_path = os.path.join(root, file)
                try:
                    size = os.path.getsize(file_path)
                    total_files += 1
                    total_size += size
                    
                    ext = os.path.splitext(file)[1].lower()
                    if ext:
                        analysis["files_by_type"][ext] = analysis["files_by_type"].get(ext, 0) + 1
                    else:
                        analysis["files_by_type"]["no_extension"] = analysis["files_by_type"].get("no_extension", 0) + 1
                        
                except OSError:
                    continue
        
        analysis["summary"] = {
            "total_files": total_files,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2)
        }
        
        # Detect project type
        project_indicators = {
            "Python": ["requirements.txt", "setup.py", "pyproject.toml", "Pipfile"],
            "Node.js": ["package.json", "package-lock.json", "yarn.lock"],
            "Web": ["index.html", "index.htm"],
            "Django": ["manage.py", "settings.py"],
            "Flask": ["app.py", "application.py"],
            "React": ["package.json", "src/App.js", "public/index.html"],
            "Vue": ["vue.config.js", "src/main.js"],
            "Java": ["pom.xml", "build.gradle", "src/main/java"],
            "C/C++": ["Makefile", "CMakeLists.txt"],
            "Rust": ["Cargo.toml"],
            "Go": ["go.mod", "main.go"]
        }
        
        detected_types = []
        for project_type, indicators in project_indicators.items():
            for indicator in indicators:
                if os.path.exists(os.path.join(project_path, indicator)):
                    detected_types.append(project_type)
                    break
        
        analysis["detected_project_types"] = detected_types
        
        # Check for common issues
        if not os.path.exists(os.path.join(project_path, "README.md")):
            analysis["potential_issues"].append("Missing README.md file")
        
        if not os.path.exists(os.path.join(project_path, ".gitignore")):
            analysis["potential_issues"].append("Missing .gitignore file")
        
        # Large files
        for root, dirs, files in os.walk(project_path):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    if os.path.getsize(file_path) > 10 * 1024 * 1024:  # 10MB
                        analysis["potential_issues"].append(f"Large file: {file_path}")
                except OSError:
                    continue
        
        # Generate suggestions
        if ".py" in analysis["files_by_type"] and not any("Python" in t for t in detected_types):
            analysis["suggestions"].append("Consider adding requirements.txt or pyproject.toml for Python dependency management")
        
        if ".js" in analysis["files_by_type"] and not any("Node" in t for t in detected_types):
            analysis["suggestions"].append("Consider adding package.json for JavaScript dependency management")
        
        # Format output
        result = f"📊 Project Analysis: {os.path.basename(project_path)}\\n\\n"
        result += f"📈 Summary:\\n"
        result += f"  • Total Files: {analysis['summary']['total_files']}\\n"
        result += f"  • Total Size: {analysis['summary']['total_size_mb']} MB\\n"
        
        if detected_types:
            result += f"\\n🔍 Detected Project Types: {', '.join(detected_types)}\\n"
        
        result += f"\\n📁 File Types:\\n"
        for ext, count in sorted(analysis["files_by_type"].items()):
            result += f"  • {ext or 'no extension'}: {count} files\\n"
        
        if analysis["potential_issues"]:
            result += f"\\n⚠️  Potential Issues:\\n"
            for issue in analysis["potential_issues"]:
                result += f"  • {issue}\\n"
        
        if analysis["suggestions"]:
            result += f"\\n💡 Suggestions:\\n"
            for suggestion in analysis["suggestions"]:
                result += f"  • {suggestion}\\n"
        
        return result
        
    except Exception as e:
        return f"Error analyzing project: {str(e)}"


def setup_git_repository(project_path: str, remote_url: Optional[str] = None) -> str:
    """Initialize git repository and optionally add remote."""
    try:
        if not os.path.exists(project_path):
            return f"Project path not found: {project_path}"
        
        # Change to project directory
        original_dir = os.getcwd()
        os.chdir(project_path)
        
        try:
            # Initialize git repo
            result = subprocess.run(["git", "init"], capture_output=True, text=True)
            if result.returncode != 0:
                return f"Failed to initialize git: {result.stderr}"
            
            output = "✅ Initialized git repository\\n"
            
            # Create .gitignore if it doesn't exist
            gitignore_path = os.path.join(project_path, ".gitignore")
            if not os.path.exists(gitignore_path):
                gitignore_content = """# Common files to ignore
*.log
*.tmp
*.temp
.DS_Store
Thumbs.db

# Editor files
.vscode/
.idea/
*.swp
*.swo

# OS generated files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db
"""
                with open(gitignore_path, 'w') as f:
                    f.write(gitignore_content)
                output += "✅ Created .gitignore\\n"
            
            # Add remote if provided
            if remote_url:
                result = subprocess.run(["git", "remote", "add", "origin", remote_url], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    output += f"✅ Added remote origin: {remote_url}\\n"
                else:
                    output += f"⚠️  Failed to add remote: {result.stderr}\\n"
            
            # Initial commit
            subprocess.run(["git", "add", "."], capture_output=True)
            result = subprocess.run(["git", "commit", "-m", "Initial commit"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                output += "✅ Created initial commit\\n"
            
            return output
            
        finally:
            os.chdir(original_dir)
            
    except Exception as e:
        return f"Error setting up git repository: {str(e)}"


def create_docker_setup(project_path: str, project_type: str = "python") -> str:
    """Create Docker setup for a project."""
    try:
        if not os.path.exists(project_path):
            return f"Project path not found: {project_path}"
        
        dockerfiles = {
            "python": '''FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "app.py"]
''',
            
            "node": '''FROM node:16-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY . .

EXPOSE 3000

CMD ["npm", "start"]
''',
            
            "web": '''FROM nginx:alpine

COPY . /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
'''
        }
        
        docker_compose = f'''version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - .:/app
    environment:
      - ENV=development
'''
        
        if project_type not in dockerfiles:
            return f"Project type '{project_type}' not supported for Docker. Available: {list(dockerfiles.keys())}"
        
        # Create Dockerfile
        dockerfile_path = os.path.join(project_path, "Dockerfile")
        with open(dockerfile_path, 'w') as f:
            f.write(dockerfiles[project_type])
        
        # Create docker-compose.yml
        compose_path = os.path.join(project_path, "docker-compose.yml")
        with open(compose_path, 'w') as f:
            f.write(docker_compose)
        
        # Create .dockerignore
        dockerignore_path = os.path.join(project_path, ".dockerignore")
        dockerignore_content = """node_modules
npm-debug.log
.git
.gitignore
README.md
.env
.nyc_output
coverage
.cache
"""
        with open(dockerignore_path, 'w') as f:
            f.write(dockerignore_content)
        
        return f"✅ Created Docker setup for {project_type} project:\\n• Dockerfile\\n• docker-compose.yml\\n• .dockerignore"
        
    except Exception as e:
        return f"Error creating Docker setup: {str(e)}"


def run_code_quality_check(project_path: str, language: str = "python") -> str:
    """Run code quality checks on a project."""
    try:
        if not os.path.exists(project_path):
            return f"Project path not found: {project_path}"
        
        original_dir = os.getcwd()
        os.chdir(project_path)
        
        try:
            results = []
            
            if language == "python":
                # Check if tools are available
                tools = {
                    "flake8": "flake8 --max-line-length=88 --extend-ignore=E203,W503 .",
                    "black": "black --check --diff .",
                    "isort": "isort --check-only --diff .",
                    "mypy": "mypy ."
                }
                
                for tool, command in tools.items():
                    try:
                        result = subprocess.run(command.split(), capture_output=True, text=True, timeout=30)
                        if result.returncode == 0:
                            results.append(f"✅ {tool}: No issues found")
                        else:
                            results.append(f"⚠️  {tool}: Issues found\\n{result.stdout[:500]}")
                    except (subprocess.TimeoutExpired, FileNotFoundError):
                        results.append(f"❌ {tool}: Not installed or timed out")
                        
            elif language == "javascript":
                tools = {
                    "eslint": "npx eslint .",
                    "prettier": "npx prettier --check ."
                }
                
                for tool, command in tools.items():
                    try:
                        result = subprocess.run(command.split(), capture_output=True, text=True, timeout=30)
                        if result.returncode == 0:
                            results.append(f"✅ {tool}: No issues found")
                        else:
                            results.append(f"⚠️  {tool}: Issues found\\n{result.stdout[:500]}")
                    except (subprocess.TimeoutExpired, FileNotFoundError):
                        results.append(f"❌ {tool}: Not installed or timed out")
            
            return "🔍 Code Quality Check Results:\\n\\n" + "\\n\\n".join(results)
            
        finally:
            os.chdir(original_dir)
            
    except Exception as e:
        return f"Error running code quality check: {str(e)}"


# Add to existing TOOLS dictionary
ADVANCED_TOOLS = {
    "generate_code_template": generate_code_template,
    "create_development_server": create_development_server,
    "analyze_project_structure": analyze_project_structure,
    "setup_git_repository": setup_git_repository,
    "create_docker_setup": create_docker_setup,
    "run_code_quality_check": run_code_quality_check,
}
