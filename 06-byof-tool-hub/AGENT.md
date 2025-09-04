# BYOF Tool Hub (06-byof-tool-hub)

## Overview
The BYOF Tool Hub is a central tool registry and execution service for the OpenWebUI Suite. It provides a standardized interface for tool discovery and execution with built-in validation, caching, and timeout management.

## Architecture
- **Port**: 8106
- **Framework**: FastAPI with async support
- **Tool Registry**: Centralized registry with OpenAI-compatible schemas
- **Execution Engine**: Async execution with timeout enforcement
- **Caching**: Built-in caching for idempotent operations
- **Validation**: JSON schema validation for all tool inputs

## API Endpoints

### GET /tools
Returns a list of all available tools in OpenAI function format.

**Response**:
```json
{
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "calendar_get_agenda",
        "description": "Get calendar agenda for a specific date",
        "parameters": {
          "type": "object",
          "properties": {
            "date": {
              "type": "string",
              "description": "Date in YYYY-MM-DD format"
            }
          },
          "required": ["date"]
        }
      }
    }
  ]
}
```

### POST /tools/exec
Executes a tool with the given name and arguments.

**Request**:
```json
{
  "name": "calendar_get_agenda",
  "arguments": {
    "date": "2024-01-15"
  }
}
```

**Response**:
```json
{
  "result": {
    "date": "2024-01-15",
    "events": [...]
  },
  "error": null
}
```

### GET /health
Health check endpoint returning service status and tool count.

## Tools

### 1. calendar_get_agenda
Retrieves calendar events for a specific date.

**Parameters**:
- `date` (string, required): Date in YYYY-MM-DD format

**Returns**: Calendar events with titles, times, and descriptions

### 2. tasks_add
Adds a new task to the task management system.

**Parameters**:
- `title` (string, required): Task title
- `description` (string, optional): Task description
- `priority` (string, optional): Priority level (low/medium/high)

**Returns**: Task object with ID, title, and metadata

### 3. notes_capture
Captures a note with optional tags.

**Parameters**:
- `content` (string, required): Note content
- `tags` (array, optional): List of tag strings

**Returns**: Note object with ID, content, and tags

### 4. web_search
Performs a web search and returns results.

**Parameters**:
- `query` (string, required): Search query
- `max_results` (integer, optional): Maximum results (default: 5, max: 20)

**Returns**: Search results with titles, snippets, and URLs

### 5. summarize_url
Summarizes the content of a given URL.

**Parameters**:
- `url` (string, required): URL to summarize
- `max_length` (integer, optional): Maximum summary length (default: 200)

**Returns**: URL summary with metadata

## Features

### Validation
- JSON schema validation for all tool parameters
- Type checking and required field validation
- Comprehensive error messages

### Timeout Management
- Configurable per-tool timeouts (default: 30 seconds)
- Async execution with proper cancellation
- Timeout error handling

### Caching
- Automatic caching for idempotent operations
- Configurable TTL (default: 5 minutes)
- Cache key generation based on tool name and arguments

### Error Handling
- Standardized error responses
- Tool execution error capture
- Validation error reporting

### Security
- Input sanitization
- Output filtering
- Safe execution environment

## Development

### Running the Service
```bash
# Install dependencies
pip install -r requirements.txt

# Start the service
python start.py
```

### Testing
```bash
# Run API tests
python test_api.py
```

### Tool Development
Tools are implemented as async functions in the `src/tools/` directory:

```python
async def my_tool(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Tool implementation"""
    # Process arguments
    # Return result
    return {"result": "data"}
```

Tools are registered in `src/app.py` with their definitions and schemas.

## Integration

The BYOF Tool Hub integrates with other OpenWebUI Suite services:

- **Pipelines Gateway** (8088): Can execute tools via the hub
- **Intent Router** (8101): Can discover available tools
- **Memory 2.0** (8102): Can store tool execution results
- **Feeling Engine** (8103): Can analyze tool outputs
- **Hidden Multi-Expert Merger** (8104): Can execute tools
- **Drive State** (8105): Can update state based on tool usage

## Configuration

### Environment Variables
- `TOOL_TIMEOUT_SECONDS`: Default tool execution timeout
- `CACHE_TTL_SECONDS`: Cache time-to-live
- `MAX_CACHE_SIZE`: Maximum cache entries

### Tool Configuration
Each tool can be configured with:
- Custom timeout
- Idempotency flag
- Parameter schema
- Description and metadata

## Monitoring

The service provides health checks and logging for:
- Tool execution metrics
- Cache hit/miss ratios
- Error rates
- Performance monitoring

## Future Enhancements

- Tool versioning and updates
- Tool marketplace integration
- Advanced caching strategies
- Tool execution analytics
- Plugin architecture for custom tools
