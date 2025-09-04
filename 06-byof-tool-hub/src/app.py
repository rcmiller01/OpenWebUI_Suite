"""
BYOF Tool Hub - Bring Your Own Function Tool Hub
Main FastAPI application for tool registry and execution

Note: Finance tools are handled by the dedicated openbb-sidecar
service (port 8120) and are not implemented in this tool hub to
maintain separation of concerns.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
import uvicorn
import logging

from .tool_registry import ToolRegistry, ToolDefinition
from .tools.calendar import calendar_get_agenda
from .tools.tasks import tasks_add
from .tools.notes import notes_capture
from .tools.web_search import web_search
from .tools.summarize_url import summarize_url

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="BYOF Tool Hub",
    description="Central tool registry and execution service for OpenWebUI Suite",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize tool registry
tool_registry = ToolRegistry()

# Register tools
tool_registry.register_tool(
    ToolDefinition(
        name="calendar_get_agenda",
        description="Get calendar agenda for a specific date",
        parameters={
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "Date in YYYY-MM-DD format"
                }
            },
            "required": ["date"]
        }
    ),
    calendar_get_agenda
)

tool_registry.register_tool(
    ToolDefinition(
        name="tasks_add",
        description="Add a new task to the task list",
        parameters={
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Task title"
                },
                "description": {
                    "type": "string",
                    "description": "Task description"
                },
                "priority": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "description": "Task priority"
                }
            },
            "required": ["title"]
        }
    ),
    tasks_add
)

tool_registry.register_tool(
    ToolDefinition(
        name="notes_capture",
        description="Capture a note with optional tags",
        parameters={
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "Note content"
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional tags for the note"
                }
            },
            "required": ["content"]
        }
    ),
    notes_capture
)

tool_registry.register_tool(
    ToolDefinition(
        name="web_search",
        description="Perform a web search and return results",
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
                    "default": 5,
                    "minimum": 1,
                    "maximum": 20
                }
            },
            "required": ["query"]
        }
    ),
    web_search
)

tool_registry.register_tool(
    ToolDefinition(
        name="summarize_url",
        description="Summarize the content of a URL",
        parameters={
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "URL to summarize"
                },
                "max_length": {
                    "type": "integer",
                    "description": "Maximum summary length in characters",
                    "default": 200,
                    "minimum": 50,
                    "maximum": 1000
                }
            },
            "required": ["url"]
        }
    ),
    summarize_url
)


class ToolExecutionRequest(BaseModel):
    """Request model for tool execution"""
    name: str = Field(..., description="Name of the tool to execute")
    arguments: Dict[str, Any] = Field(
        ..., description="Arguments for the tool"
    )


class ToolExecutionResponse(BaseModel):
    """Response model for tool execution"""
    result: Dict[str, Any] = Field(..., description="Tool execution result")
    error: Optional[str] = Field(
        None, description="Error message if execution failed"
    )


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "BYOF Tool Hub API", "version": "1.0.0"}


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy",
            "tools_registered": len(tool_registry.get_tool_definitions())}


@app.get("/tools")
async def list_tools():
    """List all available tools in OpenAI format"""
    try:
        tools = tool_registry.get_tool_definitions()
        return {"tools": tools}
    except Exception as e:
        logger.error(f"Error listing tools: {e}")
        raise HTTPException(status_code=500, detail="Failed to list tools")


@app.post("/tools/exec")
async def execute_tool(request: ToolExecutionRequest) -> ToolExecutionResponse:
    """Execute a tool with given arguments"""
    try:
        tool_result = await tool_registry.execute_tool(
            request.name, request.arguments
        )
        return ToolExecutionResponse(
            result=tool_result.result if tool_result.success else {},
            error=tool_result.error if not tool_result.success else None
        )
    except ValueError as e:
        logger.warning(f"Validation error for tool {request.name}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except TimeoutError:
        logger.error(f"Tool {request.name} execution timed out")
        raise HTTPException(status_code=408, detail="Tool execution timed out")
    except Exception as e:
        logger.error(f"Error executing tool {request.name}: {e}")
        error_msg = f"Tool execution failed: {str(e)}"
        raise HTTPException(status_code=500, detail=error_msg)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8106)
