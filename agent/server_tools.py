"""
Advanced server management and process control tools.
"""

import os
import subprocess
import signal
import psutil
import time
import json
import socket
import threading
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import tempfile
import shutil


class ProcessManager:
    """Manage system processes and background tasks."""
    
    def __init__(self):
        self.running_processes = {}
        self.server_processes = {}
    
    def start_process(self, command: str, name: Optional[str] = None, background: bool = True, 
                     working_dir: Optional[str] = None, env_vars: Optional[Dict[str, str]] = None) -> str:
        """Start a new process."""
        try:
            if not name:
                name = f"process_{int(time.time())}"
            
            # Prepare environment
            env = os.environ.copy()
            if env_vars:
                env.update(env_vars)
            
            # Start process
            if background:
                process = subprocess.Popen(
                    command,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    cwd=working_dir,
                    env=env,
                    preexec_fn=os.setsid if os.name != 'nt' else None
                )
                
                self.running_processes[name] = {
                    "process": process,
                    "command": command,
                    "pid": process.pid,
                    "started_at": time.time(),
                    "working_dir": working_dir
                }
                
                return f"Process '{name}' started with PID {process.pid}"
            else:
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    cwd=working_dir,
                    env=env,
                    timeout=30
                )
                
                output = result.stdout
                if result.stderr:
                    output += f"\nSTDERR: {result.stderr}"
                
                return output
        except subprocess.TimeoutExpired:
            return "Process timed out after 30 seconds"
        except Exception as e:
            return f"Failed to start process: {str(e)}"
    
    def stop_process(self, name: str) -> str:
        """Stop a running process."""
        try:
            if name not in self.running_processes:
                return f"Process '{name}' not found"
            
            process_info = self.running_processes[name]
            process = process_info["process"]
            
            # Terminate gracefully
            process.terminate()
            
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Force kill if it doesn't terminate
                process.kill()
                process.wait()
            
            del self.running_processes[name]
            
            # Also remove from server processes if it's there
            if name in self.server_processes:
                del self.server_processes[name]
            
            return f"Process '{name}' stopped successfully"
        except Exception as e:
            return f"Failed to stop process: {str(e)}"
    
    def get_process_status(self, name: Optional[str] = None) -> str:
        """Get status of processes."""
        try:
            if name:
                if name not in self.running_processes:
                    return f"Process '{name}' not found"
                
                process_info = self.running_processes[name]
                process = process_info["process"]
                
                status = {
                    "name": name,
                    "pid": process_info["pid"],
                    "command": process_info["command"],
                    "running": process.poll() is None,
                    "started_at": process_info["started_at"],
                    "uptime": time.time() - process_info["started_at"]
                }
                
                # Get output if available
                if process.poll() is not None:
                    stdout, stderr = process.communicate()
                    status["stdout"] = stdout[:1000]  # Limit output
                    status["stderr"] = stderr[:1000]
                
                return json.dumps(status, indent=2)
            else:
                # List all processes
                all_processes = []
                for name, info in self.running_processes.items():
                    process = info["process"]
                    all_processes.append({
                        "name": name,
                        "pid": info["pid"],
                        "command": info["command"][:50] + "...",
                        "running": process.poll() is None,
                        "uptime": time.time() - info["started_at"]
                    })
                
                return json.dumps(all_processes, indent=2)
        except Exception as e:
            return f"Failed to get process status: {str(e)}"
    
    def kill_process_by_pid(self, pid: int) -> str:
        """Kill a process by PID."""
        try:
            process = psutil.Process(pid)
            process.terminate()
            
            # Wait a bit for graceful termination
            try:
                process.wait(timeout=5)
            except psutil.TimeoutExpired:
                process.kill()
            
            return f"Process {pid} killed successfully"
        except psutil.NoSuchProcess:
            return f"Process {pid} not found"
        except psutil.AccessDenied:
            return f"Access denied to kill process {pid}"
        except Exception as e:
            return f"Failed to kill process: {str(e)}"


