"""OpenWebUI Extensions Package

This package provides the extension system for OpenWebUI, including
plugin loading and management functionality.
"""

__version__ = "1.0.0"

from .extension_loader import load_plugins
from .interfaces import Plugin

__all__ = ["load_plugins", "Plugin"]
