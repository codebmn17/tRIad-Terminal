#!/usr/bin/env python3

"""
Triad Terminal Database Manager
Provides database functionality for the terminal
"""

import os
import sys
import json
import time
import sqlite3
import logging
import threading
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union

logger = logging.getLogger("triad.database")

class DatabaseManager:
    """Manages database connections and operations"""
    
    def __init__(self, data_dir: str = "~/.triad/databases"):
        self.data_dir = os.path.expanduser(data_dir)
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Track connections
        self.connections = {}
        self.connection_lock = threading.Lock()
    
    def list_databases(self) -> List[str]:
        """List available databases"""
        databases = []
        
        for file in os.listdir(self.data_dir):
            if file.endswith('.db'):
                databases.append(os.path.splitext(file)[0])
                
        return databases
    
    def connect(self, database_name: str) -> bool:
        """Connect to a database"""
        if database_name in self.connections:
            # Already connected
            return True
            
        try:
            database_path = os.path.join(self.data_dir, f"{database_name}.db")
            
            with self.connection_lock:
                connection = sqlite3.connect(database_path, check_same_thread=False)
                # Enable foreign keys
                connection.execute("PRAGMA foreign_keys = ON")
                self.connections[database_name] = {
                    'connection': connection,
                    'lock': threading.Lock()
                }
            
            logger.info(f"Connected to database: {database_name}")
            return True
        except Exception as e:
            logger.error(f"Error connecting to database {database_name}: {e}")
            return False
    
    def disconnect(self, database_name: str) -> bool:
        """Disconnect from a database"""
        with self.connection_lock:
            if database_name not in self.connections:
                return True  # Already disconnected
                
            try:
                self.connections[database_name]['connection'].close()
                del self.connections[database_name]
                logger.info(f"Disconnected from database: {database_name}")
                return True
            except Exception as e:
                logger.error(f"Error disconnecting from database {database_name}: {e}")
                return False
    
    def disconnect_all(self) -> None:
        """Disconnect from all databases"""
        with self.connection_lock:
            for database_name, connection_data in list(self.connections.items()):
                try:
                    connection_data['connection'].close()
                    del self.connections[database_name]
                except Exception as e:
                    logger.error(f"Error disconnecting from database {database_name}: {e}")
    
    def create_table(self, database_name: str, table_name: str, columns: List[str]) -> bool:
        """Create a new table"""
        if not self._ensure_connected(database_name):
            return False
            
        try:
            conn_data = self.connections[database_name]
            with conn_data['lock']:
                conn = conn_data['connection']
                cursor = conn.cursor()
                
                # Build CREATE TABLE statement
                columns_sql = ", ".join(columns)
                sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns_sql})"
                
                cursor.execute(sql)
                conn.commit()
                
                logger.info(f"Created table {table_name} in {database_name}")
                return True
                
        except Exception as e:
            logger.error(f"Error creating table {table_name}: {e}")
            return False
    
    def list_tables(self, database_name: str) -> List[str]:
        """List tables in the database"""
        if not self._ensure_connected(database_name):
            return []
            
        try:
            conn_data = self.connections[database_name]
            with conn_data['lock']:
                conn = conn_data['connection']
                cursor = conn.cursor()
                
                # Query for table names
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                return tables
                
        except Exception as e:
            logger.error(f"Error listing tables in {database_name}: {e}")
            return []
    
    def get_table_schema(self, database_name: str, table_name: str) -> List[Dict[str, str]]:
        """Get the schema of a table"""
        if not self._ensure_connected(database_name):
            return []
            
        try:
            conn_data = self.connections[database_name]
            with conn_data['lock']:
                conn = conn_data['connection']
                cursor = conn.cursor()
                
                # Query for table schema
                cursor.execute(f"PRAGMA table_info({table_name})")
                schema = []
                
                for row in cursor.fetchall():
                    column = {
                        'cid': row[0],
                        'name': row[1],
                        'type': row[2],
                        'notnull': row[3],
                        'default_value': row[4],
                        'pk': row[5]
                    }
                    schema.append(column)
                    
                return schema
                
        except Exception as e:
            logger.error(f"Error getting schema for table {table_name}: {e}")
            return []
    
    def execute_query(self, database_name: str, query: str, parameters: Tuple = ()) -> Tuple[bool, Any]:
        """Execute a query and return results"""
        if not self._ensure_connected(database_name):
            return False, "Not connected to database"
            
        try:
            conn_data = self.connections[database_name]
            with conn_data['lock']:
                conn = conn_data['connection']
                cursor = conn.cursor()
                
                cursor.execute(query, parameters)
                
                # Check if query is SELECT
                if query.strip().upper().startswith("SELECT"):
                    # Fetch results
                    columns = [desc[0] for desc in cursor.description]
                    rows = cursor.fetchall()
                    
                    result = {
                        'columns': columns,
                        'rows': rows
                    }
                    
                    return True, result
                else:
                    # For other queries, commit and return affected rows
                    conn.commit()
                    return True, {'rowcount': cursor.rowcount}
                    
        except Exception as e:
            logger.error(f"Error executing query on {database_name}: {e}")
            return False, str(e)
    
    def execute_script(self, database_name: str, script: str) -> Tuple[bool, str]:
        """Execute a SQL script"""
        if not self._ensure_connected(database_name):
            return False, "Not connected to database"
            
        try:
            conn_data = self.connections[database_name]
            with conn_data['lock']:
                conn = conn_data['connection']
                cursor = conn.cursor()
                
                cursor.executescript(script)
                conn.commit()
                
                return True, f"Script executed successfully"
                
        except Exception as e:
            logger.error(f"Error executing script on {database_name}: {e}")
            return False, str(e)
    
    def import_csv(self, database_name: str, table_name: str, csv_path: str, 
                  has_headers: bool = True, delimiter: str = ',') -> Tuple[bool, str]:
        """Import data from a CSV file"""
        if not self._ensure_connected(database_name):
            return False, "Not connected to database"
            
        try:
            import csv
            
            # Ensure the CSV file exists
            if not os.path.exists(csv_path):
                return False, f"CSV file not found: {csv_path}"
                
            conn_data = self.connections[database_name]
            with conn_data['lock']:
                conn = conn_data['connection']
                cursor = conn.cursor()
                
                # Read the CSV file
                with open(csv_path, 'r', newline='') as csvfile:
                    csv_reader = csv.reader(csvfile, delimiter=delimiter)
                    
                    # Get headers if present
                    if has_headers:
                        headers = next(csv_reader)
                        
                        # Check if table exists
                        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
                        table_exists = cursor.fetchone() is not None
                        
                        if not table_exists:
                            # Create table with headers as column names
                            columns = [f'"{header}" TEXT' for header in headers]
                            create_sql = f'CREATE TABLE "{table_name}" ({", ".join(columns)})'
                            cursor.execute(create_sql)
                        
                        # Insert data
                        placeholders = ', '.join(['?'] * len(headers))
                        insert_sql = f'INSERT INTO "{table_name}" VALUES ({placeholders})'
                        
                        # Process rows
                        rows_to_insert = []
                        for row in csv_reader:
                            # Pad row if needed
                            padded_row = row + [''] * (len(headers) - len(row))
                            rows_to_insert.append(padded_row[:len(headers)])
                            
                            # Execute in batches of 100
                            if len(rows_to_insert) >= 100:
                                cursor.executemany(insert_sql, rows_to_insert)
                                rows_to_insert = []
                        
                        # Insert any remaining rows
                        if rows_to_insert:
                            cursor.executemany(insert_sql, rows_to_insert)
                            
                    else:
                        # No headers, read first row to determine column count
                        first_row = next(csv_reader)
                        column_count = len(first_row)
                        
                        # Check if table exists
                        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
                        table_exists = cursor.fetchone() is not None
                        
                        if not table_exists:
                            # Create table with generic column names
                            columns = [f'"column{i}" TEXT' for i in range(column_count)]
                            create_sql = f'CREATE TABLE "{table_name}" ({", ".join(columns)})'
                            cursor.execute(create_sql)
                        
                        # Insert data
                        placeholders = ', '.join(['?'] * column_count)
                        insert_sql = f'INSERT INTO "{table_name}" VALUES ({placeholders})'
                        
                        # Start with the first row we already read
                        rows_to_insert = [first_row]
                        
                        # Process remaining rows
                        for row in csv_reader:
                            # Pad row if needed
                            padded_row = row + [''] * (column_count - len(row))
                            rows_to_insert.append(padded_row[:column_count])
                            
                            # Execute in batches of 100
                            if len(rows_to_insert) >= 100:
                                cursor.executemany(insert_sql, rows_to_insert)
                                rows_to_insert = []
                        
                        # Insert any remaining rows
                        if rows_to_insert:
                            cursor.executemany(insert_sql, rows_to_insert)
                
                conn.commit()
                
                return True, f"Imported CSV data into {table_name}"
                
        except Exception as e:
            logger.error(f"Error importing CSV into {database_name}.{table_name}: {e}")
            return False, str(e)
    
    def export_csv(self, database_name: str, table_name: str, csv_path: str,
                  include_headers: bool = True, delimiter: str = ',') -> Tuple[bool, str]:
        """Export table data to a CSV file"""
        if not self._ensure_connected(database_name):
            return False, "Not connected to database"
            
        try:
            import csv
            
            conn_data = self.connections[database_name]
            with conn_data['lock']:
                conn = conn_data['connection']
                cursor = conn.cursor()
                
                # Get table data
                cursor.execute(f'SELECT * FROM "{table_name}"')
                rows = cursor.fetchall()
                
                # Get column names
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = [column[1] for column in cursor.fetchall()]
                
                # Write to CSV
                with open(csv_path, 'w', newline='') as csvfile:
                    csv_writer = csv.writer(csvfile, delimiter=delimiter)
                    
                    if include_headers:
                        csv_writer.writerow(columns)
                        
                    csv_writer.writerows(rows)
                
                return True, f"Exported {len(rows)} rows to {csv_path}"
                
        except Exception as e:
            logger.error(f"Error exporting {database_name}.{table_name} to CSV: {e}")
            return False, str(e)
    
    def backup_database(self, database_name: str, backup_path: str = None) -> Tuple[bool, str]:
        """Create a backup of the database"""
        if not self._ensure_connected(database_name):
            return False, "Not connected to database"
            
        try:
            # Generate backup path if not provided
            if not backup_path:
                backup_dir = os.path.join(self.data_dir, "backups")
                os.makedirs(backup_dir, exist_ok=True)
                
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                backup_path = os.path.join(backup_dir, f"{database_name}_{timestamp}.db")
            
            conn_data = self.connections[database_name]
            with conn_data['lock']:
                source_path = os.path.join(self.data_dir, f"{database_name}.db")
                
                # Create backup using SQLite backup API
                source_conn = conn_data['connection']
                dest_conn = sqlite3.connect(backup_path)
                
                source_conn.backup(dest_conn)
                dest_conn.close()
                
                return True, f"Database backed up to {backup_path}"
                
        except Exception as e:
            logger.error(f"Error backing up database {database_name}: {e}")
            return False, str(e)
    
    def _ensure_connected(self, database_name: str) -> bool:
        """Ensure we are connected to the specified database"""
        with self.connection_lock:
            if database_name not in self.connections:
                return self.connect(database_name)
            return True

