#!/bin/bash
# Ultimate AI CLI Agent - Universal Installation Script
# Works on macOS, Linux, and Windows (with WSL/Git Bash)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
PACKAGE_NAME="ultimate-ai-cli-agent"
GITHUB_REPO="ultimate-ai-cli/ultimate-ai-cli-agent"
PYTHON_MIN_VERSION="3.8"

# Helper functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_header() {
    echo -e "${PURPLE}🚀 $1${NC}"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check Python version
check_python() {
    if command_exists python3; then
        PYTHON_CMD="python3"
    elif command_exists python; then
        PYTHON_CMD="python"
    else
        log_error "Python is not installed. Please install Python $PYTHON_MIN_VERSION or higher."
        exit 1
    fi
    
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    if [[ $PYTHON_MAJOR -lt 3 ]] || [[ $PYTHON_MAJOR -eq 3 && $PYTHON_MINOR -lt 8 ]]; then
        log_error "Python $PYTHON_MIN_VERSION or higher is required. Found: $PYTHON_VERSION"
        exit 1
    fi
    
    log_success "Python $PYTHON_VERSION detected"
}

# Check pip
check_pip() {
    if ! command_exists pip && ! command_exists pip3; then
        log_error "pip is not installed. Installing pip..."
        if command_exists curl; then
            curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
            $PYTHON_CMD get-pip.py
            rm get-pip.py
        else
            log_error "curl is not available. Please install pip manually."
            exit 1
        fi
    fi
    
    if command_exists pip3; then
        PIP_CMD="pip3"
    else
        PIP_CMD="pip"
    fi
    
    log_success "pip is available"
}

# Detect OS
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
        if command_exists lsb_release; then
            DISTRO=$(lsb_release -si)
        elif [[ -f /etc/os-release ]]; then
            DISTRO=$(grep '^ID=' /etc/os-release | cut -d= -f2 | tr -d '"')
        else
            DISTRO="unknown"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        DISTRO="macos"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        OS="windows"
        DISTRO="windows"
    else
        OS="unknown"
        DISTRO="unknown"
    fi
    
    log_info "Detected OS: $OS ($DISTRO)"
}

# Install system dependencies
install_system_deps() {
    log_header "Installing System Dependencies"
    
    case $OS in
        "macos")
            if command_exists brew; then
                log_info "Installing dependencies via Homebrew..."
                brew install --quiet node || log_warning "Node.js installation failed"
                brew install --cask --quiet google-chrome || log_warning "Chrome installation failed"
            else
                log_warning "Homebrew not found. Please install Node.js and Chrome manually."
            fi
            ;;
        "linux")
            case $DISTRO in
                "ubuntu"|"debian")
                    log_info "Installing dependencies via apt..."
                    sudo apt update -qq
                    sudo apt install -y nodejs npm chromium-browser curl wget git build-essential || log_warning "Some dependencies failed to install"
                    ;;
                "fedora"|"centos"|"rhel")
                    log_info "Installing dependencies via dnf/yum..."
                    if command_exists dnf; then
                        sudo dnf install -y nodejs npm chromium curl wget git gcc || log_warning "Some dependencies failed to install"
                    else
                        sudo yum install -y nodejs npm chromium curl wget git gcc || log_warning "Some dependencies failed to install"
                    fi
                    ;;
                *)
                    log_warning "Unknown Linux distribution. Please install Node.js, Chrome, and build tools manually."
                    ;;
            esac
            ;;
        "windows")
            log_warning "Windows detected. Please ensure you have:"
            log_warning "  - Node.js (https://nodejs.org/)"
            log_warning "  - Google Chrome"
            log_warning "  - Git for Windows"
            ;;
        *)
            log_warning "Unknown OS. Please install Node.js and Chrome manually."
            ;;
    esac
}

# Install Python package
install_package() {
    log_header "Installing Ultimate AI CLI Agent"
    
    # Upgrade pip first
    log_info "Upgrading pip..."
    $PIP_CMD install --upgrade pip
    
    # Install the package with full capabilities
    log_info "Installing $PACKAGE_NAME with full capabilities..."
    if $PIP_CMD install "$PACKAGE_NAME[full]" --upgrade; then
        log_success "Package installed successfully!"
    else
        log_warning "Full installation failed. Trying minimal installation..."
        if $PIP_CMD install "$PACKAGE_NAME" --upgrade; then
            log_success "Minimal package installed successfully!"
            log_warning "Some advanced features may not be available."
        else
            log_error "Package installation failed!"
            exit 1
        fi
    fi
}

# Install browser drivers
install_drivers() {
    log_header "Setting up Browser Drivers"
    
    log_info "Installing browser automation drivers..."
    $PYTHON_CMD -c "
try:
    from webdriver_manager.chrome import ChromeDriverManager
    from webdriver_manager.firefox import GeckoDriverManager
    ChromeDriverManager().install()
    GeckoDriverManager().install()
    print('✅ Browser drivers installed successfully')
except Exception as e:
    print(f'⚠️  Browser driver installation failed: {e}')
    print('Browser automation may not work until drivers are manually installed')
" || log_warning "Browser driver installation failed"
}

