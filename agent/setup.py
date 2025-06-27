#!/usr/bin/env python3
"""
Post-installation setup script for ollama-agent.
Automatically installs and configures Ollama if not present.
"""

import os
import sys
import subprocess
import platform
import urllib.request
import json
import time
from pathlib import Path

def run_command(cmd, shell=False, capture_output=True):
    """Run a command and return success status and output."""
    try:
        if shell:
            result = subprocess.run(cmd, shell=True, capture_output=capture_output, text=True, timeout=30)
        else:
            result = subprocess.run(cmd, capture_output=capture_output, text=True, timeout=30)
        return result.returncode == 0, result.stdout if capture_output else "", result.stderr if capture_output else ""
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)

def check_ollama_installed():
    """Check if Ollama is installed and accessible."""
    success, _, _ = run_command(["ollama", "--version"])
    return success

def check_ollama_running():
    """Check if Ollama service is running."""
    success, _, _ = run_command(["ollama", "list"])
    return success

def install_ollama_macos():
    """Install Ollama on macOS."""
    print("🍎 Installing Ollama on macOS...")
    
    # Try homebrew first
    success, _, _ = run_command(["brew", "--version"])
    if success:
        print("📦 Installing via Homebrew...")
        success, stdout, stderr = run_command(["brew", "install", "ollama"])
        if success:
            print("✅ Ollama installed successfully via Homebrew!")
            return True
        else:
            print(f"⚠️  Homebrew installation had issues: {stderr}")
            # Don't fail completely, try direct download
    
    # Fall back to direct download
    print("📥 Downloading and installing Ollama directly...")
    try:
        installer_url = "https://ollama.ai/download/ollama-darwin"
        installer_path = "/tmp/ollama-installer"
        
        print("   Downloading installer...")
        urllib.request.urlretrieve(installer_url, installer_path)
        
        # Make executable and run
        os.chmod(installer_path, 0o755)
        print("   Running installer...")
        success, stdout, stderr = run_command([installer_path])
        
        # Clean up
        try:
            os.remove(installer_path)
        except:
            pass
            
        if success:
            print("✅ Ollama installed successfully!")
            return True
        else:
            print(f"❌ Installation failed: {stderr}")
            # Try one more approach - curl install
            print("🔄 Trying alternative installation method...")
            install_cmd = "curl -fsSL https://ollama.ai/install.sh | sh"
            success, stdout, stderr = run_command(install_cmd, shell=True)
            if success:
                print("✅ Ollama installed successfully via curl!")
                return True
            else:
                print(f"❌ All installation methods failed: {stderr}")
                return False
                
    except Exception as e:
        print(f"❌ Download failed: {e}")
        # Last resort - try curl install
        try:
            print("🔄 Trying curl installation as last resort...")
            install_cmd = "curl -fsSL https://ollama.ai/install.sh | sh"
            success, stdout, stderr = run_command(install_cmd, shell=True)
            if success:
                print("✅ Ollama installed successfully!")
                return True
        except:
            pass
        
        print("❌ All installation methods failed.")
        print("Please install manually from: https://ollama.ai/")
        return False

def install_ollama_linux():
    """Install Ollama on Linux."""
    print("🐧 Installing Ollama on Linux...")
    
    # Use the official install script
    install_cmd = "curl -fsSL https://ollama.ai/install.sh | sh"
    success, stdout, stderr = run_command(install_cmd, shell=True)
    
    if success:
        print("✅ Ollama installed successfully!")
        return True
    else:
        print(f"❌ Installation failed: {stderr}")
        return False

def install_ollama_windows():
    """Install Ollama on Windows."""
    print("🪟 Installing Ollama on Windows...")
    print("Please download and install Ollama manually from: https://ollama.ai/download")
    print("The installer will download automatically...")
    
    try:
        installer_url = "https://ollama.ai/download/OllamaSetup.exe"
        installer_path = "OllamaSetup.exe"
        urllib.request.urlretrieve(installer_url, installer_path)
        
        print(f"📥 Downloaded installer to: {installer_path}")
        print("Please run the installer and follow the instructions.")
        print("Then restart this setup by running: python -m agent.setup")
        
        # Try to run the installer
        success, _, _ = run_command([installer_path])
        return success
    except Exception as e:
        print(f"❌ Download failed: {e}")
        print("Please manually download from: https://ollama.ai/download")
        return False

def install_ollama():
    """Install Ollama based on the current platform."""
    system = platform.system().lower()
    
    if system == "darwin":
        return install_ollama_macos()
    elif system == "linux":
        return install_ollama_linux()
    elif system == "windows":
        return install_ollama_windows()
    else:
        print(f"❌ Unsupported platform: {system}")
        print("Please install Ollama manually from: https://ollama.ai/")
        return False

