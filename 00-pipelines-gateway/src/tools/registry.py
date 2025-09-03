"""
Tool registry and management

Handles registration, discovery, and execution of tools
that can be used by models during processing.
"""

import json
import logging
import os
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class Tool:
    """Base tool class"""
    
    def __init__(self, name: str, description: str, parameters: Dict[str, Any]):
        self.name = name
        self.description = description
        self.parameters = parameters
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool with given parameters"""
        raise NotImplementedError("Tool must implement execute method")


class CalculatorTool(Tool):
    """Simple calculator tool"""
    
    def __init__(self):
        super().__init__(
            name="calculator",
            description="Perform basic mathematical calculations",
            parameters={
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Mathematical expression to evaluate"
                    }
                },
                "required": ["expression"]
            }
        )
    
    async def execute(self, expression: str) -> Dict[str, Any]:
        """Execute calculation"""
        try:
            # Basic safety check
            if any(word in expression for word in ["import", "exec", "__"]):
                raise ValueError("Invalid expression")
            
            # Evaluate simple math expressions
            result = eval(expression)  # Note: unsafe for production
            return {
                "success": True,
                "result": result,
                "expression": expression
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "expression": expression
            }


class WebSearchTool(Tool):
    """Web search tool (mock implementation)"""
    
    def __init__(self):
        super().__init__(
            name="web_search",
            description="Search the web for information",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        )
    
    async def execute(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """Execute web search"""
        # Mock search results
        return {
            "success": True,
            "query": query,
            "results": [
                {
                    "title": f"Mock result 1 for '{query}'",
                    "url": "https://example.com/1",
                    "snippet": "This is a mock search result..."
                },
                {
                    "title": f"Mock result 2 for '{query}'",
                    "url": "https://example.com/2",
                    "snippet": "Another mock search result..."
                }
            ][:max_results]
        }


class ToolRegistry:
    """Registry for managing available tools"""
    
    def __init__(self):
        self.tools: Dict[str, Tool] = {}
        self.config_path = "config/tools.json"
    
    async def load_config(self):
        """Load tool configuration and register built-in tools"""
        # Register built-in tools
        await self.register_tool(CalculatorTool())
        await self.register_tool(WebSearchTool())
        
        # Load additional tools from config
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    # Process external tool configurations
                    await self._load_external_tools(config)
            else:
                # Create default config
                await self._save_config()
                
            logger.info(f"Loaded {len(self.tools)} tools")
            
        except Exception as e:
            logger.error(f"Failed to load tool config: {e}")
            raise
    
    async def register_tool(self, tool: Tool):
        """Register a tool in the registry"""
        self.tools[tool.name] = tool
        logger.debug(f"Registered tool: {tool.name}")
    
    async def _load_external_tools(self, config: Dict[str, Any]):
        """Load external tools from configuration"""
        external_tools = config.get("external_tools", [])
        
        for tool_config in external_tools:
            name = tool_config.get("name")
            if name:
                # Create placeholder for external tools
                # In production, this would dynamically load tool modules
                logger.info(f"External tool '{name}' configured but not loaded")
    
    async def _save_config(self):
        """Save current tool configuration"""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            config = {
                "built_in_tools": [tool.name for tool in self.tools.values()],
                "external_tools": []
            }
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save tool config: {e}")
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools in OpenAI function format"""
        tools = []
        
        for tool in self.tools.values():
            tools.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters
                }
            })
        
        return tools
    
    async def get_tool(self, name: str) -> Optional[Tool]:
        """Get a specific tool by name"""
        return self.tools.get(name)
    
    async def execute_tool(self, name: str, **kwargs) -> Dict[str, Any]:
        """Execute a tool with given parameters"""
        tool = self.tools.get(name)
        if not tool:
            return {
                "success": False,
                "error": f"Tool '{name}' not found"
            }
        
        try:
            result = await tool.execute(**kwargs)
            return result
        except Exception as e:
            logger.error(f"Error executing tool '{name}': {e}")
            return {
                "success": False,
                "error": str(e),
                "tool": name
            }
    
    async def search_tools(self, capability: str) -> List[str]:
        """Search for tools by capability"""
        # Simple capability matching
        matching_tools = []
        
        capability_lower = capability.lower()
        for tool_name, tool in self.tools.items():
            if capability_lower in tool.description.lower():
                matching_tools.append(tool_name)
        
        return matching_tools
