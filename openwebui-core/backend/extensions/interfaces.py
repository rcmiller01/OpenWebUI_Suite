"""Plugin interfaces and protocols for OpenWebUI extensions."""

from typing import Protocol, runtime_checkable

from fastapi import FastAPI


@runtime_checkable
class Plugin(Protocol):
    """Protocol that all OpenWebUI plugins must implement.
    
    This protocol defines the interface that plugins must follow to be
    automatically loaded by the OpenWebUI extension system.
    """
    
    def register(self, app: FastAPI) -> None:
        """Register the plugin with the FastAPI application.
        
        This method is called during application startup to register
        the plugin's routes, middleware, and other components.
        
        Args:
            app: The FastAPI application instance to register with.
        """
        ...
    
    def on_startup(self) -> None:
        """Optional startup hook called after plugin registration.
        
        This method is called after all plugins have been registered
        and can be used for initialization tasks that require other
        plugins to be available.
        """
        ...
    
    def on_shutdown(self) -> None:
        """Optional shutdown hook called during application shutdown.
        
        This method is called when the application is shutting down
        and can be used for cleanup tasks.
        """
        ...


class PluginError(Exception):
    """Base exception for plugin-related errors."""
    pass


class PluginLoadError(PluginError):
    """Raised when a plugin fails to load properly."""
    pass


class PluginRegistrationError(PluginError):
    """Raised when a plugin fails to register with the application."""
    pass
