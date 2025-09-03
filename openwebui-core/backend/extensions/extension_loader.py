"""Extension loader for OpenWebUI plugins.

This module provides functionality to automatically discover and load
plugins using Python entry points.
"""

import logging
from importlib.metadata import entry_points
from typing import Callable, List

from fastapi import FastAPI

from .interfaces import Plugin, PluginLoadError, PluginRegistrationError

logger = logging.getLogger(__name__)


def load_plugins(app: FastAPI, groups: List[str] = None) -> None:
    """Load and register plugins with the FastAPI application.
    
    This function discovers plugins using Python entry points and registers
    them with the FastAPI application. Plugins are loaded from the specified
    entry point groups.
    
    Args:
        app: The FastAPI application instance to register plugins with.
        groups: List of entry point groups to load plugins from.
               Defaults to ["openwebui.plugins"].
    """
    if groups is None:
        groups = ["openwebui.plugins"]
    
    loaded_plugins = []
    failed_plugins = []
    
    logger.info(f"Loading plugins from groups: {groups}")
    
    for group in groups:
        logger.debug(f"Discovering plugins in group: {group}")
        
        try:
            eps = entry_points().select(group=group)
        except Exception as e:
            logger.error(f"Failed to discover entry points for group {group}: {e}")
            continue
        
        for ep in eps:
            plugin_name = ep.name
            logger.debug(f"Loading plugin: {plugin_name}")
            
            try:
                # Load the plugin entry point
                register_func: Callable[[FastAPI], None] = ep.load()
                
                # Validate that the loaded object is callable
                if not callable(register_func):
                    raise PluginLoadError(
                        f"Plugin {plugin_name} entry point is not callable"
                    )
                
                # Register the plugin with the application
                register_func(app)
                
                loaded_plugins.append(plugin_name)
                logger.info(f"Successfully loaded plugin: {plugin_name}")
                
            except PluginLoadError:
                # Re-raise plugin-specific errors
                raise
            except ImportError as e:
                error_msg = f"Failed to import plugin {plugin_name}: {e}"
                logger.error(error_msg)
                failed_plugins.append((plugin_name, error_msg))
            except Exception as e:
                error_msg = f"Failed to load plugin {plugin_name}: {e}"
                logger.error(error_msg)
                failed_plugins.append((plugin_name, error_msg))
    
    # Log summary
    logger.info(f"Plugin loading complete: {len(loaded_plugins)} loaded, {len(failed_plugins)} failed")
    
    if loaded_plugins:
        logger.info(f"Loaded plugins: {', '.join(loaded_plugins)}")
    
    if failed_plugins:
        logger.warning(f"Failed plugins: {', '.join([name for name, _ in failed_plugins])}")
        
        # Store failed plugin information for admin interface
        if not hasattr(app.state, "plugin_info"):
            app.state.plugin_info = {}
        
        app.state.plugin_info.update({
            "loaded": loaded_plugins,
            "failed": failed_plugins,
            "groups": groups
        })


def get_plugin_info(app: FastAPI) -> dict:
    """Get information about loaded and failed plugins.
    
    Args:
        app: The FastAPI application instance.
        
    Returns:
        Dictionary containing plugin loading information.
    """
    default_info = {
        "loaded": [],
        "failed": [],
        "groups": ["openwebui.plugins"]
    }
    
    return getattr(app.state, "plugin_info", default_info)


def reload_plugins(app: FastAPI, groups: List[str] = None) -> dict:
    """Reload plugins for the application.
    
    Note: This is a basic implementation that logs the reload request.
    Full hot-reloading of plugins would require more complex state management.
    
    Args:
        app: The FastAPI application instance.
        groups: List of entry point groups to reload plugins from.
        
    Returns:
        Dictionary with reload status information.
    """
    logger.warning("Plugin hot-reloading is not fully implemented")
    logger.info("To reload plugins, restart the application")
    
    current_info = get_plugin_info(app)
    
    return {
        "status": "reload_requested",
        "message": "Plugin hot-reloading requires application restart",
        "current_plugins": current_info["loaded"],
        "recommendation": "Restart the application to reload plugins"
    }
