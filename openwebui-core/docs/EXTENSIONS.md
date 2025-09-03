# OpenWebUI Extensions Documentation

This document describes how to create and use extensions in OpenWebUI, including both backend plugins and frontend widgets.

## Overview

The OpenWebUI extension system consists of two main components:

1. **Backend Plugins**: Python packages that extend the FastAPI application
2. **Frontend Widgets**: JavaScript/TypeScript modules that add UI components

## Backend Plugin Development

### Plugin Structure

Backend plugins are Python packages that use entry points for automatic discovery. Each plugin must implement a `register` function that accepts a FastAPI application instance.

### Entry Point Configuration

Add this to your plugin's `pyproject.toml`:

```toml
[project.entry-points."openwebui.plugins"]
your_plugin_name = "your_package.plugin:register"
```

### Plugin Interface

```python
from fastapi import APIRouter, FastAPI

def register(app: FastAPI) -> None:
    """Register plugin routes and functionality."""
    router = APIRouter(prefix="/ext/your-plugin", tags=["your-plugin"])
    
    @router.get("/health")
    async def health():
        return {"ok": True, "plugin": "your-plugin"}
    
    app.include_router(router)
```

### Plugin Development Guidelines

1. **Namespace Routes**: Always use `/ext/{plugin-name}` prefix
2. **Error Handling**: Use FastAPI's HTTPException for errors
3. **Documentation**: Include OpenAPI/Swagger documentation
4. **Logging**: Use structured logging with plugin context
5. **Configuration**: Use environment variables for configuration

### Example Plugin

```python
import os
from fastapi import APIRouter, FastAPI, HTTPException

def register(app: FastAPI) -> None:
    config = {
        "api_key": os.getenv("YOUR_PLUGIN_API_KEY"),
        "timeout": int(os.getenv("YOUR_PLUGIN_TIMEOUT", "30"))
    }
    
    router = APIRouter(prefix="/ext/your-plugin", tags=["your-plugin"])
    
    @router.get("/health")
    async def health():
        return {
            "ok": True,
            "plugin": "your-plugin",
            "version": "1.0.0"
        }
    
    @router.get("/data")
    async def get_data():
        if not config["api_key"]:
            raise HTTPException(
                status_code=500, 
                detail="API key not configured"
            )
        
        # Your plugin logic here
        return {"data": "example"}
    
    app.include_router(router)
```

## Frontend Widget Development

### Widget Structure

Frontend widgets are JavaScript/TypeScript modules that export a registration function. Widgets are loaded dynamically based on the manifest configuration.

### Widget Interface

```typescript
interface WidgetConfig {
  id: string;
  title: string;
  description?: string;
  mount: (element: HTMLElement) => Promise<void> | void;
  unmount?: (element: HTMLElement) => Promise<void> | void;
  onResize?: (element: HTMLElement) => void;
}

export function registerWidget(): WidgetConfig {
  return {
    id: "your-widget",
    title: "Your Widget",
    mount: async (element: HTMLElement) => {
      // Create and mount your widget UI
      element.innerHTML = "<div>Your widget content</div>";
    }
  };
}
```

### Widget Registration

Widgets are registered via the manifest file at `/web/extensions/widgets/manifest.json`:

```json
{
  "widgets": [
    {
      "id": "your-widget",
      "name": "Your Widget",
      "version": "1.0.0",
      "url": "/extensions/widgets/your-widget/index.js",
      "enabled": true,
      "config": {
        "position": "sidebar",
        "order": 1
      }
    }
  ]
}
```

### Widget Development Guidelines

1. **Clean Mounting**: Always clean up when unmounting
2. **Responsive Design**: Handle resize events appropriately
3. **Error Handling**: Gracefully handle loading and runtime errors
4. **Performance**: Minimize bundle size and load time
5. **Accessibility**: Follow accessibility best practices

## Extension Discovery

### Backend Plugin Discovery

The extension loader scans Python entry points in the `openwebui.plugins` group:

```python
from backend.extensions import load_plugins

# In your FastAPI app startup
app = FastAPI()
load_plugins(app)
```

### Frontend Widget Discovery

