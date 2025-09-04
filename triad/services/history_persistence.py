"""
SQLite History Persistence Service

Provides comprehensive history persistence for chat messages, agent interactions,
commands, and multi-assistant conversations using SQLite with async support.
"""

from __future__ import annotations

import asyncio
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import aiosqlite
from sqlalchemy import text


class HistoryPersistenceService:
    """SQLite-based history persistence for Triad Terminal multi-assistant system."""

    def __init__(self, db_path: str | Path = "~/.triad/history.db"):
        self.db_path = Path(db_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the database schema."""
        if self._initialized:
            return

        async with aiosqlite.connect(self.db_path) as db:
            # Chat messages and agent interactions
            await db.execute("""
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    room TEXT NOT NULL,
                    sender TEXT NOT NULL,
                    content TEXT NOT NULL,
                    role TEXT,
                    timestamp REAL NOT NULL,
                    metadata TEXT,  -- JSON
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Command history 
            await db.execute("""
                CREATE TABLE IF NOT EXISTS command_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    command TEXT NOT NULL,
                    context TEXT,
                    success BOOLEAN,
                    output TEXT,
                    error_message TEXT,
                    user_id TEXT,
                    session_id TEXT,
                    timestamp REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Assistant interactions and predictions
            await db.execute("""
                CREATE TABLE IF NOT EXISTS assistant_interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    assistant_type TEXT NOT NULL,
                    request_type TEXT NOT NULL,
                    input_data TEXT,  -- JSON
                    output_data TEXT,  -- JSON
                    confidence_score REAL,
                    processing_time_ms INTEGER,
                    session_id TEXT,
                    timestamp REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Multi-assistant sessions 
            await db.execute("""
                CREATE TABLE IF NOT EXISTS multi_assistant_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE NOT NULL,
                    session_name TEXT,
                    active_assistants TEXT,  -- JSON list
                    room_config TEXT,  -- JSON
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ended_at TIMESTAMP,
                    status TEXT DEFAULT 'active'
                )
            """)

            # Dataset usage tracking
            await db.execute("""
                CREATE TABLE IF NOT EXISTS dataset_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dataset_id TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    assistant_type TEXT,
                    session_id TEXT,
                    metadata TEXT,  -- JSON
                    timestamp REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create indexes for better performance
            await db.execute("CREATE INDEX IF NOT EXISTS idx_chat_room ON chat_messages(room)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_chat_timestamp ON chat_messages(timestamp)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_command_session ON command_history(session_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_assistant_type ON assistant_interactions(assistant_type)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_session_id ON multi_assistant_sessions(session_id)")

            await db.commit()

        self._initialized = True

    async def store_chat_message(
        self, 
        room: str, 
        sender: str, 
        content: str, 
        role: str = None,
        timestamp: float = None,
        metadata: Dict[str, Any] = None
    ) -> int:
        """Store a chat message."""
        await self.initialize()
        
        if timestamp is None:
            timestamp = datetime.now(timezone.utc).timestamp()

        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO chat_messages (room, sender, content, role, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                room, sender, content, role, timestamp, 
                json.dumps(metadata) if metadata else None
            ))
            await db.commit()
            return cursor.lastrowid

    async def store_command(
        self,
        command: str,
        context: str = None,
        success: bool = None,
        output: str = None,
        error_message: str = None,
        user_id: str = None,
        session_id: str = None
    ) -> int:
        """Store a command execution record."""
        await self.initialize()
        
        timestamp = datetime.now(timezone.utc).timestamp()

        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO command_history 
                (command, context, success, output, error_message, user_id, session_id, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (command, context, success, output, error_message, user_id, session_id, timestamp))
            await db.commit()
            return cursor.lastrowid

    async def store_assistant_interaction(
        self,
        assistant_type: str,
        request_type: str,
        input_data: Dict[str, Any] = None,
        output_data: Dict[str, Any] = None,
        confidence_score: float = None,
        processing_time_ms: int = None,
        session_id: str = None
    ) -> int:
        """Store an assistant interaction."""
        await self.initialize()
        
        timestamp = datetime.now(timezone.utc).timestamp()

        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO assistant_interactions 
                (assistant_type, request_type, input_data, output_data, confidence_score, 
                 processing_time_ms, session_id, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                assistant_type, request_type,
                json.dumps(input_data) if input_data else None,
                json.dumps(output_data) if output_data else None,
                confidence_score, processing_time_ms, session_id, timestamp
            ))
            await db.commit()
            return cursor.lastrowid

    async def create_multi_assistant_session(
        self,
        session_id: str,
        session_name: str = None,
        active_assistants: List[str] = None,
        room_config: Dict[str, Any] = None
    ) -> int:
        """Create a new multi-assistant session."""
        await self.initialize()

        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO multi_assistant_sessions 
                (session_id, session_name, active_assistants, room_config)
                VALUES (?, ?, ?, ?)
            """, (
                session_id, session_name,
                json.dumps(active_assistants) if active_assistants else None,
                json.dumps(room_config) if room_config else None
            ))
            await db.commit()
            return cursor.lastrowid

    async def get_chat_history(
        self, 
        room: str = None, 
        limit: int = 100,
        offset: int = 0,
        start_time: float = None,
        end_time: float = None
    ) -> List[Dict[str, Any]]:
        """Retrieve chat message history."""
        await self.initialize()

        query = "SELECT * FROM chat_messages WHERE 1=1"
        params = []

        if room:
            query += " AND room = ?"
            params.append(room)
        
        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time)
            
        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time)

        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(query, params)
            rows = await cursor.fetchall()
            
            results = []
            for row in rows:
                result = dict(row)
                if result['metadata']:
                    result['metadata'] = json.loads(result['metadata'])
                results.append(result)
            
            return results

    async def get_command_history(
        self, 
        session_id: str = None,
        user_id: str = None,
        limit: int = 100,
        success_only: bool = None
    ) -> List[Dict[str, Any]]:
        """Retrieve command execution history."""
        await self.initialize()

        query = "SELECT * FROM command_history WHERE 1=1"
        params = []

        if session_id:
            query += " AND session_id = ?"
            params.append(session_id)

        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)
            
        if success_only is not None:
            query += " AND success = ?"
            params.append(success_only)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(query, params)
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_assistant_interactions(
        self,
        assistant_type: str = None,
        request_type: str = None,
        session_id: str = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Retrieve assistant interaction history."""
        await self.initialize()

        query = "SELECT * FROM assistant_interactions WHERE 1=1"
        params = []

        if assistant_type:
            query += " AND assistant_type = ?"
            params.append(assistant_type)

        if request_type:
            query += " AND request_type = ?"
            params.append(request_type)
            
        if session_id:
            query += " AND session_id = ?"
            params.append(session_id)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(query, params)
            rows = await cursor.fetchall()
            
            results = []
            for row in rows:
                result = dict(row)
                if result['input_data']:
                    result['input_data'] = json.loads(result['input_data'])
                if result['output_data']:
                    result['output_data'] = json.loads(result['output_data'])
                results.append(result)
            
            return results

    async def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """Get statistics for a multi-assistant session."""
        await self.initialize()

        async with aiosqlite.connect(self.db_path) as db:
            # Get session info
            session_cursor = await db.execute(
                "SELECT * FROM multi_assistant_sessions WHERE session_id = ?",
                (session_id,)
            )
            session = await session_cursor.fetchone()
            
            if not session:
                return {}

            # Get message count
            msg_cursor = await db.execute(
                "SELECT COUNT(*) as count FROM chat_messages WHERE room = ?",
                (session_id,)  # Assuming room name matches session_id
            )
            msg_count = await msg_cursor.fetchone()

            # Get command count
            cmd_cursor = await db.execute(
                "SELECT COUNT(*) as count FROM command_history WHERE session_id = ?",
                (session_id,)
            )
            cmd_count = await cmd_cursor.fetchone()

            # Get assistant interaction count
            ai_cursor = await db.execute(
                "SELECT COUNT(*) as count FROM assistant_interactions WHERE session_id = ?",
                (session_id,)
            )
            ai_count = await ai_cursor.fetchone()

            return {
                "session_info": dict(session) if session else {},
                "message_count": msg_count[0] if msg_count else 0,
                "command_count": cmd_count[0] if cmd_count else 0,
                "assistant_interaction_count": ai_count[0] if ai_count else 0,
            }

    async def cleanup_old_records(self, days_old: int = 30) -> Dict[str, int]:
        """Clean up records older than specified days."""
        await self.initialize()
        
        cutoff_time = datetime.now(timezone.utc).timestamp() - (days_old * 24 * 60 * 60)
        
        deleted_counts = {}
        
        async with aiosqlite.connect(self.db_path) as db:
            # Clean chat messages
            cursor = await db.execute(
                "DELETE FROM chat_messages WHERE timestamp < ?", (cutoff_time,)
            )
            deleted_counts['chat_messages'] = cursor.rowcount

            # Clean command history
            cursor = await db.execute(
                "DELETE FROM command_history WHERE timestamp < ?", (cutoff_time,)
            )
            deleted_counts['command_history'] = cursor.rowcount

            # Clean assistant interactions
            cursor = await db.execute(
                "DELETE FROM assistant_interactions WHERE timestamp < ?", (cutoff_time,)
            )
            deleted_counts['assistant_interactions'] = cursor.rowcount

            await db.commit()

        return deleted_counts