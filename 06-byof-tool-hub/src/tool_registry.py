"""
Tool Registry for BYOF Tool Hub
Manages tool registration, execution, and caching
"""

import json
import asyncio
import time
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
import hashlib


@dataclass
class ToolResult:
    """Result of tool execution"""
    success: bool
    result: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    cached: bool = False


@dataclass
class ToolDefinition:
    """OpenAI-style tool definition"""
    name: str
    description: str
    parameters: Dict[str, Any]
    timeout_seconds: int = 30
    idempotent: bool = False  # Whether results can be cached


class ToolRegistry:
    """Central registry for tools with execution and caching"""

    def __init__(self):
        self.tools: Dict[str, ToolDefinition] = {}
        self.executors: Dict[str, Callable] = {}
        self.cache: Dict[str, Dict[str, Any]] = {}  # cache_key -> {result, timestamp}
        self.cache_ttl_seconds = 300  # 5 minutes

    def register_tool(self, definition: ToolDefinition, executor: Callable):
        """Register a tool with its definition and executor function"""
        self.tools[definition.name] = definition
        self.executors[definition.name] = executor

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Get all tool definitions in OpenAI format"""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters
                }
            }
            for tool in self.tools.values()
        ]

    def get_tool_definition(self, name: str) -> Optional[ToolDefinition]:
        """Get a specific tool definition"""
        return self.tools.get(name)

    async def execute_tool(self, name: str, arguments: Dict[str, Any]) -> ToolResult:
        """Execute a tool with given arguments"""
        start_time = time.time()

        # Check if tool exists
        if name not in self.tools:
            return ToolResult(
                success=False,
                error=f"Tool '{name}' not found",
                execution_time=time.time() - start_time
            )

        tool_def = self.tools[name]

        # Validate arguments against schema
        validation_error = self._validate_arguments(arguments, tool_def.parameters)
        if validation_error:
            return ToolResult(
                success=False,
                error=f"Invalid arguments: {validation_error}",
                execution_time=time.time() - start_time
            )

        # Check cache for idempotent tools
        if tool_def.idempotent:
            cache_key = self._generate_cache_key(name, arguments)
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                return ToolResult(
                    success=True,
                    result=cached_result,
                    execution_time=time.time() - start_time,
                    cached=True
                )

        # Execute tool with timeout
        try:
            executor = self.executors[name]
            result = await asyncio.wait_for(
                executor(arguments),
                timeout=tool_def.timeout_seconds
            )

            # Sanitize result
            sanitized_result = self._sanitize_output(result)

            # Cache result if idempotent
            if tool_def.idempotent:
                cache_key = self._generate_cache_key(name, arguments)
                self._cache_result(cache_key, sanitized_result)

            return ToolResult(
                success=True,
                result=sanitized_result,
                execution_time=time.time() - start_time
            )

        except asyncio.TimeoutError:
            return ToolResult(
                success=False,
                error=f"Tool execution timed out after {tool_def.timeout_seconds} seconds",
                execution_time=time.time() - start_time
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Tool execution failed: {str(e)}",
                execution_time=time.time() - start_time
            )

    def _validate_arguments(self, arguments: Dict[str, Any], schema: Dict[str, Any]) -> Optional[str]:
        """Validate arguments against JSON schema"""
        if not isinstance(arguments, dict):
            return "Arguments must be a dictionary"

        properties = schema.get("properties", {})
        required = schema.get("required", [])

        # Check required fields
        for req_field in required:
            if req_field not in arguments:
                return f"Missing required field: {req_field}"

        # Check field types and constraints
        for field, value in arguments.items():
            if field not in properties:
                continue  # Allow extra fields

            field_schema = properties[field]
            field_type = field_schema.get("type")

            # Type validation
            if field_type == "string" and not isinstance(value, str):
                return f"Field '{field}' must be a string"
            elif field_type == "number" and not isinstance(value, (int, float)):
                return f"Field '{field}' must be a number"
            elif field_type == "integer" and not isinstance(value, int):
                return f"Field '{field}' must be an integer"
            elif field_type == "boolean" and not isinstance(value, bool):
                return f"Field '{field}' must be a boolean"
            elif field_type == "array" and not isinstance(value, list):
                return f"Field '{field}' must be an array"

            # String constraints
            if field_type == "string":
                if not isinstance(value, str):
                    continue  # Skip if not actually a string
                min_length = field_schema.get("minLength")
                max_length = field_schema.get("maxLength")
                if min_length and len(value) < min_length:
                    return f"Field '{field}' must be at least {min_length} characters"
                if max_length and len(value) > max_length:
                    return f"Field '{field}' must be at most {max_length} characters"

            # Number constraints
            if field_type in ["number", "integer"]:
                minimum = field_schema.get("minimum")
                maximum = field_schema.get("maximum")
                if minimum is not None and value < minimum:
                    return f"Field '{field}' must be at least {minimum}"
                if maximum is not None and value > maximum:
                    return f"Field '{field}' must be at most {maximum}"

        return None

    def _sanitize_output(self, result: Any) -> Any:
        """Sanitize tool output to prevent information leakage"""
        if isinstance(result, dict):
            # Remove sensitive fields
            sanitized = {}
            sensitive_fields = ['password', 'token', 'key', 'secret', 'auth']
            for key, value in result.items():
                if not any(sensitive in key.lower() for sensitive in sensitive_fields):
                    sanitized[key] = self._sanitize_output(value)
            return sanitized
        elif isinstance(result, list):
            return [self._sanitize_output(item) for item in result]
        elif isinstance(result, str):
            # Limit string length
            return result[:1000] + "..." if len(result) > 1000 else result
        else:
            return result

    def _generate_cache_key(self, name: str, arguments: Dict[str, Any]) -> str:
        """Generate cache key for idempotent operations"""
        # Sort arguments for consistent hashing
        sorted_args = json.dumps(arguments, sort_keys=True)
        cache_content = f"{name}:{sorted_args}"
        return hashlib.md5(cache_content.encode()).hexdigest()

    def _get_cached_result(self, cache_key: str) -> Optional[Any]:
        """Get cached result if still valid"""
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if time.time() - cached['timestamp'] < self.cache_ttl_seconds:
                return cached['result']
            else:
                # Remove expired cache entry
                del self.cache[cache_key]
        return None

    def _cache_result(self, cache_key: str, result: Any):
        """Cache a result"""
        self.cache[cache_key] = {
            'result': result,
            'timestamp': time.time()
        }


# Global registry instance
tool_registry = ToolRegistry()
