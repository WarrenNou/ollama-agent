# 📦 Installation Guide

This guide provides comprehensive instructions for installing the Ultimate AI CLI Agent (ollama-agent) using pip and other methods.

## 🚀 Quick Installation (Recommended)

### Method 1: Install from PyPI (when published)

```bash
# Install the latest stable version
pip install ultimate-ai-cli-agent

# Or using the legacy name (if aliased)
pip install ollama-agent
```

### Method 2: Install from Source (Current)

Since the package may not be published to PyPI yet, you can install directly from source:

```bash
# Clone the repository
git clone https://github.com/your-username/ollama-agent.git
cd ollama-agent

# Install the package
pip install .
```

## 🔧 Installation Options

### Basic Installation
```bash
# Minimal installation with core features only
pip install ultimate-ai-cli-agent
```

### Installation with Optional Features
```bash
# Web automation and browser features
pip install ultimate-ai-cli-agent[web]

# Server management features  
pip install ultimate-ai-cli-agent[server]

# Development tools
pip install ultimate-ai-cli-agent[dev]

# All features (recommended for full functionality)
pip install ultimate-ai-cli-agent[full]
```

### Development Installation
```bash
# Clone the repository
git clone https://github.com/your-username/ollama-agent.git
cd ollama-agent

# Install in editable mode for development
pip install -e .

# Or install with development dependencies
pip install -e .[dev]
```

## 📋 Prerequisites

Before installing, ensure you have the following prerequisites:

### 1. Python Requirements
- **Python 3.8 or higher** is required
- pip (Python package installer)

```bash
# Check your Python version
python --version

# Check pip version
pip --version
```

### 2. Ollama Installation
The agent requires Ollama to be installed and running:

#### Install Ollama
```bash
# macOS (using Homebrew)
brew install ollama

# Or download from https://ollama.ai/
```

#### Start Ollama Service
```bash
# Start the Ollama service
ollama serve
```

#### Download a Model
```bash
# Download the default model (recommended)
ollama pull llama3

# Or download other models
ollama pull llama2
ollama pull codellama
ollama pull mistral
```

### 3. Optional Dependencies

#### For Web Automation Features
```bash
# Chrome/Chromium browser (for Selenium)
# Install via your system's package manager

# macOS
brew install --cask google-chrome

# Ubuntu/Debian
sudo apt-get install chromium-browser

# Windows - Download from Google Chrome website
```

## 🛠️ Verification

After installation, verify everything is working:

### 1. Check Installation
```bash
# Check if the command is available
ultimate-ai-cli --version

# Or using aliases
uai --version
ollama-agent --version
```

### 2. Test Basic Functionality
```bash
# Run a simple test
ultimate-ai-cli "echo 'Hello, World!'"

# Or in interactive mode
ultimate-ai-cli -i
```

### 3. Verify Ollama Connection
```bash
# Test Ollama connectivity
ultimate-ai-cli "test ollama connection"
```

## 🌍 Platform-Specific Instructions

### macOS
```bash
# Using Homebrew (if package is available)
brew install ultimate-ai-cli-agent

# Or using pip
pip3 install ultimate-ai-cli-agent
```

### Linux (Ubuntu/Debian)
```bash
# Update package list
sudo apt update

# Install Python and pip if needed
sudo apt install python3 python3-pip

# Install the agent
pip3 install ultimate-ai-cli-agent
```

### Windows
```bash
# Using pip in Command Prompt or PowerShell
pip install ultimate-ai-cli-agent

# Or using Chocolatey (if package is available)
choco install ultimate-ai-cli-agent
```

## 🔄 Updating

### Update to Latest Version
```bash
# Update from PyPI
pip install --upgrade ultimate-ai-cli-agent

# Update from source
cd ollama-agent
git pull origin main
pip install --upgrade .
```

## 🗑️ Uninstallation

### Remove the Package
```bash
# Uninstall the package
pip uninstall ultimate-ai-cli-agent

# Clean up configuration (optional)
rm -rf ~/.ollama-agent
```

## 🐛 Troubleshooting

### Common Issues

#### 1. Command Not Found
```bash
# If ultimate-ai-cli command is not found, try:
python -m agent.main

# Or check your PATH
echo $PATH
```

#### 2. Permission Errors
```bash
# Use --user flag to install for current user only
pip install --user ultimate-ai-cli-agent

# Or use virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install ultimate-ai-cli-agent
```

#### 3. Ollama Connection Issues
```bash
# Check if Ollama is running
curl http://localhost:11434/api/version

# Restart Ollama service
ollama serve
```

#### 4. Missing Dependencies
```bash
# Install missing optional dependencies
pip install ultimate-ai-cli-agent[full]

# Or install specific dependencies manually
pip install selenium beautifulsoup4 flask
```

## 🏗️ Building from Source

If you want to build the package yourself:

```bash
# Clone the repository
git clone https://github.com/your-username/ollama-agent.git
cd ollama-agent

# Install build dependencies
pip install build twine

# Build the package
python -m build

# Install the built package
pip install dist/ultimate_ai_cli_agent-*.whl
```

## 🔐 Virtual Environment (Recommended)

For a clean installation, use a virtual environment:

```bash
# Create virtual environment
python -m venv ollama-agent-env

# Activate virtual environment
# On macOS/Linux:
source ollama-agent-env/bin/activate
# On Windows:
ollama-agent-env\Scripts\activate

# Install the package
pip install ultimate-ai-cli-agent

# When done, deactivate
deactivate
```

## 📞 Support

If you encounter any installation issues:

1. Check the [troubleshooting section](#-troubleshooting) above
2. Review the [project issues](https://github.com/your-username/ollama-agent/issues)
3. Create a new issue with your installation details
4. Join our community discussions

## 🎯 Quick Start After Installation

Once installed, you can immediately start using the agent:

```bash
# Interactive mode
ultimate-ai-cli

# Direct command
ultimate-ai-cli "create a hello world python script"

# With specific model
ultimate-ai-cli -m llama2 "analyze this code file"
```

Enjoy using the Ultimate AI CLI Agent! 🤖✨
