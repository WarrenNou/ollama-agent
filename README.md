# 🤖 Ultimate AI CLI Agent

The most advanced intelligent CLI agent that uses local Ollama models to execute development tasks through natural language commands. Now featuring internet access, browser automation, server management, enhanced AI intelligence, and full terminal control.

## 🚀 Ultra-Quick Start

```bash
pip install ollama-agent
ollama-agent
```

**That's it!** The agent automatically installs and configures everything you need on first run.

### What Happens Automatically

On first run, the agent will:
- ✅ **Detect missing prerequisites** and offer to install them
- ✅ **Download and install Ollama** if not present
- ✅ **Start the Ollama service** automatically  
- ✅ **Download the default model** (llama3)
- ✅ **Install enhanced capabilities** (web tools, server management)
- ✅ **Verify everything works** and guide you through first steps

## ✨ Ultimate AI CLI Features

### 🌐 Internet Access & Web Browsing
- **Real-time Web Search**: Search the internet for current information
- **Web Scraping**: Extract data from any website
- **Browser Automation**: Control browsers, click elements, fill forms
- **API Integration**: Call REST APIs, fetch weather, news, and more
- **Web Development**: Test websites, debug issues, monitor performance

### 🖥️ Browser Automation & Control
- **Selenium Integration**: Full browser control with Chrome/Firefox
- **Element Interaction**: Click buttons, fill forms, navigate pages
- **Screenshot Capture**: Take screenshots of web pages
- **JavaScript Execution**: Run custom JavaScript in browser context
- **Visual Testing**: Automated UI testing and validation

### 🚀 Server Management & Process Control
- **Multi-Server Support**: HTTP, Flask, Node.js, Django, React, Vue
- **Development Servers**: Auto-detect and start project-specific dev servers
- **Process Management**: Start, stop, monitor background processes
- **Port Management**: Check availability, resolve conflicts
- **System Monitoring**: Real-time CPU, memory, disk usage tracking

### 🧠 Enhanced AI Intelligence
- **Adaptive Reasoning**: Multiple reasoning strategies (sequential, parallel, recursive)
- **Task Complexity Analysis**: Automatic complexity scoring and step estimation
- **Learning from Experience**: Remembers successful patterns and failures
- **Code Intelligence**: Advanced code analysis with improvement suggestions
- **Knowledge Base**: Persistent learning and knowledge retention

### 🔧 Full Terminal & System Control
- **Enhanced Shell Execution**: Run any command with intelligent error handling
- **File System Operations**: Advanced file management with safety checks
- **Project Scaffolding**: Generate complete project structures instantly
- **Git Integration**: Full version control support
- **Package Management**: Install and manage dependencies automatically

### 🛡️ Advanced Safety & Reliability
- **Risk Assessment**: Multi-level analysis of all operations
- **Automatic Backups**: Created before any risky file modifications
- **Graduated Confirmations**: Different safety levels for different operations
- **Audit Logging**: Complete record of all operations for compliance
- **Recovery Mechanisms**: Automatic error detection and recovery

## 📋 Example Commands

### Internet & Web Operations
```bash
# Search the internet
"Search for the latest Python web frameworks"

# Browse and analyze a website
"Go to github.com and find trending Python repositories"

# Get real-time data
"Get current weather for San Francisco"
"Fetch latest tech news headlines"

# Web scraping
"Extract all product prices from this e-commerce page"
```

### Server & Development
```bash
# Start various servers
"Start a Flask development server on port 5000"
"Launch a React development server"
"Create and run an HTTP server for this directory"

# Process management
"Show all running Python processes"
"Kill the process running on port 3000"
"Monitor system resource usage"
```

### Advanced Development
```bash
# Intelligent project creation
"Create a full-stack web application with Python backend and React frontend"

# Code analysis and improvement
"Analyze this Python file and suggest improvements"
"Review my JavaScript code for best practices"

# Complex automation
"Set up a CI/CD pipeline for this project"
"Deploy this Flask app to production"
```

### Smart Problem Solving
```bash
# Learning and adaptation
"I'm getting CORS errors, help me fix them"
"My React app won't build, diagnose and fix the issues"

# Research and implementation
"Research the best authentication methods for REST APIs and implement one"
"Find and integrate a payment processing solution for my e-commerce site"
```
- **Browser Integration**: View files with syntax highlighting in your browser

## ✨ Features