class QueryBuilder:
    """Helper for building SQL queries"""
    
    @staticmethod
    def create_table(table_name: str, columns: Dict[str, str], 
                    primary_key: str = None, foreign_keys: Dict[str, Tuple[str, str]] = None) -> str:
        """
        Build a CREATE TABLE query
        
        Args:
            table_name: Name of the table to create
            columns: Dict of column_name -> column_type
            primary_key: Name of primary key column
            foreign_keys: Dict of column_name -> (referenced_table, referenced_column)
        """
        column_defs = []
        
        for col_name, col_type in columns.items():
            column_def = f'"{col_name}" {col_type}'
            
            # Add primary key constraint if this is the primary key
            if primary_key and col_name == primary_key:
                column_def += " PRIMARY KEY"
                
            column_defs.append(column_def)
        
        # Add foreign key constraints
        if foreign_keys:
            for col_name, (ref_table, ref_col) in foreign_keys.items():
                fk_constraint = f'FOREIGN KEY ("{col_name}") REFERENCES "{ref_table}"("{ref_col}")'
                column_defs.append(fk_constraint)
        
        query = f'CREATE TABLE IF NOT EXISTS "{table_name}" ({", ".join(column_defs)})'
        return query
    
    @staticmethod
    def insert(table_name: str, columns: List[str]) -> Tuple[str, List[str]]:
        """
        Build an INSERT query
        
        Returns:
            Tuple of (query, parameter_placeholders)
        """
        placeholders = ", ".join(["?" for _ in columns])
        columns_str = ", ".join([f'"{col}"' for col in columns])
        
        query = f'INSERT INTO "{table_name}" ({columns_str}) VALUES ({placeholders})'
        return query, ["?" for _ in columns]
    
    @staticmethod
    def select(table_name: str, columns: List[str] = None, where: Dict[str, Any] = None,
              order_by: str = None, limit: int = None) -> Tuple[str, List[Any]]:
        """
        Build a SELECT query
        
        Args:
            table_name: Name of the table to query
            columns: List of columns to select, None for all (*)
            where: Dict of column_name -> value for WHERE conditions
            order_by: Column name to order by
            limit: Maximum number of rows to return
            
        Returns:
            Tuple of (query, parameters)
        """
        # Build columns part
        columns_str = "*"
        if columns:
            columns_str = ", ".join([f'"{col}"' for col in columns])
        
        # Start building query
        query = f'SELECT {columns_str} FROM "{table_name}"'
        
        # Build WHERE clause and parameter list
        parameters = []
        if where:
            conditions = []
            for col, value in where.items():
                conditions.append(f'"{col}" = ?')
                parameters.append(value)
                
            query += f' WHERE {" AND ".join(conditions)}'
        
        # Add ORDER BY if specified
        if order_by:
            query += f' ORDER BY "{order_by}"'
        
        # Add LIMIT if specified
        if limit is not None:
            query += f' LIMIT {limit}'
        
        return query, parameters
    
    @staticmethod
    def update(table_name: str, columns: Dict[str, Any], where: Dict[str, Any]) -> Tuple[str, List[Any]]:
        """
        Build an UPDATE query
        
        Args:
            table_name: Name of the table to update
            columns: Dict of column_name -> new_value
            where: Dict of column_name -> value for WHERE conditions
            
        Returns:
            Tuple of (query, parameters)
        """
        # Build SET clause and first part of parameter list
        set_clauses = []
        parameters = []
        
        for col, value in columns.items():
            set_clauses.append(f'"{col}" = ?')
            parameters.append(value)
        
        # Start building query
        query = f'UPDATE "{table_name}" SET {", ".join(set_clauses)}'
        
        # Build WHERE clause and add to parameter list
        if where:
            conditions = []
            for col, value in where.items():
                conditions.append(f'"{col}" = ?')
                parameters.append(value)
                
            query += f' WHERE {" AND ".join(conditions)}'
        
        return query, parameters
    
    @staticmethod
    def delete(table_name: str, where: Dict[str, Any]) -> Tuple[str, List[Any]]:
        """
        Build a DELETE query
        
        Args:
            table_name: Name of the table to delete from
            where: Dict of column_name -> value for WHERE conditions
            
        Returns:
            Tuple of (query, parameters)
        """
        # Start building query
        query = f'DELETE FROM "{table_name}"'
        
        # Build WHERE clause and parameter list
        parameters = []
        if where:
            conditions = []
            for col, value in where.items():
                conditions.append(f'"{col}" = ?')
                parameters.append(value)
                
            query += f' WHERE {" AND ".join(conditions)}'
        
        return query, parameters

