"""
Enhanced AI intelligence and reasoning tools for the ultimate CLI agent.
"""

import os
import json
import time
import hashlib
import pickle
from typing import Dict, List, Any, Optional, Union, Tuple
from pathlib import Path
import sqlite3
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import re
import ast
import subprocess


@dataclass
class TaskContext:
    """Context information for a task."""
    task_id: str
    description: str
    complexity_score: float
    estimated_steps: int
    dependencies: List[str]
    created_at: datetime
    status: str = "pending"
    progress: float = 0.0
    artifacts: Optional[List[str]] = None
    
    def __post_init__(self):
        if self.artifacts is None:
            self.artifacts = []


@dataclass
class KnowledgeEntry:
    """A piece of knowledge or learning."""
    id: str
    topic: str
    content: str
    source: str
    confidence: float
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    tags: Optional[List[str]] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class EnhancedMemory:
    """Advanced memory system with learning and reasoning capabilities."""
    
    def __init__(self, db_path: str = "enhanced_agent_memory.db"):
        self.db_path = db_path
        self.init_database()
        self.working_memory = {}
        self.reasoning_cache = {}
    
    def init_database(self):
        """Initialize the enhanced memory database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tasks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT PRIMARY KEY,
                description TEXT,
                complexity_score REAL,
                estimated_steps INTEGER,
                dependencies TEXT,
                created_at TEXT,
                status TEXT,
                progress REAL,
                artifacts TEXT
            )
        ''')
        
        # Knowledge base table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS knowledge (
                id TEXT PRIMARY KEY,
                topic TEXT,
                content TEXT,
                source TEXT,
                confidence REAL,
                created_at TEXT,
                last_accessed TEXT,
                access_count INTEGER,
                tags TEXT
            )
        ''')
        
        # Patterns and learnings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS patterns (
                id TEXT PRIMARY KEY,
                pattern_type TEXT,
                pattern_data TEXT,
                success_rate REAL,
                usage_count INTEGER,
                created_at TEXT,
                last_used TEXT
            )
        ''')
        
        # Command history with outcomes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS command_history (
                id TEXT PRIMARY KEY,
                command TEXT,
                context TEXT,
                outcome TEXT,
                success BOOLEAN,
                execution_time REAL,
                timestamp TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def store_task_context(self, task: TaskContext):
        """Store task context in memory."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO tasks 
            (task_id, description, complexity_score, estimated_steps, dependencies, 
             created_at, status, progress, artifacts)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            task.task_id,
            task.description,
            task.complexity_score,
            task.estimated_steps,
            json.dumps(task.dependencies),
            task.created_at.isoformat(),
            task.status,
            task.progress,
            json.dumps(task.artifacts)
        ))
        
        conn.commit()
        conn.close()
    
    def get_task_context(self, task_id: str) -> Optional[TaskContext]:
        """Retrieve task context from memory."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM tasks WHERE task_id = ?', (task_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return TaskContext(
                task_id=row[0],
                description=row[1],
                complexity_score=row[2],
                estimated_steps=row[3],
                dependencies=json.loads(row[4]),
                created_at=datetime.fromisoformat(row[5]),
                status=row[6],
                progress=row[7],
                artifacts=json.loads(row[8])
            )
        return None
    
    def store_knowledge(self, entry: KnowledgeEntry):
        """Store knowledge entry."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO knowledge 
            (id, topic, content, source, confidence, created_at, last_accessed, access_count, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            entry.id,
            entry.topic,
            entry.content,
            entry.source,
            entry.confidence,
            entry.created_at.isoformat(),
            entry.last_accessed.isoformat(),
            entry.access_count,
            json.dumps(entry.tags)
        ))
        
        conn.commit()
        conn.close()
    
    def query_knowledge(self, topic: str, confidence_threshold: float = 0.5) -> List[KnowledgeEntry]:
        """Query knowledge base by topic."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM knowledge 
            WHERE topic LIKE ? AND confidence >= ?
            ORDER BY confidence DESC, access_count DESC
        ''', (f'%{topic}%', confidence_threshold))
        
        entries = []
        for row in cursor.fetchall():
            entry = KnowledgeEntry(
                id=row[0],
                topic=row[1],
                content=row[2],
                source=row[3],
                confidence=row[4],
                created_at=datetime.fromisoformat(row[5]),
                last_accessed=datetime.fromisoformat(row[6]),
                access_count=row[7],
                tags=json.loads(row[8])
            )
            entries.append(entry)
        
        conn.close()
        return entries
    
    def store_command_outcome(self, command: str, context: str, outcome: str, 
                            success: bool, execution_time: float):
        """Store command execution outcome for learning."""
        command_id = hashlib.md5(f"{command}{context}{time.time()}".encode()).hexdigest()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO command_history 
            (id, command, context, outcome, success, execution_time, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            command_id,
            command,
            context,
            outcome,
            success,
            execution_time,
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    def get_similar_commands(self, command: str, limit: int = 5) -> List[Dict]:
        """Get similar commands from history."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Simple similarity based on command keywords
        words = command.lower().split()
        query_conditions = ' OR '.join([f'command LIKE ?' for _ in words])
        query_params = [f'%{word}%' for word in words]
        query_params.append(str(limit))
        
        cursor.execute(f'''
            SELECT command, context, outcome, success, execution_time 
            FROM command_history 
            WHERE {query_conditions}
            ORDER BY timestamp DESC
            LIMIT ?
        ''', query_params)
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "command": row[0],
                "context": row[1],
                "outcome": row[2],
                "success": row[3],
                "execution_time": row[4]
            })
        
        conn.close()
        return results


