"""
MITO Engine - Database Manager
Complete database management system with multiple database support
"""

import os
import sqlite3
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import logging

class DatabaseConnection:
    """Database connection wrapper"""
    
    def __init__(self, db_type: str, connection_string: str):
        self.db_type = db_type
        self.connection_string = connection_string
        self.connection = None
        self.cursor = None
        self.connected = False
        
    def connect(self) -> bool:
        """Establish database connection"""
        try:
            if self.db_type == "sqlite":
                self.connection = sqlite3.connect(self.connection_string)
                self.connection.row_factory = sqlite3.Row
                self.cursor = self.connection.cursor()
                self.connected = True
                return True
            else:
                # Placeholder for other database types
                raise NotImplementedError(f"Database type {self.db_type} not implemented")
        except Exception as e:
            logging.error(f"Database connection failed: {e}")
            return False
    
    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            self.connected = False
    
    def execute(self, query: str, params: tuple = None) -> Dict[str, Any]:
        """Execute database query"""
        try:
            if not self.connected:
                if not self.connect():
                    return {"success": False, "error": "Failed to connect to database"}
            
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            
            # For SELECT queries, fetch results
            if query.strip().upper().startswith('SELECT'):
                rows = self.cursor.fetchall()
                results = [dict(row) for row in rows]
                return {
                    "success": True,
                    "data": results,
                    "row_count": len(results)
                }
            else:
                # For INSERT, UPDATE, DELETE
                self.connection.commit()
                return {
                    "success": True,
                    "affected_rows": self.cursor.rowcount,
                    "last_insert_id": self.cursor.lastrowid
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}

class Table:
    """Database table representation"""
    
    def __init__(self, name: str, columns: List[Dict[str, Any]]):
        self.name = name
        self.columns = columns
        self.created_at = datetime.now().isoformat()
    
    def get_create_sql(self, db_type: str = "sqlite") -> str:
        """Generate CREATE TABLE SQL"""
        if db_type == "sqlite":
            column_defs = []
            for col in self.columns:
                col_def = f"{col['name']} {col['type']}"
                if col.get('primary_key'):
                    col_def += " PRIMARY KEY"
                if col.get('auto_increment'):
                    col_def += " AUTOINCREMENT"
                if col.get('not_null'):
                    col_def += " NOT NULL"
                if col.get('unique'):
                    col_def += " UNIQUE"
                if col.get('default'):
                    col_def += f" DEFAULT {col['default']}"
                column_defs.append(col_def)
            
            newline = '\n'
            return f"CREATE TABLE IF NOT EXISTS {self.name} ({newline}  {f',{newline}  '.join(column_defs)}{newline})"
        
        return ""