def main():
    """CLI interface for database management"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Triad Terminal Database Manager")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # List databases command
    subparsers.add_parser("list", help="List available databases")
    
    # Create table command
    create_parser = subparsers.add_parser("create", help="Create a new table")
    create_parser.add_argument("database", help="Database name")
    create_parser.add_argument("table", help="Table name")
    create_parser.add_argument("columns", help="Column definitions (name type, ...)")
    
    # List tables command
    tables_parser = subparsers.add_parser("tables", help="List tables in a database")
    tables_parser.add_argument("database", help="Database name")
    
    # Schema command
    schema_parser = subparsers.add_parser("schema", help="Show table schema")
    schema_parser.add_argument("database", help="Database name")
    schema_parser.add_argument("table", help="Table name")
    
    # Query command
    query_parser = subparsers.add_parser("query", help="Execute a SQL query")
    query_parser.add_argument("database", help="Database name")
    query_parser.add_argument("sql", help="SQL query to execute")
    
    # Import command
    import_parser = subparsers.add_parser("import", help="Import data from CSV")
    import_parser.add_argument("database", help="Database name")
    import_parser.add_argument("table", help="Table name")
    import_parser.add_argument("file", help="CSV file path")
    import_parser.add_argument("--no-headers", action="store_true", help="CSV has no headers")
    
    # Export command
    export_parser = subparsers.add_parser("export", help="Export data to CSV")
    export_parser.add_argument("database", help="Database name")
    export_parser.add_argument("table", help="Table name")
    export_parser.add_argument("file", help="Output CSV file path")
    
    # Backup command
    backup_parser = subparsers.add_parser("backup", help="Backup a database")
    backup_parser.add_argument("database", help="Database name")
    backup_parser.add_argument("--output", "-o", help="Output file path")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Initialize database manager
    db_manager = DatabaseManager()
    
    # Execute the appropriate command
    try:
        if args.command == "list":
            # List databases
            databases = db_manager.list_databases()
            if databases:
                print("Available databases:")
                for db in databases:
                    print(f"  - {db}")
            else:
                print("No databases found")
                
        elif args.command == "create":
            # Create table
            columns = [col.strip() for col in args.columns.split(",")]
            success = db_manager.create_table(args.database, args.table, columns)
            
            if success:
                print(f"Table '{args.table}' created successfully")
            else:
                print("Failed to create table")
                
        elif args.command == "tables":
            # List tables
            tables = db_manager.list_tables(args.database)
            
            if tables:
                print(f"Tables in {args.database}:")
                for table in tables:
                    print(f"  - {table}")
            else:
                print(f"No tables found in {args.database}")
                
        elif args.command == "schema":
            # Show table schema
            schema = db_manager.get_table_schema(args.database, args.table)
            
            if schema:
                print(f"Schema for {args.table}:")
                for column in schema:
                    pk_marker = "PK" if column['pk'] else "  "
                    null_marker = "NOT NULL" if column['notnull'] else "NULL    "
                    print(f"  {pk_marker} {column['name']:<20} {column['type']:<10} {null_marker}")
            else:
                print(f"Could not retrieve schema for {args.table}")
                
        elif args.command == "query":
            # Execute query
            success, result = db_manager.execute_query(args.database, args.sql)
            
            if success:
                if isinstance(result, dict) and 'columns' in result:
                    # Display query results
                    columns = result['columns']
                    rows = result['rows']
                    
                    # Print header
                    header = " | ".join(str(col) for col in columns)
                    print(header)
                    print("-" * len(header))
                    
                    # Print rows
                    for row in rows:
                        print(" | ".join(str(val) for val in row))
                        
                    print(f"\n{len(rows)} rows returned")
                else:
                    # Non-select query
                    print(f"Query executed successfully. Rows affected: {result.get('rowcount', 0)}")
            else:
                print(f"Query failed: {result}")
                
        elif args.command == "import":
            # Import CSV
            has_headers = not args.no_headers
            success, message = db_manager.import_csv(
                args.database, args.table, args.file, has_headers
            )
            
            if success:
                print(message)
            else:
                print(f"Import failed: {message}")
                
        elif args.command == "export":
            # Export to CSV
            success, message = db_manager.export_csv(
                args.database, args.table, args.file
            )
            
            if success:
                print(message)
            else:
                print(f"Export failed: {message}")
                
        elif args.command == "backup":
            # Backup database
            success, message = db_manager.backup_database(
                args.database, args.output
            )
            
            if success:
                print(message)
            else:
                print(f"Backup failed: {message}")
                
        else:
            print("Please specify a command. Use --help for usage information.")
            
    except Exception as e:
        print(f"Error: {e}")
        
    finally:
        # Clean up connections
        db_manager.disconnect_all()

if __name__ == "__main__":
    main()