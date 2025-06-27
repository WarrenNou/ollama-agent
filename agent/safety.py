"""
Enhanced safety module for the Ollama agent.
Provides improved dangerous command detection and safety confirmations.
"""

import re
import os
from typing import List, Dict, Any, Tuple
from rich.console import Console
from rich.prompt import Confirm
from rich.panel import Panel


class SafetyManager:
    """Enhanced safety management for agent operations."""
    
    def __init__(self, console: Console = None):
        self.console = console or Console()
        
        # Dangerous command patterns
        self.dangerous_patterns = {
            "destructive": [
                r'\brm\s+.*-r.*/',  # rm -r commands
                r'\brm\s+.*-rf.*',  # rm -rf commands
                r'\brmdir\s+',      # rmdir commands
                r'\bdel\s+.*\*',    # Windows del with wildcards
                r'\bformat\s+',     # format commands
                r'\bfdisk\s+',      # disk partitioning
                r'>\s*/dev/',       # Writing to device files
                r'\bdd\s+.*of=',    # dd command with output
            ],
            "system_modification": [
                r'\bchmod\s+.*777', # Wide open permissions
                r'\bchown\s+.*root', # Ownership changes to root
                r'\bsudo\s+',       # Sudo commands
                r'\bsu\s+',         # Switch user
                r'passwd\s+',       # Password changes
                r'/etc/',           # System config directories
                r'/boot/',          # Boot directory
                r'/sys/',           # System directory
            ],
            "network_security": [
                r'\bcurl\s+.*\|\s*sh',    # Pipe curl to shell
                r'\bwget\s+.*\|\s*sh',    # Pipe wget to shell
                r'\bnc\s+.*-e',           # Netcat with execute
                r'\btelnet\s+',           # Telnet connections
                r'\bftp\s+',              # FTP connections
                r'ssh\s+.*@',             # SSH connections
            ],
            "data_exfiltration": [
                r'\btar\s+.*\|\s*ssh',    # Archive and send via SSH
                r'\bzip\s+.*\|\s*curl',   # Zip and upload
                r'\bcp\s+.*\/tmp',        # Copy to temp (potential staging)
                r'\bmv\s+.*\/tmp',        # Move to temp
            ]
        }
        
        # File patterns that require extra caution
        self.sensitive_file_patterns = [
            r'\.ssh/',
            r'\.aws/',
            r'\.config/',
            r'passwords?\.txt',
            r'secrets?\.txt',
            r'\.env',
            r'\.key$',
            r'\.pem$',
            r'\.p12$',
            r'\.pfx$',
        ]
        
        # Directories that should be protected
        self.protected_directories = [
            '/',
            '/bin',
            '/boot',
            '/dev',
            '/etc',
            '/lib',
            '/lib64',
            '/proc',
            '/root',
            '/sbin',
            '/sys',
            '/usr',
            '/var',
            'C:\\Windows',
            'C:\\Program Files',
            'C:\\System32',
        ]
    
    def assess_command_risk(self, command: str) -> Tuple[str, float, List[str]]:
        """
        Assess the risk level of a command.
        
        Returns:
            Tuple of (risk_level, risk_score, warnings)
        """
        warnings = []
        risk_score = 0.0
        
        command_lower = command.lower()
        
        # Check for dangerous patterns
        for category, patterns in self.dangerous_patterns.items():
            for pattern in patterns:
                if re.search(pattern, command, re.IGNORECASE):
                    risk_score += 0.3
                    warnings.append(f"Detected {category} pattern: {pattern}")
        
        # Check for sensitive files
        for pattern in self.sensitive_file_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                risk_score += 0.2
                warnings.append(f"Command involves sensitive files: {pattern}")
        
        # Check for protected directories
        for protected_dir in self.protected_directories:
            if protected_dir in command:
                risk_score += 0.4
                warnings.append(f"Command affects protected directory: {protected_dir}")
        
        # Determine risk level
        if risk_score >= 0.8:
            risk_level = "CRITICAL"
        elif risk_score >= 0.5:
            risk_level = "HIGH"
        elif risk_score >= 0.3:
            risk_level = "MEDIUM"
        elif risk_score > 0:
            risk_level = "LOW"
        else:
            risk_level = "SAFE"
        
        return risk_level, risk_score, warnings
    
    def assess_file_operation_risk(self, operation: str, file_path: str) -> Tuple[str, float, List[str]]:
        """Assess risk for file operations."""
        warnings = []
        risk_score = 0.0
        
        # Check if operation is destructive
        destructive_ops = ["delete", "move", "modify", "overwrite"]
        if operation.lower() in destructive_ops:
            risk_score += 0.3
        
        # Check for sensitive file patterns
        for pattern in self.sensitive_file_patterns:
            if re.search(pattern, file_path, re.IGNORECASE):
                risk_score += 0.4
                warnings.append(f"Sensitive file detected: {pattern}")
        
        # Check for protected directories
        abs_path = os.path.abspath(file_path)
        for protected_dir in self.protected_directories:
            if abs_path.startswith(protected_dir):
                risk_score += 0.5
                warnings.append(f"File in protected directory: {protected_dir}")
        
        # Check for system files
        system_extensions = ['.exe', '.dll', '.sys', '.so', '.dylib']
        if any(file_path.lower().endswith(ext) for ext in system_extensions):
            risk_score += 0.3
            warnings.append("System executable file detected")
        
        # Determine risk level
        if risk_score >= 0.8:
            risk_level = "CRITICAL"
        elif risk_score >= 0.5:
            risk_level = "HIGH"
        elif risk_score >= 0.3:
            risk_level = "MEDIUM"
        elif risk_score > 0:
            risk_level = "LOW"
        else:
            risk_level = "SAFE"
        
        return risk_level, risk_score, warnings
    
    def require_confirmation(self, operation: str, details: str, risk_level: str, warnings: List[str]) -> bool:
        """
        Show safety warning and get user confirmation.
        
        Args:
            operation: Description of the operation
            details: Detailed information about what will happen
            risk_level: Risk level (SAFE, LOW, MEDIUM, HIGH, CRITICAL)
            warnings: List of specific warnings
        
        Returns:
            True if user confirms, False otherwise
        """
        # Auto-approve safe operations
        if risk_level == "SAFE":
            return True
        
        # Create warning panel
        risk_colors = {
            "LOW": "yellow",
            "MEDIUM": "orange3",
            "HIGH": "red",
            "CRITICAL": "bold red"
        }
        
        color = risk_colors.get(risk_level, "white")
        
        warning_text = f"[{color}]⚠️  SAFETY WARNING - {risk_level} RISK[/]\n\n"
        warning_text += f"Operation: {operation}\n"
        warning_text += f"Details: {details}\n\n"
        
        if warnings:
            warning_text += "Specific concerns:\n"
            for warning in warnings:
                warning_text += f"• {warning}\n"
        
        self.console.print(Panel(warning_text, border_style=color, title="Safety Check"))
        
        # Critical operations require explicit typing
        if risk_level == "CRITICAL":
            response = self.console.input("\n[bold red]Type 'I UNDERSTAND THE RISKS' to proceed: [/]")
            return response == "I UNDERSTAND THE RISKS"
        
        # Other risky operations need confirmation
        return Confirm.ask(f"\n[{color}]Do you want to proceed with this {risk_level.lower()} risk operation?[/]")
    
    def sanitize_command(self, command: str) -> str:
        """
        Sanitize a command by removing or escaping dangerous elements.
        """
        # Remove multiple spaces
        command = re.sub(r'\s+', ' ', command.strip())
        
        # Escape special characters that could be used for injection
        dangerous_chars = ['|', '&', ';', '$(', '`', '>', '<']
        for char in dangerous_chars:
            if char in command:
                self.console.print(f"[yellow]Warning: Removing potentially dangerous character: {char}[/]")
                command = command.replace(char, '')
        
        return command
    
    def create_backup(self, file_path: str) -> str:
        """Create a backup of a file before modification."""
        if not os.path.exists(file_path):
            return "File does not exist, no backup needed"
        
        try:
            import shutil
            from datetime import datetime
            
            # Create backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{file_path}.backup_{timestamp}"
            
            shutil.copy2(file_path, backup_path)
            return f"Backup created: {backup_path}"
            
        except Exception as e:
            return f"Failed to create backup: {str(e)}"
    
    def log_risky_operation(self, operation: str, details: str, risk_level: str, approved: bool):
        """Log risky operations for audit purposes."""
        try:
            import json
            from datetime import datetime
            
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "operation": operation,
                "details": details,
                "risk_level": risk_level,
                "approved": approved,
                "user": os.getenv("USER", "unknown")
            }
            
            log_file = "agent_safety_log.json"
            
            # Read existing log or create new
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    logs = json.load(f)
            else:
                logs = []
            
            logs.append(log_entry)
            
            # Keep only last 1000 entries
            if len(logs) > 1000:
                logs = logs[-1000:]
            
            with open(log_file, 'w') as f:
                json.dump(logs, f, indent=2)
                
        except Exception as e:
            self.console.print(f"[yellow]Warning: Could not log operation: {e}[/]")


# Global safety manager instance
safety_manager = SafetyManager()
