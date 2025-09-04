"""
Memory 2.0 Package

Persistent memory system for OpenWebUI Suite with dual storage:
- Traits: Key-value store for user characteristics (SQL)
- Episodes: Semantic memory for conversations (Vector DB)
"""

__version__ = "2.0.0"
__author__ = "OpenWebUI Suite"
__description__ = "Persistent memory system with traits and episodic storage"

from .app import app

__all__ = ["app"]
