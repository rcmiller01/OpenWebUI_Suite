"""OpenWebUI Ollama Tools Plugin

This plugin provides Ollama integration tools for OpenWebUI including
model management, health monitoring, routing, and memory storage.
"""

__version__ = "0.1.0"
__author__ = "OpenWebUI Suite"

from .plugin import register

__all__ = ["register"]
