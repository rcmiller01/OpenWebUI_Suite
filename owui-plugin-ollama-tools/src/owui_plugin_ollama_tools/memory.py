"""Memory storage module for simple key-value persistence."""

import os
import sqlite3
from pathlib import Path
from typing import Optional


class Memory:
    """Simple SQLite-based key-value memory store for plugin data."""
    
    def __init__(self, path: str) -> None:
        """Initialize the memory store with a SQLite database.
        
        Args:
            path: Path to the SQLite database file.
        """
        self.path = Path(path)
        
        # Ensure the directory exists
        self.path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize the database
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize the SQLite database with the key-value table."""
        with sqlite3.connect(self.path) as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS kv (
                    k TEXT PRIMARY KEY,
                    v TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create trigger to update timestamp
            db.execute("""
                CREATE TRIGGER IF NOT EXISTS update_timestamp 
                AFTER UPDATE ON kv
                BEGIN
                    UPDATE kv SET updated_at = CURRENT_TIMESTAMP WHERE k = NEW.k;
                END
            """)
    
    def set(self, key: str, value: str) -> None:
        """Set a key-value pair in the memory store.
        
        Args:
            key: The key to store the value under.
            value: The value to store.
        """
        with sqlite3.connect(self.path) as db:
            db.execute("""
                INSERT INTO kv(k, v) VALUES(?, ?) 
                ON CONFLICT(k) DO UPDATE SET 
                    v = excluded.v,
                    updated_at = CURRENT_TIMESTAMP
            """, (key, value))
    
    def get(self, key: str) -> Optional[str]:
        """Get a value from the memory store by key.
        
        Args:
            key: The key to retrieve the value for.
            
        Returns:
            The stored value or None if the key doesn't exist.
        """
        with sqlite3.connect(self.path) as db:
            row = db.execute("SELECT v FROM kv WHERE k = ?", (key,)).fetchone()
            return row[0] if row else None
    
    def delete(self, key: str) -> bool:
        """Delete a key-value pair from the memory store.
        
        Args:
            key: The key to delete.
            
        Returns:
            True if the key was deleted, False if it didn't exist.
        """
        with sqlite3.connect(self.path) as db:
            cursor = db.execute("DELETE FROM kv WHERE k = ?", (key,))
            return cursor.rowcount > 0
    
    def list_keys(self, prefix: str = "") -> list[str]:
        """List all keys in the memory store, optionally filtered by prefix.
        
        Args:
            prefix: Optional prefix to filter keys by.
            
        Returns:
            List of keys matching the prefix.
        """
        with sqlite3.connect(self.path) as db:
            if prefix:
                rows = db.execute(
                    "SELECT k FROM kv WHERE k LIKE ? ORDER BY k", 
                    (f"{prefix}%",)
                ).fetchall()
            else:
                rows = db.execute("SELECT k FROM kv ORDER BY k").fetchall()
            
            return [row[0] for row in rows]
    
    def clear(self) -> int:
        """Clear all key-value pairs from the memory store.
        
        Returns:
            Number of records deleted.
        """
        with sqlite3.connect(self.path) as db:
            cursor = db.execute("DELETE FROM kv")
            return cursor.rowcount
    
    def stats(self) -> dict:
        """Get statistics about the memory store.
        
        Returns:
            Dictionary with store statistics.
        """
        with sqlite3.connect(self.path) as db:
            count = db.execute("SELECT COUNT(*) FROM kv").fetchone()[0]
            size = os.path.getsize(self.path) if self.path.exists() else 0
            
            return {
                "total_keys": count,
                "database_size_bytes": size,
                "database_path": str(self.path)
            }