class ReasoningEngine:
    """Advanced reasoning and decision-making engine."""
    
    def __init__(self, memory: EnhancedMemory):
        self.memory = memory
        self.reasoning_strategies = {
            "sequential": self._sequential_reasoning,
            "parallel": self._parallel_reasoning,
            "recursive": self._recursive_reasoning,
            "adaptive": self._adaptive_reasoning
        }
    
    def analyze_task_complexity(self, task_description: str) -> float:
        """Analyze and score task complexity."""
        complexity_indicators = {
            # File operations
            "file": 0.2, "directory": 0.2, "folder": 0.2,
            "create": 0.3, "read": 0.3, "write": 0.3, "delete": 0.3,
            "copy": 0.4, "move": 0.4, "rename": 0.4,
            
            # Programming tasks
            "code": 0.5, "program": 0.5, "script": 0.5, "function": 0.5,
            "class": 0.6, "module": 0.6, "package": 0.6,
            "test": 0.7, "debug": 0.7, "optimize": 0.7,
            
            # System operations
            "install": 0.6, "configure": 0.6, "setup": 0.6,
            "server": 0.8, "service": 0.8, "daemon": 0.8,
            "database": 0.9, "network": 0.9, "security": 0.9,
            
            # Complex integrations
            "api": 0.7, "integration": 0.7, "automation": 0.7,
            "deploy": 0.9, "production": 0.9, "scale": 0.9,
            "machine learning": 1.0, "ai": 1.0, "model": 1.0
        }
        
        description_lower = task_description.lower()
        complexity_score = 0.1  # Base complexity
        
        for indicator, score in complexity_indicators.items():
            if indicator in description_lower:
                complexity_score += score
        
        # Adjust for task length and detail
        word_count = len(task_description.split())
        if word_count > 50:
            complexity_score += 0.3
        elif word_count > 20:
            complexity_score += 0.1
        
        return min(complexity_score, 1.0)
    
    def estimate_task_steps(self, task_description: str, complexity_score: float) -> int:
        """Estimate number of steps required for a task."""
        base_steps = max(1, int(complexity_score * 20))
        
        # Adjust based on task patterns
        if any(keyword in task_description.lower() for keyword in ["create", "build", "develop"]):
            base_steps += 5
        
        if any(keyword in task_description.lower() for keyword in ["test", "verify", "validate"]):
            base_steps += 3
        
        if any(keyword in task_description.lower() for keyword in ["deploy", "install", "configure"]):
            base_steps += 4
        
        return min(base_steps, 50)  # Cap at 50 steps
    
    def break_down_task(self, task_description: str) -> List[str]:
        """Break down a complex task into smaller subtasks."""
        subtasks = []
        
        # Basic task patterns
        if "create" in task_description.lower():
            if "file" in task_description.lower():
                subtasks.extend([
                    "Analyze file requirements",
                    "Create file structure",
                    "Implement file content",
                    "Validate file creation"
                ])
            elif "project" in task_description.lower():
                subtasks.extend([
                    "Set up project structure",
                    "Create main files",
                    "Configure dependencies",
                    "Implement core functionality",
                    "Add tests",
                    "Document the project"
                ])
            elif "server" in task_description.lower():
                subtasks.extend([
                    "Choose server technology",
                    "Set up server environment",
                    "Implement server logic",
                    "Configure routes/endpoints",
                    "Test server functionality",
                    "Deploy server"
                ])
        
        if "install" in task_description.lower():
            subtasks.extend([
                "Check system requirements",
                "Download/fetch packages",
                "Install dependencies",
                "Configure installation",
                "Verify installation"
            ])
        
        if "test" in task_description.lower():
            subtasks.extend([
                "Design test cases",
                "Implement test code",
                "Run tests",
                "Analyze test results",
                "Fix any issues"
            ])
        
        # If no specific patterns found, create generic subtasks
        if not subtasks:
            subtasks = [
                "Analyze requirements",
                "Plan implementation",
                "Execute main task",
                "Verify results"
            ]
        
        return subtasks
    
    def _sequential_reasoning(self, task: TaskContext) -> List[str]:
        """Sequential step-by-step reasoning."""
        return self.break_down_task(task.description)
    
    def _parallel_reasoning(self, task: TaskContext) -> List[str]:
        """Identify parallelizable subtasks."""
        subtasks = self.break_down_task(task.description)
        # Mark parallelizable tasks
        parallel_tasks = []
        for subtask in subtasks:
            if any(keyword in subtask.lower() for keyword in ["test", "validate", "check"]):
                parallel_tasks.append(f"[PARALLEL] {subtask}")
            else:
                parallel_tasks.append(subtask)
        return parallel_tasks
    
    def _recursive_reasoning(self, task: TaskContext) -> List[str]:
        """Break down complex tasks recursively."""
        subtasks = self.break_down_task(task.description)
        
        # Further break down complex subtasks
        detailed_tasks = []
        for subtask in subtasks:
            if task.complexity_score > 0.7:
                sub_breakdown = self.break_down_task(subtask)
                detailed_tasks.extend([f"  {sub}" for sub in sub_breakdown])
            else:
                detailed_tasks.append(subtask)
        
        return detailed_tasks
    
    def _adaptive_reasoning(self, task: TaskContext) -> List[str]:
        """Adaptive reasoning based on context and history."""
        # Check for similar tasks in history
        similar_commands = self.memory.get_similar_commands(task.description)
        
        if similar_commands:
            # Adapt based on previous experiences
            successful_patterns = [cmd for cmd in similar_commands if cmd["success"]]
            if successful_patterns:
                # Use successful patterns as a guide
                return [f"Apply pattern from: {pattern['command']}" for pattern in successful_patterns[:3]]
        
        # Fall back to complexity-based reasoning
        if task.complexity_score > 0.8:
            return self._recursive_reasoning(task)
        elif task.complexity_score > 0.5:
            return self._parallel_reasoning(task)
        else:
            return self._sequential_reasoning(task)
    
    def plan_task_execution(self, task_description: str, strategy: str = "adaptive") -> TaskContext:
        """Plan task execution using specified reasoning strategy."""
        task_id = hashlib.md5(f"{task_description}{time.time()}".encode()).hexdigest()[:8]
        complexity = self.analyze_task_complexity(task_description)
        estimated_steps = self.estimate_task_steps(task_description, complexity)
        
        task = TaskContext(
            task_id=task_id,
            description=task_description,
            complexity_score=complexity,
            estimated_steps=estimated_steps,
            dependencies=[],
            created_at=datetime.now()
        )
        
        # Apply reasoning strategy
        if strategy in self.reasoning_strategies:
            subtasks = self.reasoning_strategies[strategy](task)
            task.dependencies = subtasks
        
        # Store in memory
        self.memory.store_task_context(task)
        
        return task


