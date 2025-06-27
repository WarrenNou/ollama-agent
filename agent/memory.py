"""
Advanced memory management system for the Ollama agent.
Provides persistent storage, learning from mistakes, and context retention.
"""

import json
import sqlite3
import os
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path


@dataclass
class MemoryEntry:
    """Represents a single memory entry."""
    id: str
    timestamp: datetime
    category: str
    content: Dict[str, Any]
    importance: float
    tags: List[str]
    success: bool


class MemoryManager:
    """Advanced memory management system for the agent."""
    
    def __init__(self, db_path: str = "agent_memory.db"):
        self.db_path = db_path
        self._init_database()
        self.short_term_memory: List[Dict] = []
        self.working_memory: Dict[str, Any] = {}
        
    def _init_database(self):
        """Initialize the SQLite database for persistent memory."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                timestamp TEXT,
                category TEXT,
                content TEXT,
                importance REAL,
                tags TEXT,
                success INTEGER
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS learned_patterns (
                id TEXT PRIMARY KEY,
                pattern_type TEXT,
                pattern_data TEXT,
                success_rate REAL,
                usage_count INTEGER,
                last_used TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS error_patterns (
                id TEXT PRIMARY KEY,
                error_type TEXT,
                error_context TEXT,
                solution TEXT,
                effectiveness REAL,
                created_at TEXT
            )
        """)
        
        conn.commit()
        conn.close()
    
    def store_memory(self, category: str, content: Dict[str, Any], 
                     importance: float = 0.5, tags: List[str] = None, 
                     success: bool = True) -> str:
        """Store a memory entry in the database."""
        memory_id = hashlib.md5(
            f"{category}_{json.dumps(content, sort_keys=True)}_{datetime.now().isoformat()}"
            .encode()
        ).hexdigest()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO memories 
            (id, timestamp, category, content, importance, tags, success)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            memory_id,
            datetime.now().isoformat(),
            category,
            json.dumps(content),
            importance,
            json.dumps(tags or []),
            int(success)
        ))
        
        conn.commit()
        conn.close()
        
        return memory_id
    
    def retrieve_memories(self, category: str = None, tags: List[str] = None,
                         min_importance: float = 0.0, limit: int = 100) -> List[MemoryEntry]:
        """Retrieve memories based on filters."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT * FROM memories WHERE importance >= ?"
        params = [min_importance]
        
        if category:
            query += " AND category = ?"
            params.append(category)
        
        query += " ORDER BY importance DESC, timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        memories = []
        for row in rows:
            memory = MemoryEntry(
                id=row[0],
                timestamp=datetime.fromisoformat(row[1]),
                category=row[2],
                content=json.loads(row[3]),
                importance=row[4],
                tags=json.loads(row[5]),
                success=bool(row[6])
            )
            
            # Filter by tags if specified
            if tags and not any(tag in memory.tags for tag in tags):
                continue
                
            memories.append(memory)
        
        return memories
    
    def learn_from_error(self, error_type: str, error_context: str, 
                        solution: str = None, effectiveness: float = 0.0):
        """Learn from errors and store solutions."""
        error_id = hashlib.md5(f"{error_type}_{error_context}".encode()).hexdigest()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO error_patterns 
            (id, error_type, error_context, solution, effectiveness, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            error_id,
            error_type,
            error_context,
            solution or "",
            effectiveness,
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    def get_error_solutions(self, error_type: str, context: str = None) -> List[Dict]:
        """Get known solutions for similar errors."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT * FROM error_patterns WHERE error_type = ?"
        params = [error_type]
        
        if context:
            query += " AND error_context LIKE ?"
            params.append(f"%{context}%")
        
        query += " ORDER BY effectiveness DESC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "id": row[0],
                "error_type": row[1],
                "error_context": row[2],
                "solution": row[3],
                "effectiveness": row[4],
                "created_at": row[5]
            }
            for row in rows
        ]
    
    def update_working_memory(self, key: str, value: Any):
        """Update working memory with key-value pairs."""
        self.working_memory[key] = value
    
    def get_working_memory(self, key: str = None) -> Any:
        """Get value from working memory."""
        if key:
            return self.working_memory.get(key)
        return self.working_memory
    
    def clear_working_memory(self):
        """Clear working memory."""
        self.working_memory.clear()
    
    def add_to_short_term(self, item: Dict[str, Any]):
        """Add item to short-term memory."""
        self.short_term_memory.append({
            **item,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep only recent items (last 50)
        if len(self.short_term_memory) > 50:
            self.short_term_memory = self.short_term_memory[-50:]
    
    def get_relevant_context(self, goal: str, max_items: int = 10) -> str:
        """Get relevant context for a goal from memory."""
        # Get recent successful memories
        recent_memories = self.retrieve_memories(
            min_importance=0.3,
            limit=max_items
        )
        
        context_parts = []
        
        # Add working memory
        if self.working_memory:
            context_parts.append("Current Working Memory:")
            for key, value in self.working_memory.items():
                context_parts.append(f"  {key}: {value}")
        
        # Add recent memories
        if recent_memories:
            context_parts.append("\nRelevant Past Experiences:")
            for memory in recent_memories[:max_items//2]:
                if memory.success:
                    context_parts.append(f"  - {memory.category}: {memory.content}")
        
        # Add short-term memory
        if self.short_term_memory:
            context_parts.append("\nRecent Actions:")
            for item in self.short_term_memory[-5:]:
                context_parts.append(f"  - {item}")
        
        return "\n".join(context_parts)
    
    def cleanup_old_memories(self, days: int = 30):
        """Clean up old, low-importance memories."""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM memories 
            WHERE timestamp < ? AND importance < 0.3
        """, (cutoff_date.isoformat(),))
        
        conn.commit()
        conn.close()
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get statistics about stored memories."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM memories")
        total_memories = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM memories WHERE success = 1")
        successful_memories = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM error_patterns")
        error_patterns = cursor.fetchone()[0]
        
        cursor.execute("SELECT category, COUNT(*) FROM memories GROUP BY category")
        categories = dict(cursor.fetchall())
        
        conn.close()
        
        return {
            "total_memories": total_memories,
            "successful_memories": successful_memories,
            "error_patterns": error_patterns,
            "categories": categories,
            "working_memory_size": len(self.working_memory),
            "short_term_memory_size": len(self.short_term_memory)
        }
