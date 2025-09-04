"""
Dataset Catalog Service

Manages and catalogs datasets used by assistants, including metadata,
usage tracking, and discovery functionality.
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import aiosqlite
import pandas as pd


class DatasetCatalogService:
    """Catalog and management system for datasets used by Triad Terminal assistants."""

    def __init__(self, catalog_dir: str | Path = "~/.triad/datasets"):
        self.catalog_dir = Path(catalog_dir).expanduser()
        self.catalog_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.catalog_dir / "catalog.db"
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the catalog database schema."""
        if self._initialized:
            return

        async with aiosqlite.connect(self.db_path) as db:
            # Main dataset catalog
            await db.execute("""
                CREATE TABLE IF NOT EXISTS datasets (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    type TEXT NOT NULL,  -- 'csv', 'json', 'parquet', 'text', etc.
                    path TEXT NOT NULL,  -- relative to catalog_dir
                    size_bytes INTEGER,
                    rows INTEGER,
                    columns INTEGER,
                    schema_info TEXT,  -- JSON description of columns/structure
                    tags TEXT,  -- JSON array of tags
                    source_url TEXT,
                    version TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_accessed TIMESTAMP,
                    access_count INTEGER DEFAULT 0,
                    metadata TEXT  -- JSON for additional metadata
                )
            """)

            # Dataset usage log
            await db.execute("""
                CREATE TABLE IF NOT EXISTS dataset_usage_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dataset_id TEXT NOT NULL,
                    operation TEXT NOT NULL,  -- 'read', 'write', 'analyze', etc.
                    assistant_type TEXT,
                    session_id TEXT,
                    rows_processed INTEGER,
                    processing_time_ms INTEGER,
                    success BOOLEAN DEFAULT TRUE,
                    error_message TEXT,
                    timestamp REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (dataset_id) REFERENCES datasets (id)
                )
            """)

            # Dataset relationships (for datasets derived from others)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS dataset_relationships (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    parent_dataset_id TEXT NOT NULL,
                    child_dataset_id TEXT NOT NULL,
                    relationship_type TEXT NOT NULL,  -- 'derived', 'filtered', 'merged', etc.
                    transformation_info TEXT,  -- JSON description of transformation
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (parent_dataset_id) REFERENCES datasets (id),
                    FOREIGN KEY (child_dataset_id) REFERENCES datasets (id)
                )
            """)

            # Create indexes
            await db.execute("CREATE INDEX IF NOT EXISTS idx_dataset_type ON datasets(type)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_dataset_tags ON datasets(tags)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_usage_dataset ON dataset_usage_log(dataset_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_usage_timestamp ON dataset_usage_log(timestamp)")

            await db.commit()

        self._initialized = True

    async def add_dataset(
        self,
        dataset_id: str,
        name: str,
        file_path: Union[str, Path],
        description: str = None,
        tags: List[str] = None,
        source_url: str = None,
        version: str = "1.0",
        metadata: Dict[str, Any] = None,
        copy_file: bool = True
    ) -> Dict[str, Any]:
        """Add a new dataset to the catalog."""
        await self.initialize()

        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Dataset file not found: {file_path}")

        # Determine dataset type from file extension
        dataset_type = self._detect_dataset_type(file_path)
        
        # Copy file to catalog directory if requested
        if copy_file:
            catalog_file_path = self.catalog_dir / f"{dataset_id}{file_path.suffix}"
            shutil.copy2(file_path, catalog_file_path)
            relative_path = catalog_file_path.name
        else:
            relative_path = str(file_path.absolute())

        # Analyze dataset structure
        structure_info = await self._analyze_dataset_structure(file_path, dataset_type)
        
        dataset_info = {
            "id": dataset_id,
            "name": name,
            "description": description,
            "type": dataset_type,
            "path": relative_path,
            "size_bytes": file_path.stat().st_size,
            "rows": structure_info.get("rows"),
            "columns": structure_info.get("columns"),
            "schema_info": json.dumps(structure_info.get("schema", {})),
            "tags": json.dumps(tags or []),
            "source_url": source_url,
            "version": version,
            "metadata": json.dumps(metadata or {})
        }

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO datasets 
                (id, name, description, type, path, size_bytes, rows, columns,
                 schema_info, tags, source_url, version, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                dataset_info["id"], dataset_info["name"], dataset_info["description"],
                dataset_info["type"], dataset_info["path"], dataset_info["size_bytes"],
                dataset_info["rows"], dataset_info["columns"], dataset_info["schema_info"],
                dataset_info["tags"], dataset_info["source_url"], dataset_info["version"],
                dataset_info["metadata"]
            ))
            await db.commit()

        return dataset_info

    async def get_dataset(self, dataset_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve dataset information."""
        await self.initialize()

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM datasets WHERE id = ?", (dataset_id,))
            row = await cursor.fetchone()
            
            if not row:
                return None

            result = dict(row)
            result["tags"] = json.loads(result["tags"]) if result["tags"] else []
            result["schema_info"] = json.loads(result["schema_info"]) if result["schema_info"] else {}
            result["metadata"] = json.loads(result["metadata"]) if result["metadata"] else {}
            
            return result

    async def list_datasets(
        self,
        dataset_type: str = None,
        tags: List[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List datasets with optional filtering."""
        await self.initialize()

        query = "SELECT * FROM datasets WHERE 1=1"
        params = []

        if dataset_type:
            query += " AND type = ?"
            params.append(dataset_type)

        if tags:
            # Simple tag matching - in production, you might want more sophisticated tag queries
            for tag in tags:
                query += " AND tags LIKE ?"
                params.append(f"%{tag}%")

        query += " ORDER BY updated_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(query, params)
            rows = await cursor.fetchall()
            
            results = []
            for row in rows:
                result = dict(row)
                result["tags"] = json.loads(result["tags"]) if result["tags"] else []
                result["schema_info"] = json.loads(result["schema_info"]) if result["schema_info"] else {}
                result["metadata"] = json.loads(result["metadata"]) if result["metadata"] else {}
                results.append(result)
            
            return results

    async def update_dataset(
        self,
        dataset_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """Update dataset information."""
        await self.initialize()

        # Prepare update fields
        set_clauses = []
        params = []
        
        allowed_fields = ["name", "description", "tags", "source_url", "version", "metadata"]
        
        for field, value in updates.items():
            if field in allowed_fields:
                if field in ["tags", "metadata"]:
                    value = json.dumps(value)
                set_clauses.append(f"{field} = ?")
                params.append(value)

        if not set_clauses:
            return False

        set_clauses.append("updated_at = CURRENT_TIMESTAMP")
        query = f"UPDATE datasets SET {', '.join(set_clauses)} WHERE id = ?"
        params.append(dataset_id)

        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(query, params)
            await db.commit()
            return cursor.rowcount > 0

    async def delete_dataset(self, dataset_id: str, remove_file: bool = True) -> bool:
        """Delete a dataset from the catalog."""
        await self.initialize()

        # Get dataset info first
        dataset = await self.get_dataset(dataset_id)
        if not dataset:
            return False

        async with aiosqlite.connect(self.db_path) as db:
            # Delete relationships
            await db.execute(
                "DELETE FROM dataset_relationships WHERE parent_dataset_id = ? OR child_dataset_id = ?",
                (dataset_id, dataset_id)
            )
            
            # Delete usage log
            await db.execute("DELETE FROM dataset_usage_log WHERE dataset_id = ?", (dataset_id,))
            
            # Delete main record
            cursor = await db.execute("DELETE FROM datasets WHERE id = ?", (dataset_id,))
            await db.commit()
            
            success = cursor.rowcount > 0

        # Remove file if requested and it's in catalog directory
        if success and remove_file:
            file_path = Path(dataset["path"])
            if not file_path.is_absolute():
                file_path = self.catalog_dir / file_path
                
            if file_path.exists() and file_path.parent == self.catalog_dir:
                file_path.unlink()

        return success

    async def log_dataset_usage(
        self,
        dataset_id: str,
        operation: str,
        assistant_type: str = None,
        session_id: str = None,
        rows_processed: int = None,
        processing_time_ms: int = None,
        success: bool = True,
        error_message: str = None
    ) -> int:
        """Log dataset usage."""
        await self.initialize()

        timestamp = datetime.now(timezone.utc).timestamp()

        async with aiosqlite.connect(self.db_path) as db:
            # Log usage
            cursor = await db.execute("""
                INSERT INTO dataset_usage_log 
                (dataset_id, operation, assistant_type, session_id, rows_processed,
                 processing_time_ms, success, error_message, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                dataset_id, operation, assistant_type, session_id, rows_processed,
                processing_time_ms, success, error_message, timestamp
            ))

            # Update dataset access info
            await db.execute("""
                UPDATE datasets 
                SET last_accessed = CURRENT_TIMESTAMP, access_count = access_count + 1
                WHERE id = ?
            """, (dataset_id,))

            await db.commit()
            return cursor.lastrowid

    async def get_dataset_usage_stats(self, dataset_id: str) -> Dict[str, Any]:
        """Get usage statistics for a dataset."""
        await self.initialize()

        async with aiosqlite.connect(self.db_path) as db:
            # Total usage count
            total_cursor = await db.execute(
                "SELECT COUNT(*) as count FROM dataset_usage_log WHERE dataset_id = ?",
                (dataset_id,)
            )
            total_count = await total_cursor.fetchone()

            # Usage by operation
            ops_cursor = await db.execute("""
                SELECT operation, COUNT(*) as count 
                FROM dataset_usage_log 
                WHERE dataset_id = ? 
                GROUP BY operation
            """, (dataset_id,))
            operations = await ops_cursor.fetchall()

            # Recent usage
            recent_cursor = await db.execute("""
                SELECT * FROM dataset_usage_log 
                WHERE dataset_id = ? 
                ORDER BY timestamp DESC 
                LIMIT 10
            """, (dataset_id,))
            recent_cursor.row_factory = aiosqlite.Row
            recent_usage = [dict(row) for row in await recent_cursor.fetchall()]

            return {
                "total_usage_count": total_count[0] if total_count else 0,
                "operations": {op[0]: op[1] for op in operations},
                "recent_usage": recent_usage
            }

    async def search_datasets(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search datasets by name, description, or tags."""
        await self.initialize()

        search_query = f"%{query.lower()}%"

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM datasets 
                WHERE LOWER(name) LIKE ? 
                   OR LOWER(description) LIKE ? 
                   OR LOWER(tags) LIKE ?
                ORDER BY access_count DESC, updated_at DESC
                LIMIT ?
            """, (search_query, search_query, search_query, limit))
            
            rows = await cursor.fetchall()
            
            results = []
            for row in rows:
                result = dict(row)
                result["tags"] = json.loads(result["tags"]) if result["tags"] else []
                result["schema_info"] = json.loads(result["schema_info"]) if result["schema_info"] else {}
                result["metadata"] = json.loads(result["metadata"]) if result["metadata"] else {}
                results.append(result)
            
            return results

    def _detect_dataset_type(self, file_path: Path) -> str:
        """Detect dataset type from file extension."""
        suffix = file_path.suffix.lower()
        type_map = {
            '.csv': 'csv',
            '.json': 'json',
            '.jsonl': 'jsonl',
            '.parquet': 'parquet',
            '.txt': 'text',
            '.tsv': 'tsv',
            '.xlsx': 'excel',
            '.xls': 'excel',
        }
        return type_map.get(suffix, 'unknown')

    async def _analyze_dataset_structure(self, file_path: Path, dataset_type: str) -> Dict[str, Any]:
        """Analyze dataset structure to extract schema information."""
        try:
            if dataset_type == 'csv':
                df = pd.read_csv(file_path, nrows=1000)  # Sample first 1000 rows
                return {
                    "rows": len(df),
                    "columns": len(df.columns),
                    "schema": {
                        col: str(df[col].dtype) for col in df.columns
                    },
                    "sample_data": df.head().to_dict('records')
                }
            elif dataset_type == 'json':
                with open(file_path) as f:
                    data = json.load(f)
                    
                if isinstance(data, list):
                    return {
                        "rows": len(data),
                        "columns": len(data[0].keys()) if data else 0,
                        "schema": self._infer_json_schema(data[:100]),  # Sample first 100 items
                        "sample_data": data[:5]
                    }
                else:
                    return {
                        "rows": 1,
                        "columns": len(data.keys()) if isinstance(data, dict) else 0,
                        "schema": self._infer_json_schema([data]),
                        "sample_data": [data]
                    }
            elif dataset_type == 'parquet':
                df = pd.read_parquet(file_path)
                return {
                    "rows": len(df),
                    "columns": len(df.columns),
                    "schema": {
                        col: str(df[col].dtype) for col in df.columns
                    },
                    "sample_data": df.head().to_dict('records')
                }
            else:
                # For other types, just return basic file info
                return {
                    "rows": None,
                    "columns": None,
                    "schema": {},
                    "sample_data": []
                }
                
        except Exception as e:
            return {
                "rows": None,
                "columns": None,
                "schema": {},
                "sample_data": [],
                "analysis_error": str(e)
            }

    def _infer_json_schema(self, data_list: List[Dict]) -> Dict[str, str]:
        """Infer schema from JSON data."""
        if not data_list:
            return {}
            
        schema = {}
        for item in data_list:
            if isinstance(item, dict):
                for key, value in item.items():
                    if key not in schema:
                        schema[key] = type(value).__name__
        
        return schema

    async def get_catalog_stats(self) -> Dict[str, Any]:
        """Get overall catalog statistics."""
        await self.initialize()

        async with aiosqlite.connect(self.db_path) as db:
            # Total datasets
            total_cursor = await db.execute("SELECT COUNT(*) as count FROM datasets")
            total_count = await total_cursor.fetchone()

            # By type
            type_cursor = await db.execute("""
                SELECT type, COUNT(*) as count 
                FROM datasets 
                GROUP BY type
            """)
            types = await type_cursor.fetchall()

            # Total size
            size_cursor = await db.execute("SELECT SUM(size_bytes) as total_size FROM datasets")
            total_size = await size_cursor.fetchone()

            # Most used datasets
            popular_cursor = await db.execute("""
                SELECT id, name, access_count 
                FROM datasets 
                ORDER BY access_count DESC 
                LIMIT 10
            """)
            popular_cursor.row_factory = aiosqlite.Row
            popular_datasets = [dict(row) for row in await popular_cursor.fetchall()]

            return {
                "total_datasets": total_count[0] if total_count else 0,
                "datasets_by_type": {t[0]: t[1] for t in types},
                "total_size_bytes": total_size[0] if total_size and total_size[0] else 0,
                "popular_datasets": popular_datasets
            }