# Verify installation
verify_installation() {
    log_header "Verifying Installation"
    
    # Check if commands are available
    if command_exists ultimate-ai-cli; then
        log_success "ultimate-ai-cli command is available"
    elif command_exists uai; then
        log_success "uai command is available"
    else
        log_warning "Commands not found in PATH. You may need to restart your terminal."
    fi
    
    # Test basic functionality
    log_info "Testing basic functionality..."
    if $PYTHON_CMD -c "
try:
    import agent
    print('✅ Agent module imported successfully')
except ImportError as e:
    print(f'❌ Agent import failed: {e}')
    exit(1)
"; then
        log_success "Basic functionality test passed"
    else
        log_error "Basic functionality test failed"
        exit 1
    fi
    
    # Test enhanced features
    log_info "Testing enhanced features..."
    $PYTHON_CMD -c "
import sys
features = []
try:
    import requests
    features.append('✅ Internet access')
except ImportError:
    features.append('❌ Internet access')

try:
    import selenium
    features.append('✅ Browser automation')
except ImportError:
    features.append('❌ Browser automation')

try:
    import psutil
    features.append('✅ System monitoring')
except ImportError:
    features.append('❌ System monitoring')

try:
    import flask
    features.append('✅ Web server support')
except ImportError:
    features.append('❌ Web server support')

for feature in features:
    print(feature)
"
}

# Create desktop shortcuts (optional)
create_shortcuts() {
    log_header "Creating Desktop Integration"
    
    case $OS in
        "macos")
            # Create alias in shell profile
            SHELL_PROFILE=""
            if [[ -f "$HOME/.zshrc" ]]; then
                SHELL_PROFILE="$HOME/.zshrc"
            elif [[ -f "$HOME/.bash_profile" ]]; then
                SHELL_PROFILE="$HOME/.bash_profile"
            elif [[ -f "$HOME/.bashrc" ]]; then
                SHELL_PROFILE="$HOME/.bashrc"
            fi
            
            if [[ -n "$SHELL_PROFILE" ]]; then
                if ! grep -q "alias ai=" "$SHELL_PROFILE"; then
                    echo "alias ai='ultimate-ai-cli'" >> "$SHELL_PROFILE"
                    log_success "Added 'ai' alias to $SHELL_PROFILE"
                fi
            fi
            ;;
        "linux")
            # Create desktop entry
            DESKTOP_DIR="$HOME/.local/share/applications"
            mkdir -p "$DESKTOP_DIR"
            
            cat > "$DESKTOP_DIR/ultimate-ai-cli.desktop" << EOF
[Desktop Entry]
Name=Ultimate AI CLI Agent
Comment=The Ultimate AI CLI Agent with enhanced capabilities
Exec=ultimate-ai-cli
Icon=terminal
Type=Application
Categories=Development;System;
Terminal=true
EOF
            log_success "Created desktop entry"
            ;;
    esac
}

# Show completion message
show_completion() {
    log_header "Installation Complete! 🎉"
    
    echo ""
    echo "The Ultimate AI CLI Agent is now installed with enhanced capabilities:"
    echo "  🌐 Internet access and web browsing"
    echo "  🖥️  Browser automation and control"
    echo "  🚀 Server management and process control"
    echo "  🧠 Enhanced AI intelligence and reasoning"
    echo "  🔧 Full terminal and system control"
    echo "  🛡️  Advanced safety and reliability"
    echo ""
    echo "Available commands:"
    echo "  ultimate-ai-cli    # Full command"
    echo "  uai                # Short alias"
    echo "  ai-agent           # Alternative name"
    echo ""
    echo "Quick start:"
    echo "  ultimate-ai-cli \"create a simple web application\""
    echo "  uai \"search for Python best practices and apply them\""
    echo ""
    echo "For help:"
    echo "  ultimate-ai-cli --help"
    echo "  ultimate-ai-cli --examples"
    echo ""
    echo "Documentation: https://ultimate-ai-cli.readthedocs.io/"
    echo "GitHub: https://github.com/$GITHUB_REPO"
    echo ""
    echo "Enjoy your Ultimate AI CLI Agent! 🚀"
}

# Main installation flow
main() {
    echo "=========================================="
    log_header "Ultimate AI CLI Agent Installer"
    echo "=========================================="
    echo ""
    
    # Checks
    detect_os
    check_python
    check_pip
    
    # Installation
    install_system_deps
    install_package
    install_drivers
    
    # Verification
    verify_installation
    create_shortcuts
    
    # Completion
    show_completion
}

# Handle interrupts
trap 'log_error "Installation interrupted"; exit 1' INT TERM

# Run main function
main "$@"
