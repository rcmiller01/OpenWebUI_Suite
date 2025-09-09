# 00-pipelines-gateway/src/tools/dispatch.py
"""
Tools dispatch system for OpenRouter refactor
Handles n8n workflow routing and MCP tool integration
"""
import json
import httpx
import logging
import os
from typing import Dict, Any, List, Optional
import asyncio

logger = logging.getLogger(__name__)

# Tool endpoints from configuration
N8N_BASE_URL = os.getenv("N8N_BASE_URL", "http://192.168.50.145:5678")
N8N_API_KEY = os.getenv("N8N_API_KEY", "")
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", 
                           "http://192.168.50.145:5678/webhook/openrouter-router")
N8N_MCP_ENDPOINT = os.getenv("N8N_MCP_ENDPOINT", 
                            "http://192.168.50.145:5678/webhook/mcp-tools")
TIMEOUT_SECONDS = int(os.getenv("TOOLS_TIMEOUT", "30"))


class ToolDispatcher:
    """Handles tool execution via n8n and MCP integrations"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=TIMEOUT_SECONDS)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def execute_n8n_workflow(self, 
                                  workflow_name: str, 
                                  parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute n8n workflow via webhook
        
        Args:
            workflow_name: Name of the workflow to execute
            parameters: Parameters to pass to the workflow
            
        Returns:
            Workflow execution result
        """
        payload = {
            "workflow": workflow_name,
            "parameters": parameters,
            "source": "openrouter-gateway"
        }
        
        try:
            response = await self.client.post(
                N8N_WEBHOOK_URL,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"n8n workflow '{workflow_name}' executed successfully")
            return {
                "success": True,
                "result": result,
                "workflow": workflow_name
            }
            
        except Exception as e:
            logger.error(f"n8n workflow '{workflow_name}' failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "workflow": workflow_name
            }
    
    async def execute_mcp_tool(self, 
                              tool_name: str, 
                              arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute MCP tool via HTTP endpoint
        
        Args:
            tool_name: Name of the MCP tool to call
            arguments: Arguments to pass to the tool
            
        Returns:
            Tool execution result
        """
        payload = {
            "method": "call_tool",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        try:
            response = await self.client.post(
                f"{N8N_MCP_ENDPOINT}/call",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"MCP tool '{tool_name}' executed successfully")
            return {
                "success": True,
                "result": result.get("result"),
                "tool": tool_name
            }
            
        except Exception as e:
            logger.error(f"MCP tool '{tool_name}' failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "tool": tool_name
            }
    
    async def dispatch_tool_call(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """
        Dispatch a tool call to appropriate handler
        
        Args:
            tool_call: Tool call specification from model
            
        Returns:
            Tool execution result
        """
        tool_name = tool_call.get("function", {}).get("name")
        if not tool_name:
            return {
                "success": False,
                "error": "Missing tool name",
                "tool_call": tool_call
            }
        
        arguments_str = tool_call.get("function", {}).get("arguments", "{}")
        try:
            arguments = json.loads(arguments_str) if isinstance(arguments_str, str) else arguments_str
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"Invalid arguments JSON: {e}",
                "tool_call": tool_call
            }
        
        # Route based on tool name prefix
        if tool_name.startswith("n8n_"):
            workflow_name = tool_name.replace("n8n_", "")
            return await self.execute_n8n_workflow(workflow_name, arguments)
        
        elif tool_name.startswith("mcp_"):
            mcp_tool_name = tool_name.replace("mcp_", "")
            return await self.execute_mcp_tool(mcp_tool_name, arguments)
        
        else:
            # Unknown tool type
            return {
                "success": False,
                "error": f"Unknown tool type for '{tool_name}'",
                "tool_call": tool_call
            }
    
    async def get_available_tools(self) -> List[Dict[str, Any]]:
        """
        Get list of available tools from both n8n and MCP
        
        Returns:
            List of tool definitions
        """
        tools = []
        
        # Add n8n router tool
        tools.append({
            "type": "function",
            "function": {
                "name": "n8n_router",
                "description": "Route request to n8n workflow for processing",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "workflow": {
                            "type": "string",
                            "description": "Name of the n8n workflow to execute"
                        },
                        "input_data": {
                            "type": "object",
                            "description": "Data to pass to the workflow"
                        }
                    },
                    "required": ["workflow", "input_data"]
                }
            }
        })
        
        # Add MCP tool
        tools.append({
            "type": "function", 
            "function": {
                "name": "mcp_call",
                "description": "Call Model Context Protocol tool",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "tool_name": {
                            "type": "string",
                            "description": "Name of the MCP tool to call"
                        },
                        "arguments": {
                            "type": "object",
                            "description": "Arguments to pass to the MCP tool"
                        }
                    },
                    "required": ["tool_name", "arguments"]
                }
            }
        })
        
        return tools
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check health of tool endpoints
        
        Returns:
            Health status of n8n and MCP endpoints
        """
        health_status = {
            "n8n": {"available": False, "error": None},
            "mcp": {"available": False, "error": None}
        }
        
        # Check n8n webhook
        try:
            response = await self.client.get(
                N8N_WEBHOOK_URL.replace("/webhook/openrouter-router", "/healthz"),
                timeout=5
            )
            health_status["n8n"]["available"] = response.status_code == 200
        except Exception as e:
            health_status["n8n"]["error"] = str(e)
        
        # Check MCP endpoint
        try:
            response = await self.client.get(
                f"{N8N_MCP_ENDPOINT}/health", timeout=5
            )
            health_status["mcp"]["available"] = response.status_code == 200
        except Exception as e:
            health_status["mcp"]["error"] = str(e)
        
        return health_status


# Global dispatcher instance
_dispatcher = None


async def get_tool_dispatcher() -> ToolDispatcher:
    """Get or create the global tool dispatcher"""
    global _dispatcher
    if _dispatcher is None:
        _dispatcher = ToolDispatcher()
    return _dispatcher


async def dispatch_tool_calls(tool_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Dispatch multiple tool calls in parallel
    
    Args:
        tool_calls: List of tool call specifications
        
    Returns:
        List of tool execution results
    """
    async with ToolDispatcher() as dispatcher:
        tasks = [
            dispatcher.dispatch_tool_call(tool_call)
            for tool_call in tool_calls
        ]
        return await asyncio.gather(*tasks, return_exceptions=True)


async def get_available_tools() -> List[Dict[str, Any]]:
    """Get list of all available tools"""
    async with ToolDispatcher() as dispatcher:
        return await dispatcher.get_available_tools()


async def check_tools_health() -> Dict[str, Any]:
    """Check health of all tool endpoints"""
    async with ToolDispatcher() as dispatcher:
        return await dispatcher.health_check()
