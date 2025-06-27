#!/usr/bin/env python3
"""
Post-installation hook for ollama-agent.
This runs automatically after pip install to set up prerequisites.
"""

import sys
import os
import subprocess
import time

def main():
    """Run post-installation setup."""
    print("🤖 Ollama Agent: Setting up prerequisites...")
    
    # Check if we should run silently
    if "--quiet" in sys.argv or os.environ.get("OLLAMA_AGENT_QUIET_INSTALL"):
        return setup_quietly()
    
    try:
        # Import and run the setup
        from agent.setup import main as setup_main
        return setup_main()
    except ImportError:
        # Fallback - run setup as subprocess
        try:
            result = subprocess.run([sys.executable, "-m", "agent.setup"], 
                                  capture_output=False, text=True)
            return result.returncode == 0
        except Exception as e:
            print(f"❌ Setup failed: {e}")
            print("You can run setup manually with: ollama-agent-setup")
            return False

def setup_quietly():
    """Setup prerequisites quietly without user interaction."""
    try:
        from agent.setup import (
            check_ollama_installed, 
            check_ollama_running, 
            install_ollama,
            start_ollama_service,
            download_default_model,
            run_command
        )
        
        # Check if Ollama is already installed and working
        if check_ollama_installed() and check_ollama_running():
            # Check if default model exists
            success, stdout, _ = run_command(["ollama", "list"])
            if success and "llama3" in stdout:
                print("✅ Ollama is already set up and ready!")
                return True
        
        print("📦 Installing Ollama automatically...")
        
        # Install Ollama if needed
        if not check_ollama_installed():
            if not install_ollama():
                print("⚠️  Could not install Ollama automatically.")
                print("Please run: ollama-agent-setup")
                return False
        
        # Start service if needed
        if not check_ollama_running():
            start_ollama_service()
            time.sleep(3)  # Give it time to start
        
        # Download model in background
        print("📥 Downloading model in background...")
        success, stdout, _ = run_command(["ollama", "list"])
        if not success or "llama3" not in stdout:
            # Start download without blocking
            subprocess.Popen(["ollama", "pull", "llama3"], 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL)
            print("⏳ Model download started. This will continue in the background.")
        
        print("✅ Setup completed! Run 'ollama-agent' to get started.")
        return True
        
    except Exception as e:
        print(f"⚠️  Automatic setup encountered an issue: {e}")
        print("You can complete setup manually with: ollama-agent-setup")
        return False

if __name__ == "__main__":
    main()
