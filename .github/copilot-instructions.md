# OpenWebUI Suite Project Instructions

This is a multi-repository project for creating a thin fork of OpenWebUI with a clean extension system.

## Project Structure
- **openwebui-core**: Thin fork with backend/frontend extension loaders
- **owui-plugin-template**: Python plugin template with entry points
- **owui-widget-template**: Frontend widget template for dynamic UI panels
- **owui-plugin-ollama-tools**: First real plugin with Ollama tools
- **openwebui-suite**: Meta repo with Docker composition and deployment

## Technology Stack
- Backend: FastAPI, Python 3.10+
- Frontend: React, TypeScript, Tailwind CSS
- Deployment: Docker, Docker Compose
- Package Management: PyPI, GitHub Packages

## Development Guidelines
- Keep core fork minimal - all new logic in plugins/widgets
- Use entry points for Python plugin discovery (openwebui.plugins group)
- Use GitHub Packages for Python and npm by default
- Fast CI/CD - tests must run in <3 minutes
- No hardcoded secrets - use environment variables

## Current Status
- [x] Workspace initialized
- [x] Project requirements clarified
- [x] Project scaffolded
- [x] Repositories created
- [x] Extension system implemented
- [x] Plugins developed
- [x] Docker composition setup
- [x] Documentation completed

## Repository Status

### ✅ Completed Repositories

1. **openwebui-core** - Core extension system
   - Backend plugin loader with entry points
   - Frontend widget manifest system  
   - Extension interfaces and error handling
   - Admin plugin management hooks
   - Comprehensive documentation

2. **owui-plugin-template** - Python plugin template
   - Complete plugin structure with FastAPI integration
   - Pydantic models and type safety
   - Comprehensive test suite with pytest
   - CI/CD workflow with GitHub Actions
   - Development and publishing documentation

3. **owui-plugin-ollama-tools** - Production Ollama plugin
   - Health monitoring and model management
   - Simple model routing based on criteria
   - SQLite-based memory store with full CRUD
   - Async HTTP client for Ollama API
   - Complete error handling and logging

4. **owui-widget-template** - Frontend widget template
   - TypeScript widget interface and API
   - Dynamic DOM manipulation and styling
   - Event handling and cleanup
   - Build system with TypeScript compilation
   - NPM packaging for GitHub Packages

5. **openwebui-suite** - Meta deployment repository
   - Release manifest with version pinning
   - Multi-stage Dockerfile with core + plugins
   - Comprehensive Docker Compose configuration
   - Deployment scripts and automation
   - Production-ready configuration options

## Next Steps for Implementation

1. **Create GitHub Repositories**
   - Set up 5 repositories under your GitHub organization
   - Configure repository settings and access permissions
   - Set up GitHub Packages for Python and NPM publishing

2. **Fork OpenWebUI Core**
   - Fork open-webui/open-webui to your organization
   - Implement the extension loader in the FastAPI application
   - Add widget loading to the frontend React application
   - Create minimal admin interface for plugin management

3. **Publish Plugin Packages**
   - Publish owui-plugin-template to PyPI/GitHub Packages
   - Publish owui-plugin-ollama-tools to PyPI/GitHub Packages
   - Publish owui-widget-template to GitHub NPM registry

4. **Build and Deploy Suite**
   - Build core Docker image with extension system
   - Build suite Docker image with plugins installed
   - Test deployment with docker-compose
   - Publish suite image to GitHub Container Registry

5. **Setup CI/CD**
   - Configure GitHub Actions for all repositories
   - Set up automated testing and security scanning
   - Configure automated publishing on releases
   - Set up automated suite builds on manifest changes
