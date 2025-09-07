# Projects Feature Integration Guide

## Backend Setup

The projects feature is automatically available in the gateway service. No additional dependencies required (uses Python stdlib sqlite3).

### Environment Variables

```bash
GATEWAY_DB=/data/gateway.db    # Database file path
```

### Docker Volume

Ensure the gateway container has a persistent volume for the database:

```yaml
services:
  pipelines-gateway:
    volumes:
      - gateway_data:/data
volumes:
  gateway_data:
```

## Frontend Integration

### 1. Install the Component

Copy `ProjectsSidebar.tsx` to your React components directory.

### 2. Feature Flag

Add environment variable support:

```typescript
// In your app config or environment
const ENABLE_PROJECTS = import.meta.env.VITE_ENABLE_PROJECTS === "1";
```

### 3. Integration Example

```typescript
import ProjectsSidebar from "./components/ProjectsSidebar";

function App() {
  const [currentProject, setCurrentProject] = useState<string | null>(null);
  const [showProjects, setShowProjects] = useState(ENABLE_PROJECTS);

  return (
    <div className="flex h-screen">
      {showProjects && (
        <ProjectsSidebar
          currentProjectId={currentProject}
          onProjectSelect={setCurrentProject}
        />
      )}
      <main className="flex-1">
        {/* Your main content */}
      </main>
    </div>
  );
}
```

### 4. Build-time Configuration

Add to your Dockerfile or build environment:

```dockerfile
ARG ENABLE_PROJECTS=0
ENV VITE_ENABLE_PROJECTS=${ENABLE_PROJECTS}
```

## API Reference

### Projects

- `GET /projects` - List all projects
- `POST /projects` - Create project (body: `{"name": "string"}`)
- `DELETE /projects/{id}` - Delete project

### Project Items

- `GET /projects/{id}/items` - List conversation IDs in project
- `POST /projects/{id}/items` - Add conversation (body: `{"convo_id": "string"}`)
- `DELETE /projects/{id}/items/{convo_id}` - Remove conversation

## Database Schema

```sql
CREATE TABLE projects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    created_at INTEGER NOT NULL
);

CREATE TABLE project_items (
    project_id TEXT NOT NULL,
    convo_id TEXT NOT NULL,
    PRIMARY KEY (project_id, convo_id),
    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
);
```

## Security Considerations

- No authentication implemented (add as needed)
- SQLite uses WAL mode for better concurrency
- File-based storage requires proper volume permissions
- Input validation on project names recommended

## Testing

```bash
# Test project creation
curl -X POST http://localhost:8088/projects \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Project"}'

# Test project listing
curl http://localhost:8088/projects

# Test item management
curl -X POST http://localhost:8088/projects/{project_id}/items \
  -H "Content-Type: application/json" \
  -d '{"convo_id":"test-conversation-123"}'
```