class CodeAnalyzer:
    """Advanced code analysis and understanding."""
    
    def __init__(self):
        self.supported_languages = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.go': 'go',
            '.rs': 'rust',
            '.rb': 'ruby',
            '.php': 'php'
        }
    
    def analyze_code_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze a code file and extract insights."""
        try:
            if not os.path.exists(file_path):
                return {"error": f"File not found: {file_path}"}
            
            file_ext = Path(file_path).suffix
            if file_ext not in self.supported_languages:
                return {"error": f"Unsupported file type: {file_ext}"}
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            analysis = {
                "file_path": file_path,
                "language": self.supported_languages[file_ext],
                "size": len(content),
                "lines": len(content.splitlines()),
                "functions": [],
                "classes": [],
                "imports": [],
                "complexity_score": 0,
                "issues": []
            }
            
            # Language-specific analysis
            if file_ext == '.py':
                analysis.update(self._analyze_python_code(content))
            elif file_ext in ['.js', '.ts']:
                analysis.update(self._analyze_javascript_code(content))
            
            return analysis
        except Exception as e:
            return {"error": f"Analysis failed: {str(e)}"}
    
    def _analyze_python_code(self, content: str) -> Dict[str, Any]:
        """Analyze Python code specifically."""
        try:
            tree = ast.parse(content)
            
            functions = []
            classes = []
            imports = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions.append({
                        "name": node.name,
                        "line": node.lineno,
                        "args": [arg.arg for arg in node.args.args],
                        "docstring": ast.get_docstring(node)
                    })
                elif isinstance(node, ast.ClassDef):
                    classes.append({
                        "name": node.name,
                        "line": node.lineno,
                        "methods": [n.name for n in node.body if isinstance(n, ast.FunctionDef)],
                        "docstring": ast.get_docstring(node)
                    })
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    if isinstance(node, ast.Import):
                        imports.extend([alias.name for alias in node.names])
                    else:
                        imports.append(node.module)
            
            # Calculate complexity
            complexity = len(functions) * 2 + len(classes) * 3 + len(imports)
            
            return {
                "functions": functions,
                "classes": classes,
                "imports": list(set(imports)),
                "complexity_score": min(complexity / 10, 1.0)
            }
        except SyntaxError as e:
            return {"issues": [f"Syntax error: {str(e)}"]}
        except Exception as e:
            return {"issues": [f"Analysis error: {str(e)}"]}
    
    def _analyze_javascript_code(self, content: str) -> Dict[str, Any]:
        """Analyze JavaScript/TypeScript code."""
        # Basic pattern matching for JS/TS
        function_pattern = r'function\s+(\w+)\s*\('
        class_pattern = r'class\s+(\w+)'
        import_pattern = r'import\s+.*?from\s+[\'"]([^\'"]+)[\'"]'
        
        functions = re.findall(function_pattern, content)
        classes = re.findall(class_pattern, content)
        imports = re.findall(import_pattern, content)
        
        return {
            "functions": [{"name": f, "line": 0} for f in functions],
            "classes": [{"name": c, "line": 0} for c in classes],
            "imports": imports,
            "complexity_score": min((len(functions) * 2 + len(classes) * 3) / 10, 1.0)
        }
    
    def suggest_improvements(self, analysis: Dict[str, Any]) -> List[str]:
        """Suggest code improvements based on analysis."""
        suggestions = []
        
        if analysis.get("complexity_score", 0) > 0.8:
            suggestions.append("Consider breaking down complex functions into smaller ones")
        
        if not analysis.get("functions") and not analysis.get("classes"):
            suggestions.append("Consider organizing code into functions or classes")
        
        if len(analysis.get("imports", [])) > 10:
            suggestions.append("Consider reducing the number of imports")
        
        functions = analysis.get("functions", [])
        for func in functions:
            if not func.get("docstring"):
                suggestions.append(f"Add documentation for function '{func['name']}'")
        
        return suggestions


# Global instances
enhanced_memory = EnhancedMemory()
reasoning_engine = ReasoningEngine(enhanced_memory)
code_analyzer = CodeAnalyzer()


# Tool functions for the agent
def analyze_task_intelligence(task_description: str, strategy: str = "adaptive") -> str:
    """Analyze task with advanced intelligence and create execution plan."""
    try:
        task_context = reasoning_engine.plan_task_execution(task_description, strategy)
        
        result = {
            "task_id": task_context.task_id,
            "complexity_score": task_context.complexity_score,
            "estimated_steps": task_context.estimated_steps,
            "reasoning_strategy": strategy,
            "subtasks": task_context.dependencies,
            "recommendations": []
        }
        
        # Add recommendations based on complexity
        if task_context.complexity_score > 0.8:
            result["recommendations"].append("High complexity task - consider breaking into smaller parts")
            result["recommendations"].append("Implement comprehensive testing")
            result["recommendations"].append("Create backup before making changes")
        elif task_context.complexity_score > 0.5:
            result["recommendations"].append("Medium complexity task - plan execution carefully")
            result["recommendations"].append("Test incrementally")
        
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Task analysis failed: {str(e)}"


def learn_from_execution(command: str, context: str, outcome: str, success: bool, execution_time: float = 0.0) -> str:
    """Learn from command execution to improve future decisions."""
    try:
        enhanced_memory.store_command_outcome(command, context, outcome, success, execution_time)
        
        # Store knowledge if successful
        if success:
            knowledge_id = hashlib.md5(f"{command}{context}".encode()).hexdigest()[:8]
            knowledge = KnowledgeEntry(
                id=knowledge_id,
                topic=command.split()[0] if command.split() else "general",
                content=f"Command: {command}\nContext: {context}\nOutcome: {outcome}",
                source="execution_experience",
                confidence=0.8,
                created_at=datetime.now(),
                last_accessed=datetime.now(),
                tags=["command", "success"]
            )
            enhanced_memory.store_knowledge(knowledge)
        
        return f"Learning recorded: {'success' if success else 'failure'} for command '{command[:50]}...'"
    except Exception as e:
        return f"Learning failed: {str(e)}"


def query_knowledge_base(topic: str, confidence_threshold: float = 0.5) -> str:
    """Query the knowledge base for relevant information."""
    try:
        entries = enhanced_memory.query_knowledge(topic, confidence_threshold)
        
        if not entries:
            return f"No knowledge found for topic: {topic}"
        
        result = {
            "topic": topic,
            "entries_found": len(entries),
            "knowledge": []
        }
        
        for entry in entries[:5]:  # Limit to top 5 results
            result["knowledge"].append({
                "id": entry.id,
                "content": entry.content[:200] + "..." if len(entry.content) > 200 else entry.content,
                "confidence": entry.confidence,
                "source": entry.source,
                "tags": entry.tags
            })
        
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Knowledge query failed: {str(e)}"


def analyze_code_intelligence(file_path: str) -> str:
    """Analyze code with advanced intelligence."""
    try:
        analysis = code_analyzer.analyze_code_file(file_path)
        
        if "error" in analysis:
            return json.dumps(analysis)
        
        # Add improvement suggestions
        analysis["suggestions"] = code_analyzer.suggest_improvements(analysis)
        
        return json.dumps(analysis, indent=2)
    except Exception as e:
        return f"Code analysis failed: {str(e)}"


def get_similar_solutions(problem_description: str) -> str:
    """Get similar solutions from command history."""
    try:
        similar_commands = enhanced_memory.get_similar_commands(problem_description)
        
        if not similar_commands:
            return "No similar solutions found in history"
        
        result = {
            "problem": problem_description,
            "similar_solutions": similar_commands
        }
        
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Solution search failed: {str(e)}"


def enhance_reasoning_capability() -> str:
    """Enhance the agent's reasoning capabilities."""
    try:
        # This could trigger learning from additional sources
        # For now, return current capabilities
        capabilities = {
            "reasoning_strategies": list(reasoning_engine.reasoning_strategies.keys()),
            "supported_languages": list(code_analyzer.supported_languages.values()),
            "memory_systems": ["working_memory", "long_term_memory", "knowledge_base"],
            "learning_capabilities": ["command_outcomes", "pattern_recognition", "adaptive_planning"]
        }
        
        return json.dumps(capabilities, indent=2)
    except Exception as e:
        return f"Capability enhancement failed: {str(e)}"