class DatabaseManager:
    """Complete database management system"""
    
    def __init__(self):
        self.connections = {}
        self.schemas = {}
        self.default_db = "mito_main.db"
        
        # Initialize default database
        self.create_connection("default", "sqlite", self.default_db)
        self.initialize_system_tables()
    
    def create_connection(self, name: str, db_type: str, connection_string: str) -> Dict[str, Any]:
        """Create new database connection"""
        try:
            connection = DatabaseConnection(db_type, connection_string)
            if connection.connect():
                self.connections[name] = connection
                return {
                    "success": True,
                    "message": f"Connection '{name}' created successfully",
                    "db_type": db_type
                }
            else:
                return {"success": False, "error": "Failed to establish connection"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_connection(self, name: str = "default") -> Optional[DatabaseConnection]:
        """Get database connection by name"""
        return self.connections.get(name)
    
    def list_connections(self) -> List[Dict[str, Any]]:
        """List all database connections"""
        connections = []
        for name, conn in self.connections.items():
            connections.append({
                "name": name,
                "type": conn.db_type,
                "connected": conn.connected,
                "connection_string": conn.connection_string
            })
        return connections
    
    def execute_query(self, query: str, params: tuple = None, connection_name: str = "default") -> Dict[str, Any]:
        """Execute query on specified connection"""
        conn = self.get_connection(connection_name)
        if not conn:
            return {"success": False, "error": f"Connection '{connection_name}' not found"}
        
        return conn.execute(query, params)
    
    def create_table(self, table: Table, connection_name: str = "default") -> Dict[str, Any]:
        """Create table in database"""
        conn = self.get_connection(connection_name)
        if not conn:
            return {"success": False, "error": f"Connection '{connection_name}' not found"}
        
        create_sql = table.get_create_sql(conn.db_type)
        result = conn.execute(create_sql)
        
        if result["success"]:
            # Store table schema
            if connection_name not in self.schemas:
                self.schemas[connection_name] = {}
            self.schemas[connection_name][table.name] = table
            
            result["message"] = f"Table '{table.name}' created successfully"
        
        return result
    
    def drop_table(self, table_name: str, connection_name: str = "default") -> Dict[str, Any]:
        """Drop table from database"""
        conn = self.get_connection(connection_name)
        if not conn:
            return {"success": False, "error": f"Connection '{connection_name}' not found"}
        
        result = conn.execute(f"DROP TABLE IF EXISTS {table_name}")
        
        if result["success"]:
            # Remove from schema
            if connection_name in self.schemas and table_name in self.schemas[connection_name]:
                del self.schemas[connection_name][table_name]
            
            result["message"] = f"Table '{table_name}' dropped successfully"
        
        return result
    
    def list_tables(self, connection_name: str = "default") -> Dict[str, Any]:
        """List all tables in database"""
        conn = self.get_connection(connection_name)
        if not conn:
            return {"success": False, "error": f"Connection '{connection_name}' not found"}
        
        if conn.db_type == "sqlite":
            query = "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        else:
            return {"success": False, "error": f"Unsupported database type: {conn.db_type}"}
        
        return conn.execute(query)
    
    def describe_table(self, table_name: str, connection_name: str = "default") -> Dict[str, Any]:
        """Get table structure"""
        conn = self.get_connection(connection_name)
        if not conn:
            return {"success": False, "error": f"Connection '{connection_name}' not found"}
        
        if conn.db_type == "sqlite":
            query = f"PRAGMA table_info({table_name})"
        else:
            return {"success": False, "error": f"Unsupported database type: {conn.db_type}"}
        
        result = conn.execute(query)
        if result["success"]:
            columns = []
            for row in result["data"]:
                columns.append({
                    "name": row["name"],
                    "type": row["type"],
                    "not_null": bool(row["notnull"]),
                    "primary_key": bool(row["pk"]),
                    "default_value": row["dflt_value"]
                })
            result["columns"] = columns
        
        return result
    
    def insert_data(self, table_name: str, data: Dict[str, Any], connection_name: str = "default") -> Dict[str, Any]:
        """Insert data into table"""
        conn = self.get_connection(connection_name)
        if not conn:
            return {"success": False, "error": f"Connection '{connection_name}' not found"}
        
        columns = list(data.keys())
        placeholders = ", ".join(["?" for _ in columns])
        values = tuple(data.values())
        
        query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
        
        return conn.execute(query, values)
    
    def update_data(self, table_name: str, data: Dict[str, Any], where_clause: str, 
                   where_params: tuple = None, connection_name: str = "default") -> Dict[str, Any]:
        """Update data in table"""
        conn = self.get_connection(connection_name)
        if not conn:
            return {"success": False, "error": f"Connection '{connection_name}' not found"}
        
        set_clause = ", ".join([f"{col} = ?" for col in data.keys()])
        values = tuple(data.values())
        
        if where_params:
            all_params = values + where_params
        else:
            all_params = values
        
        query = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}"
        
        return conn.execute(query, all_params)
    
    def delete_data(self, table_name: str, where_clause: str, where_params: tuple = None, 
                   connection_name: str = "default") -> Dict[str, Any]:
        """Delete data from table"""
        conn = self.get_connection(connection_name)
        if not conn:
            return {"success": False, "error": f"Connection '{connection_name}' not found"}
        
        query = f"DELETE FROM {table_name} WHERE {where_clause}"
        
        return conn.execute(query, where_params)
    
    def select_data(self, table_name: str, columns: str = "*", where_clause: str = None, 
                   where_params: tuple = None, limit: int = None, offset: int = None,
                   order_by: str = None, connection_name: str = "default") -> Dict[str, Any]:
        """Select data from table"""
        conn = self.get_connection(connection_name)
        if not conn:
            return {"success": False, "error": f"Connection '{connection_name}' not found"}
        
        query = f"SELECT {columns} FROM {table_name}"
        
        if where_clause:
            query += f" WHERE {where_clause}"
        
        if order_by:
            query += f" ORDER BY {order_by}"
        
        if limit:
            query += f" LIMIT {limit}"
            if offset:
                query += f" OFFSET {offset}"
        
        return conn.execute(query, where_params)
    
    def backup_database(self, connection_name: str = "default", backup_path: str = None) -> Dict[str, Any]:
        """Backup database to file"""
        try:
            conn = self.get_connection(connection_name)
            if not conn:
                return {"success": False, "error": f"Connection '{connection_name}' not found"}
            
            if not backup_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = f"backup_{connection_name}_{timestamp}.db"
            
            if conn.db_type == "sqlite":
                # For SQLite, copy the database file
                import shutil
                shutil.copy2(conn.connection_string, backup_path)
                
                return {
                    "success": True,
                    "message": f"Database backed up to {backup_path}",
                    "backup_path": backup_path
                }
            else:
                return {"success": False, "error": f"Backup not supported for {conn.db_type}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def restore_database(self, backup_path: str, connection_name: str = "default") -> Dict[str, Any]:
        """Restore database from backup"""
        try:
            if not Path(backup_path).exists():
                return {"success": False, "error": "Backup file not found"}
            
            conn = self.get_connection(connection_name)
            if not conn:
                return {"success": False, "error": f"Connection '{connection_name}' not found"}
            
            if conn.db_type == "sqlite":
                # Close current connection
                conn.close()
                
                # Replace database file
                import shutil
                shutil.copy2(backup_path, conn.connection_string)
                
                # Reconnect
                conn.connect()
                
                return {
                    "success": True,
                    "message": f"Database restored from {backup_path}"
                }
            else:
                return {"success": False, "error": f"Restore not supported for {conn.db_type}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_database_stats(self, connection_name: str = "default") -> Dict[str, Any]:
        """Get database statistics"""
        try:
            conn = self.get_connection(connection_name)
            if not conn:
                return {"success": False, "error": f"Connection '{connection_name}' not found"}
            
            stats = {
                "connection_name": connection_name,
                "database_type": conn.db_type,
                "connected": conn.connected
            }
            
            if conn.db_type == "sqlite":
                # Get database file size
                db_path = Path(conn.connection_string)
                if db_path.exists():
                    stats["file_size"] = db_path.stat().st_size
                    stats["file_path"] = str(db_path)
                
                # Get table count
                tables_result = self.list_tables(connection_name)
                if tables_result["success"]:
                    stats["table_count"] = len(tables_result["data"])
                    
                    # Get row counts for each table
                    table_stats = {}
                    for table in tables_result["data"]:
                        table_name = table["name"]
                        count_result = conn.execute(f"SELECT COUNT(*) as count FROM {table_name}")
                        if count_result["success"]:
                            table_stats[table_name] = count_result["data"][0]["count"]
                    
                    stats["table_statistics"] = table_stats
            
            return {"success": True, "statistics": stats}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def initialize_system_tables(self):
        """Initialize system tables for MITO Engine"""
        
        # System configuration table
        config_table = Table("mito_config", [
            {"name": "key", "type": "TEXT", "primary_key": True},
            {"name": "value", "type": "TEXT"},
            {"name": "created_at", "type": "DATETIME", "default": "CURRENT_TIMESTAMP"},
            {"name": "updated_at", "type": "DATETIME", "default": "CURRENT_TIMESTAMP"}
        ])
        
        # System logs table
        logs_table = Table("mito_logs", [
            {"name": "id", "type": "INTEGER", "primary_key": True, "auto_increment": True},
            {"name": "level", "type": "TEXT", "not_null": True},
            {"name": "message", "type": "TEXT", "not_null": True},
            {"name": "module", "type": "TEXT"},
            {"name": "timestamp", "type": "DATETIME", "default": "CURRENT_TIMESTAMP"}
        ])
        
        # User sessions table
        sessions_table = Table("mito_sessions", [
            {"name": "session_id", "type": "TEXT", "primary_key": True},
            {"name": "user_id", "type": "TEXT"},
            {"name": "data", "type": "TEXT"},
            {"name": "created_at", "type": "DATETIME", "default": "CURRENT_TIMESTAMP"},
            {"name": "last_access", "type": "DATETIME", "default": "CURRENT_TIMESTAMP"}
        ])
        
        # Create tables
        self.create_table(config_table)
        self.create_table(logs_table)
        self.create_table(sessions_table)
        
        # Insert default configuration
        default_config = [
            ("system_initialized", "true"),
            ("version", "1.2.0"),
            ("last_startup", datetime.now().isoformat())
        ]
        
        for key, value in default_config:
            try:
                self.insert_data("mito_config", {"key": key, "value": value})
            except:
                # Config already exists
                pass

# Global database manager instance
database_manager = DatabaseManager()

def main():
    """Demo of database manager functionality"""
    
    # List connections
    connections = database_manager.list_connections()
    print("Database connections:", json.dumps(connections, indent=2))
    
    # Create a test table
    test_table = Table("test_users", [
        {"name": "id", "type": "INTEGER", "primary_key": True, "auto_increment": True},
        {"name": "username", "type": "TEXT", "not_null": True, "unique": True},
        {"name": "email", "type": "TEXT", "not_null": True},
        {"name": "created_at", "type": "DATETIME", "default": "CURRENT_TIMESTAMP"}
    ])
    
    result = database_manager.create_table(test_table)
    print("Create table result:", json.dumps(result, indent=2))
    
    # Insert test data
    if result["success"]:
        insert_result = database_manager.insert_data("test_users", {
            "username": "testuser",
            "email": "test@example.com"
        })
        print("Insert result:", json.dumps(insert_result, indent=2))
        
        # Select data
        select_result = database_manager.select_data("test_users")
        print("Select result:", json.dumps(select_result, indent=2))
    
    # Get database stats
    stats = database_manager.get_database_stats()
    print("Database stats:", json.dumps(stats, indent=2))

if __name__ == "__main__":
    main()