The widget loader reads the manifest file and dynamically imports widgets:

```typescript
// Load widgets from manifest
const manifest = await fetch('/extensions/widgets/manifest.json');
const config = await manifest.json();

for (const widget of config.widgets) {
  if (widget.enabled) {
    const module = await import(widget.url);
    const widgetConfig = module.registerWidget();
    // Mount widget...
  }
}
```

## Configuration

### Environment Variables

Plugins can use environment variables for configuration:

- `OPENWEBUI_PLUGIN_*`: Plugin-specific configuration
- `OPENWEBUI_WIDGET_*`: Widget-specific configuration
- `OPENWEBUI_EXTENSION_*`: General extension configuration

### Plugin Configuration

```python
import os

def register(app: FastAPI) -> None:
    config = {
        "enabled": os.getenv("OPENWEBUI_PLUGIN_ENABLED", "true").lower() == "true",
        "debug": os.getenv("OPENWEBUI_PLUGIN_DEBUG", "false").lower() == "true",
        "timeout": int(os.getenv("OPENWEBUI_PLUGIN_TIMEOUT", "30"))
    }
    
    if not config["enabled"]:
        return  # Skip registration
    
    # Register plugin...
```

## Testing

### Plugin Testing

```python
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from your_plugin.plugin import register

@pytest.fixture
def app():
    test_app = FastAPI()
    register(test_app)
    return test_app

@pytest.fixture
def client(app):
    return TestClient(app)

def test_plugin_health(client):
    response = client.get("/ext/your-plugin/health")
    assert response.status_code == 200
    assert response.json()["ok"] is True
```

### Widget Testing

```typescript
import { registerWidget } from './widget';

describe('Widget Registration', () => {
  it('should return valid widget config', () => {
    const config = registerWidget();
    
    expect(config.id).toBeDefined();
    expect(config.title).toBeDefined();
    expect(typeof config.mount).toBe('function');
  });
  
  it('should mount without errors', async () => {
    const config = registerWidget();
    const element = document.createElement('div');
    
    await expect(config.mount(element)).resolves.toBeUndefined();
    expect(element.children.length).toBeGreaterThan(0);
  });
});
```

## Deployment

### Plugin Packaging

1. Package as standard Python wheel
2. Publish to PyPI or GitHub Packages
3. Include in deployment via pip install

### Widget Packaging

1. Build as JavaScript/TypeScript module
2. Publish to npm or GitHub Packages
3. Include in build process or serve statically

### Docker Integration

```dockerfile
# Install plugins
RUN pip install your-plugin==1.0.0

# Copy widgets
COPY widgets/ /app/web/extensions/widgets/
```

## Admin Interface

The admin interface provides information about loaded extensions:

- **Plugin Status**: View loaded and failed plugins
- **Widget Management**: Enable/disable widgets
- **Configuration**: Manage extension settings
- **Logs**: View extension loading logs

Access the admin interface at `/admin/extensions`.

## Troubleshooting

### Common Plugin Issues

1. **Import Errors**: Check Python path and dependencies
2. **Registration Failures**: Verify entry point configuration
3. **Route Conflicts**: Ensure unique route prefixes
4. **Configuration Issues**: Check environment variables

### Common Widget Issues

1. **Loading Failures**: Check manifest configuration and file paths
2. **Mount Errors**: Verify DOM manipulation and async handling
3. **Performance Issues**: Optimize bundle size and loading
4. **Browser Compatibility**: Test across different browsers

### Debug Mode

Enable debug logging:

```bash
export OPENWEBUI_DEBUG=true
export OPENWEBUI_LOG_LEVEL=DEBUG
```

## Examples

### Complete Plugin Example

See the `owui-plugin-ollama-tools` repository for a complete plugin implementation.

### Complete Widget Example

See the `owui-widget-template` repository for a complete widget implementation.

## Contributing

1. Follow the plugin/widget development guidelines
2. Include comprehensive tests
3. Document configuration options
4. Provide usage examples
5. Submit pull requests with clear descriptions

## Support

- **Documentation**: GitHub Wiki
- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Examples**: Template repositories
