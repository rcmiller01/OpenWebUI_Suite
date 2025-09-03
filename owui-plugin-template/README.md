# OpenWebUI Plugin Template

A template for creating OpenWebUI plugins with FastAPI backend integration.

## Overview

This template provides a standardized structure for developing OpenWebUI plugins using Python entry points and FastAPI routing. It includes testing framework, CI/CD configuration, and documentation templates.

## Features

- **Entry Point System**: Automatic plugin discovery via `openwebui.plugins` group
- **FastAPI Integration**: Clean router-based API endpoints
- **Type Safety**: Full Pydantic model support and type hints
- **Testing Framework**: Comprehensive test suite with pytest
- **CI/CD Ready**: GitHub Actions configuration included
- **Documentation**: Complete API documentation and usage examples

## Quick Start

### 1. Installation

```bash
# Install from PyPI (when published)
pip install owui-plugin-template

# Or install from source
git clone <repo-url>
cd owui-plugin-template
pip install -e .
```

### 2. Development Setup

```bash
# Install with development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src tests
isort src tests

# Type checking
mypy src
```

### 3. Using as Template

```bash
# Copy template structure
cp -r owui-plugin-template my-new-plugin
cd my-new-plugin

# Update package name and metadata
# Edit pyproject.toml, src/ directory names, imports
```

## Project Structure

```
owui-plugin-template/
├── src/owui_plugin_template/
│   ├── __init__.py          # Package initialization
│   └── plugin.py            # Main plugin registration
├── tests/
│   └── test_smoke.py        # Basic functionality tests
├── pyproject.toml           # Package configuration
├── README.md               # This file
└── .github/workflows/      # CI/CD configuration
```

## Plugin Development

### Entry Point Registration

The plugin uses Python entry points for automatic discovery:

```toml
[project.entry-points."openwebui.plugins"]
template = "owui_plugin_template.plugin:register"
```

### Plugin Interface

All plugins must implement a `register(app: FastAPI) -> None` function:

```python
from fastapi import APIRouter, FastAPI

def register(app: FastAPI) -> None:
    """Register plugin routes with the FastAPI application."""
    router = APIRouter(prefix="/ext/template", tags=["owui-template"])
    
    @router.get("/health")
    async def health():
        return {"ok": True, "plugin": "template"}
    
    app.include_router(router)
```

### API Endpoints

The template provides these endpoints:

- **GET /ext/template/health**: Health check and plugin status
- **GET /ext/template/info**: Plugin metadata and capabilities

## Configuration

Environment variables can be used for plugin configuration:

```python
import os

# Example configuration
PLUGIN_DEBUG = os.getenv("OWUI_TEMPLATE_DEBUG", "false").lower() == "true"
PLUGIN_PREFIX = os.getenv("OWUI_TEMPLATE_PREFIX", "/ext/template")
```

## Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=owui_plugin_template

# Run specific test file
pytest tests/test_smoke.py -v
```

## Building and Publishing

```bash
# Build wheel
python -m build

# Publish to PyPI (configure credentials first)
python -m twine upload dist/*

# Publish to GitHub Packages
# Configure .pypirc for GitHub registry
python -m twine upload --repository github dist/*
```

## Extension Points

The template can be extended with:

- **Custom Models**: Add Pydantic models in `models.py`
- **Database Integration**: Add database connections and ORM
- **External APIs**: Add HTTP clients for external services
- **Background Tasks**: Add Celery or background job support
- **Authentication**: Add custom auth middleware

## Best Practices

1. **Namespace Routes**: Always use `/ext/{plugin-name}` prefix
2. **Type Annotations**: Use Pydantic models for request/response
3. **Error Handling**: Implement proper HTTP error responses
4. **Logging**: Use structured logging with plugin context
5. **Documentation**: Include OpenAPI/Swagger documentation
6. **Testing**: Maintain >90% test coverage

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

- **Issues**: GitHub Issues
- **Documentation**: GitHub Wiki
- **Discussions**: GitHub Discussions

---

**Created**: September 3, 2025  
**Version**: 0.1.0  
**Compatibility**: OpenWebUI Core v1.x