### 🛠️ Comprehensive Tool Set
- **File Operations**: Read, write, copy, move, delete files and directories
- **Shell Commands**: Execute system commands with safety confirmations
- **File Search**: Find files by name patterns or search content within files
- **Directory Management**: Navigate, list, and manage directory structures
- **Content Analysis**: Analyze file contents, metadata, and project structures

### 🔒 Safety Features
- Interactive confirmations for destructive operations
- Dangerous command detection and warnings
- File diff previews before modifications
- Step-by-step execution with user control
- Timeout protection for long-running commands

### 🎯 User Experience
- Rich terminal interface with colors and formatting
- Interactive and single-shot execution modes
- Streaming responses for real-time feedback
- Verbose mode for debugging
- Comprehensive error handling

## 🚀 Quick Installation

### Simple Install (Recommended)
```bash
pip install ollama-agent
```

### With Optional Features
```bash
# For development tools
pip install ollama-agent[dev]

# For web development 
pip install ollama-agent[web]

# For game development (pygame)
pip install ollama-agent[games]

# All features
pip install ollama-agent[dev,web,games]
```

### Prerequisites
1. Install [Ollama](https://ollama.ai/) and ensure it's running:
   ```bash
   ollama serve
   ```

2. Pull a compatible model (e.g., llama3):
   ```bash
   ollama pull llama3
   ```

### Alternative Installation Methods

#### From Source
```bash
git clone https://github.com/ollama-agent/ollama-agent.git
cd ollama-agent
pip install -e .
```

#### Development Installation
```bash
# Clone or navigate to the project directory
cd ollama-agent

# Install in development mode
pip install -e .

# Or install dependencies directly
pip install -r requirements.txt
```

## 📖 Usage

### Basic Usage
```bash
# Start the agent (will prompt for goal)
ollama-agent

# Execute a specific goal immediately
ollama-agent "Create a Python script that prints hello world"

# Use a different model
ollama-agent -m llama2 "List all Python files in this directory"
```

### Advanced Options
```bash
# Interactive mode - continue with multiple tasks
ollama-agent -i

# Verbose mode - see prompts and raw responses
ollama-agent -v "Analyze the structure of this project"

# Stream responses in real-time
ollama-agent -s "Search for TODO comments in my code"

# Increase max reasoning steps
ollama-agent -n 20 "Complex multi-step task"

# Show available tools
ollama-agent --show-tools

# Skip confirmations (use with caution!)
ollama-agent --no-confirm "Safe automated task"
```

### Example Goals

#### File Operations
```bash
ollama-agent "Create a backup directory and copy all .py files to it"
ollama-agent "Find the largest files in this directory"
ollama-agent "Organize files by extension into subdirectories"
```

#### Code Analysis
```bash
ollama-agent "Analyze this Python project structure and create a summary"
ollama-agent "Find all TODO and FIXME comments in the codebase"
ollama-agent "Count lines of code in all Python files"
```

#### Development Tasks
```bash
ollama-agent "Create a simple web server script using Python"
ollama-agent "Generate a .gitignore file for this Python project"
ollama-agent "Create unit tests for all Python modules"
```

#### System Administration
```bash
ollama-agent "Check disk usage and find large files"
ollama-agent "Monitor system resources and create a report"
ollama-agent "Clean up temporary files older than 7 days"
```

## 🛠️ Available Tools

| Tool | Description | Safety Level |
|------|-------------|-------------|
| `execute_shell_command` | Execute shell commands | ⚠️ Requires confirmation |
| `search_file` | Read file contents | ✅ Safe |
| `modify_file` | Write/modify files | ⚠️ Shows diff, requires confirmation |
| `list_directory` | List directory contents | ✅ Safe |
| `find_files` | Find files by pattern | ✅ Safe |
| `get_file_info` | Get file metadata | ✅ Safe |
| `create_directory` | Create directories | ✅ Safe |
| `copy_file` | Copy files | ✅ Safe |
| `move_file` | Move/rename files | ⚠️ Requires confirmation |
| `delete_file` | Delete files/directories | 🚨 Requires confirmation |
| `search_in_files` | Search text in files | ✅ Safe |
| `get_current_directory` | Get current directory | ✅ Safe |
| `change_directory` | Change directory | ✅ Safe |

## ⚙️ Configuration

### Environment Variables
- `OLLAMA_HOST`: Ollama server URL (default: http://localhost:11434)

### Model Selection
The agent works with most Ollama models, but larger models (7B+ parameters) tend to perform better for complex reasoning tasks:
- `llama3` (recommended)
- `llama2`
- `codellama`
- `mistral`
- `dolphin-mixtral`