def start_ollama_service():
    """Start the Ollama service."""
    print("🚀 Starting Ollama service...")
    
    system = platform.system().lower()
    
    if system == "darwin":
        # On macOS, try to start as a service
        success, _, _ = run_command(["brew", "services", "start", "ollama"])
        if not success:
            # Fall back to direct command
            subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    elif system == "linux":
        # Try systemd first
        success, _, _ = run_command(["sudo", "systemctl", "start", "ollama"])
        if not success:
            # Fall back to direct command
            subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        # Windows or other - direct command
        subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Wait a moment for service to start
    print("⏳ Waiting for Ollama service to start...")
    for i in range(10):
        time.sleep(1)
        if check_ollama_running():
            print("✅ Ollama service is running!")
            return True
        print(f"   Checking... ({i+1}/10)")
    
    print("⚠️  Ollama service may not be fully started yet.")
    return False

def download_default_model():
    """Download a default model (llama3)."""
    print("📦 Downloading default model (llama3)...")
    print("This may take a few minutes depending on your internet connection...")
    
    success, stdout, stderr = run_command(["ollama", "pull", "llama3"], capture_output=False)
    
    if success:
        print("✅ Model downloaded successfully!")
        return True
    else:
        print(f"❌ Model download failed: {stderr}")
        print("You can download it later with: ollama pull llama3")
        return False

def verify_installation():
    """Verify that everything is working."""
    print("🔍 Verifying installation...")
    
    # Check if ollama command works
    if not check_ollama_installed():
        print("❌ Ollama command not found")
        return False
    
    # Check if service is running
    if not check_ollama_running():
        print("❌ Ollama service not running")
        return False
    
    # Try to list models
    success, stdout, stderr = run_command(["ollama", "list"])
    if success and "llama3" in stdout:
        print("✅ Installation verified successfully!")
        print("✅ llama3 model is available")
        return True
    else:
        print("⚠️  Installation partially successful")
        print("You may need to download a model: ollama pull llama3")
        return True

def main():
    """Main setup function."""
    print("🤖 Ollama Agent Setup")
    print("=" * 50)
    
    try:
        # Check if Ollama is already installed and working
        if check_ollama_installed():
            print("✅ Ollama is already installed!")
            
            # Check if it's running
            if check_ollama_running():
                print("✅ Ollama service is already running!")
                
                # Check if default model exists
                success, stdout, stderr = run_command(["ollama", "list"])
                if success and "llama3" in stdout:
                    print("✅ Default model (llama3) is already available!")
                    print("\n" + "=" * 50)
                    print("🎉 Everything is already set up! You can use ollama-agent:")
                    print("   ollama-agent --help")
                    print("   ollama-agent \"Create a Python hello world script\"")
                    return True
                else:
                    # Download model
                    if download_default_model():
                        print("\n" + "=" * 50)
                        print("🎉 Setup complete! You can now use ollama-agent:")
                        print("   ollama-agent --help")
                        return True
            else:
                # Start service
                if start_ollama_service():
                    # Check for model and download if needed
                    success, stdout, stderr = run_command(["ollama", "list"])
                    if not success or "llama3" not in stdout:
                        download_default_model()
                    
                    if verify_installation():
                        print("\n" + "=" * 50)
                        print("🎉 Setup complete! You can now use ollama-agent:")
                        print("   ollama-agent --help")
                        return True
                else:
                    print("⚠️  Could not start Ollama service automatically.")
                    print("Please run: ollama serve")
                    return False
        else:
            print("📦 Ollama not found. Installing automatically...")
            
            if not install_ollama():
                print("❌ Failed to install Ollama automatically.")
                print("Please install manually from: https://ollama.ai/")
                print("Then run: ollama-agent-setup")
                return False
            
            print("✅ Ollama installed successfully!")
            
            # Start the service
            if start_ollama_service():
                print("✅ Ollama service started!")
                
                # Download default model
                if download_default_model():
                    # Final verification
                    if verify_installation():
                        print("\n" + "=" * 50)
                        print("🎉 Complete setup finished! You can now use ollama-agent:")
                        print("   ollama-agent --help")
                        print("   ollama-agent \"Create a Python hello world script\"")
                        return True
                else:
                    print("⚠️  Model download failed, but you can download it later:")
                    print("   ollama pull llama3")
                    return True
            else:
                print("⚠️  Could not start Ollama service automatically.")
                print("Please run: ollama serve")
                print("Then run: ollama pull llama3")
                return False
    
    except Exception as e:
        print(f"\n❌ Setup failed with error: {e}")
        print("You can try running the setup again with: ollama-agent-setup")
        print("Or install manually from: https://ollama.ai/")
        return False

def automatic_setup():
    """Run automatic setup without user prompts (for post-install)."""
    try:
        # Quick check if everything is already working
        if (check_ollama_installed() and check_ollama_running()):
            success, stdout, _ = run_command(["ollama", "list"])
            if success and "llama3" in stdout:
                return True
        
        # Install Ollama if needed
        if not check_ollama_installed():
            if not install_ollama():
                return False
        
        # Start service if needed
        if not check_ollama_running():
            start_ollama_service()
            time.sleep(2)  # Brief wait for startup
        
        # Download model if needed (non-blocking)
        success, stdout, _ = run_command(["ollama", "list"])
        if not success or "llama3" not in stdout:
            # Start download in background
            subprocess.Popen(["ollama", "pull", "llama3"], 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL)
        
        return True
        
    except Exception:
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ Setup interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed with error: {e}")
        sys.exit(1)
