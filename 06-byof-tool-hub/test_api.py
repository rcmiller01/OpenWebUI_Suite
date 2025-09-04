#!/usr/bin/env python3
"""
BYOF Tool Hub - API Tests
Tests the tool registry and execution endpoints
"""

import asyncio
import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.tool_registry import ToolRegistry, ToolDefinition
from src.tools.calendar import calendar_get_agenda
from src.tools.tasks import tasks_add
from src.tools.notes import notes_capture
from src.tools.web_search import web_search
from src.tools.summarize_url import summarize_url


async def test_tool_registry():
    """Test the tool registry functionality"""
    print("Testing Tool Registry...")

    registry = ToolRegistry()

    # Register tools
    registry.register_tool(
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

    registry.register_tool(
        ToolDefinition(
            name="tasks_add",
            description="Add a new task to the task list",
            parameters={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Task title"
                    }
                },
                "required": ["title"]
            }
        ),
        tasks_add
    )

    # Test tool definitions
    tools = registry.get_tool_definitions()
    print(f"Registered tools: {len(tools)}")
    assert len(tools) == 2

    # Test tool execution
    result = await registry.execute_tool(
        "calendar_get_agenda", {"date": "2024-01-15"}
    )
    print(f"Calendar tool result: {result.success}")
    assert result.success

    result = await registry.execute_tool("tasks_add", {"title": "Test task"})
    print(f"Tasks tool result: {result.success}")
    assert result.success

    print("✓ Tool Registry tests passed")


async def test_individual_tools():
    """Test individual tool functions directly"""
    print("\nTesting Individual Tools...")

    # Test calendar tool
    result = await calendar_get_agenda({"date": "2024-01-15"})
    print(f"Calendar result: {result}")
    assert "agenda" in result
    assert "total_events" in result

    # Test tasks tool
    result = await tasks_add(
        {"title": "Test task", "description": "Test description"}
    )
    print(f"Tasks result: {result}")
    assert "task" in result
    assert "id" in result["task"]
    assert result["task"]["title"] == "Test task"

    # Test notes tool
    result = await notes_capture({"content": "Test note", "tags": ["test"]})
    print(f"Notes result: {result}")
    assert "note" in result
    assert "id" in result["note"]
    assert result["note"]["content"] == "Test note"

    # Test web search tool
    result = await web_search({"query": "test query"})
    print(f"Web search result: {result}")
    assert "results" in result
    assert len(result["results"]) > 0

    # Test summarize URL tool
    result = await summarize_url({"url": "https://github.com/example"})
    print(f"Summarize URL result: {result}")
    assert "summary" in result
    assert "url" in result

    print("✓ Individual tool tests passed")


async def test_validation():
    """Test input validation"""
    print("\nTesting Validation...")

    registry = ToolRegistry()

    async def test_executor(args):
        return {"result": "success"}

    registry.register_tool(
        ToolDefinition(
            name="test_tool",
            description="Test tool",
            parameters={
                "type": "object",
                "properties": {
                    "required_field": {"type": "string"}
                },
                "required": ["required_field"]
            }
        ),
        test_executor
    )

    # Test missing required field
    result = await registry.execute_tool("test_tool", {})
    print(f"Validation error: {result.error}")
    assert not result.success
    assert result.error and "required" in result.error.lower()

    # Test valid input
    result = await registry.execute_tool(
        "test_tool", {"required_field": "test"}
    )
    print(f"Valid execution: {result.success}")
    assert result.success

    print("✓ Validation tests passed")


async def main():
    """Run all tests"""
    print("Running BYOF Tool Hub Tests...\n")

    try:
        await test_tool_registry()
        await test_individual_tools()
        await test_validation()

        print("\n🎉 All tests passed!")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