class ServerManager:
    """Manage various types of servers and services."""
    
    def __init__(self, process_manager: ProcessManager):
        self.process_manager = process_manager
        self.servers = {}
    
    def start_http_server(self, port: int = 8000, directory: Optional[str] = None, name: Optional[str] = None) -> str:
        """Start a simple HTTP server."""
        try:
            if not name:
                name = f"http_server_{port}"
            
            if not directory:
                directory = os.getcwd()
            
            # Use Python's built-in HTTP server
            command = f"python3 -m http.server {port}"
            
            result = self.process_manager.start_process(
                command, 
                name, 
                background=True, 
                working_dir=directory
            )
            
            if "started" in result:
                self.servers[name] = {
                    "type": "http",
                    "port": port,
                    "directory": directory,
                    "url": f"http://localhost:{port}"
                }
                
                return f"HTTP server started on port {port}. URL: http://localhost:{port}"
            
            return result
        except Exception as e:
            return f"Failed to start HTTP server: {str(e)}"
    
    def start_flask_app(self, app_file: str, port: int = 5000, name: Optional[str] = None, 
                       debug: bool = True) -> str:
        """Start a Flask application."""
        try:
            if not name:
                name = f"flask_app_{port}"
            
            if not os.path.exists(app_file):
                return f"Flask app file not found: {app_file}"
            
            env_vars = {
                "FLASK_APP": app_file,
                "FLASK_ENV": "development" if debug else "production",
                "FLASK_DEBUG": "1" if debug else "0"
            }
            
            command = f"python3 -m flask run --host=0.0.0.0 --port={port}"
            
            result = self.process_manager.start_process(
                command,
                name,
                background=True,
                working_dir=os.path.dirname(app_file) or os.getcwd(),
                env_vars=env_vars
            )
            
            if "started" in result:
                self.servers[name] = {
                    "type": "flask",
                    "port": port,
                    "app_file": app_file,
                    "url": f"http://localhost:{port}"
                }
                
                return f"Flask app started on port {port}. URL: http://localhost:{port}"
            
            return result
        except Exception as e:
            return f"Failed to start Flask app: {str(e)}"
    
    def start_node_server(self, script_file: str, port: int = 3000, name: Optional[str] = None) -> str:
        """Start a Node.js server."""
        try:
            if not name:
                name = f"node_server_{port}"
            
            if not os.path.exists(script_file):
                return f"Node.js script file not found: {script_file}"
            
            command = f"node {script_file}"
            
            result = self.process_manager.start_process(
                command,
                name,
                background=True,
                working_dir=os.path.dirname(script_file) or os.getcwd(),
                env_vars={"PORT": str(port)}
            )
            
            if "started" in result:
                self.servers[name] = {
                    "type": "node",
                    "port": port,
                    "script_file": script_file,
                    "url": f"http://localhost:{port}"
                }
                
                return f"Node.js server started on port {port}. URL: http://localhost:{port}"
            
            return result
        except Exception as e:
            return f"Failed to start Node.js server: {str(e)}"
    
    def start_development_server(self, project_type: str, directory: Optional[str] = None, 
                                port: Optional[int] = None, name: Optional[str] = None) -> str:
        """Start a development server based on project type."""
        try:
            if not directory:
                directory = os.getcwd()
            
            if not name:
                name = f"{project_type}_dev_server"
            
            project_type = project_type.lower()
            
            if project_type in ["react", "nextjs", "next.js"]:
                command = "npm run dev" if port is None else f"npm run dev -- --port {port}"
                default_port = 3000
            elif project_type in ["vue", "vuejs"]:
                command = "npm run serve" if port is None else f"npm run serve -- --port {port}"
                default_port = 8080
            elif project_type in ["angular"]:
                command = "ng serve" if port is None else f"ng serve --port {port}"
                default_port = 4200
            elif project_type in ["django"]:
                command = "python manage.py runserver" if port is None else f"python manage.py runserver 0.0.0.0:{port}"
                default_port = 8000
            elif project_type in ["rails", "ruby"]:
                command = "rails server" if port is None else f"rails server -p {port}"
                default_port = 3000
            elif project_type in ["vite"]:
                command = "npm run dev" if port is None else f"npm run dev -- --port {port}"
                default_port = 5173
            else:
                return f"Unsupported project type: {project_type}"
            
            result = self.process_manager.start_process(
                command,
                name,
                background=True,
                working_dir=directory
            )
            
            if "started" in result:
                used_port = port or default_port
                self.servers[name] = {
                    "type": project_type,
                    "port": used_port,
                    "directory": directory,
                    "url": f"http://localhost:{used_port}"
                }
                
                return f"{project_type.title()} dev server started on port {used_port}. URL: http://localhost:{used_port}"
            
            return result
        except Exception as e:
            return f"Failed to start development server: {str(e)}"
    
    def stop_server(self, name: str) -> str:
        """Stop a server."""
        try:
            result = self.process_manager.stop_process(name)
            
            if name in self.servers:
                del self.servers[name]
            
            return result
        except Exception as e:
            return f"Failed to stop server: {str(e)}"
    
    def list_servers(self) -> str:
        """List all running servers."""
        try:
            if not self.servers:
                return "No servers currently running"
            
            server_list = []
            for name, info in self.servers.items():
                # Check if process is still running
                process_status = self.process_manager.get_process_status(name)
                try:
                    status_data = json.loads(process_status)
                    running = status_data.get("running", False)
                except:
                    running = False
                
                server_list.append({
                    "name": name,
                    "type": info["type"],
                    "port": info["port"],
                    "url": info["url"],
                    "running": running
                })
            
            return json.dumps(server_list, indent=2)
        except Exception as e:
            return f"Failed to list servers: {str(e)}"
    
    def check_port(self, port: int) -> str:
        """Check if a port is available."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                result = sock.connect_ex(('localhost', port))
                if result == 0:
                    return f"Port {port} is in use"
                else:
                    return f"Port {port} is available"
        except Exception as e:
            return f"Failed to check port: {str(e)}"


class SystemMonitor:
    """Monitor system resources and performance."""
    
    def get_system_info(self) -> str:
        """Get comprehensive system information."""
        try:
            info = {
                "cpu": {
                    "count": psutil.cpu_count(),
                    "usage_percent": psutil.cpu_percent(interval=1),
                    "frequency": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
                },
                "memory": {
                    "total": psutil.virtual_memory().total,
                    "available": psutil.virtual_memory().available,
                    "used": psutil.virtual_memory().used,
                    "percent": psutil.virtual_memory().percent
                },
                "disk": {
                    "total": psutil.disk_usage('/').total,
                    "used": psutil.disk_usage('/').used,
                    "free": psutil.disk_usage('/').free,
                    "percent": psutil.disk_usage('/').percent
                },
                "network": {}
            }
            
            # Network info
            try:
                net_io = psutil.net_io_counters()
                info["network"] = {
                    "bytes_sent": net_io.bytes_sent,
                    "bytes_recv": net_io.bytes_recv,
                    "packets_sent": net_io.packets_sent,
                    "packets_recv": net_io.packets_recv
                }
            except:
                info["network"] = {"error": "Network info not available"}
            
            return json.dumps(info, indent=2)
        except Exception as e:
            return f"Failed to get system info: {str(e)}"
    
    def get_running_processes(self, limit: int = 10) -> str:
        """Get list of running processes."""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Sort by CPU usage
            processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
            
            return json.dumps(processes[:limit], indent=2)
        except Exception as e:
            return f"Failed to get running processes: {str(e)}"


# Global instances
process_manager = ProcessManager()
server_manager = ServerManager(process_manager)
system_monitor = SystemMonitor()


# Tool functions for the agent
def start_server(server_type: str, **kwargs) -> str:
    """
    Start various types of servers.
    
    Server types:
    - http: Simple HTTP server (port, directory)
    - flask: Flask application (app_file, port, debug)
    - node: Node.js server (script_file, port)
    - dev: Development server (project_type, directory, port)
    """
    try:
        server_type = server_type.lower()
        
        if server_type == "http":
            return server_manager.start_http_server(
                kwargs.get("port", 8000),
                kwargs.get("directory"),
                kwargs.get("name")
            )
        elif server_type == "flask":
            app_file = kwargs.get("app_file")
            if not app_file:
                return "Flask server requires 'app_file' parameter"
            return server_manager.start_flask_app(
                app_file,
                kwargs.get("port", 5000),
                kwargs.get("name"),
                kwargs.get("debug", True)
            )
        elif server_type == "node":
            script_file = kwargs.get("script_file")
            if not script_file:
                return "Node server requires 'script_file' parameter"
            return server_manager.start_node_server(
                script_file,
                kwargs.get("port", 3000),
                kwargs.get("name")
            )
        elif server_type == "dev":
            project_type = kwargs.get("project_type")
            if not project_type:
                return "Development server requires 'project_type' parameter"
            return server_manager.start_development_server(
                project_type,
                kwargs.get("directory"),
                kwargs.get("port"),
                kwargs.get("name")
            )
        else:
            return f"Unsupported server type: {server_type}"
    except Exception as e:
        return f"Failed to start server: {str(e)}"


def stop_server(name: str) -> str:
    """Stop a running server."""
    return server_manager.stop_server(name)


def list_servers() -> str:
    """List all running servers."""
    return server_manager.list_servers()


def manage_process(action: str, **kwargs) -> str:
    """
    Manage system processes.
    
    Actions:
    - start: Start a new process (command, name, background, working_dir)
    - stop: Stop a process (name)
    - status: Get process status (name)
    - kill: Kill process by PID (pid)
    """
    try:
        action = action.lower()
        
        if action == "start":
            command = kwargs.get("command")
            if not command:
                return "Start action requires 'command' parameter"
            return process_manager.start_process(
                command,
                kwargs.get("name"),
                kwargs.get("background", True),
                kwargs.get("working_dir"),
                kwargs.get("env_vars")
            )
        elif action == "stop":
            name = kwargs.get("name")
            if not name:
                return "Stop action requires 'name' parameter"
            return process_manager.stop_process(name)
        elif action == "status":
            return process_manager.get_process_status(kwargs.get("name"))
        elif action == "kill":
            pid = kwargs.get("pid")
            if not pid:
                return "Kill action requires 'pid' parameter"
            return process_manager.kill_process_by_pid(int(pid))
        else:
            return f"Unsupported action: {action}"
    except Exception as e:
        return f"Process management failed: {str(e)}"


def get_system_status() -> str:
    """Get comprehensive system status."""
    return system_monitor.get_system_info()


def get_running_processes(limit: int = 10) -> str:
    """Get list of running processes."""
    return system_monitor.get_running_processes(limit)


def check_port_availability(port: int) -> str:
    """Check if a port is available."""
    return server_manager.check_port(port)


def install_server_dependencies() -> str:
    """Install required dependencies for server management."""
    try:
        dependencies = [
            "psutil>=5.8.0",
            "flask>=2.0.0",
        ]
        
        for dep in dependencies:
            subprocess.run(["pip", "install", dep], check=True, capture_output=True)
        
        return "Server management dependencies installed successfully"
    except subprocess.CalledProcessError as e:
        return f"Failed to install dependencies: {str(e)}"
    except Exception as e:
        return f"Installation error: {str(e)}"
