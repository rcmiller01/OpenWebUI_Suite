# Hidden Multi-Expert Merger Service

## Overview
The Hidden Multi-Expert Merger service combines draft text with critiques from multiple helper agents to produce a final, polished output that maintains the target persona while incorporating improvements.

## Architecture
- **Port**: 8104
- **Framework**: FastAPI with async processing
- **Templates**: Deterministic merge templates (persona-preserving, concise-executive, creative-enhancement)
- **Helpers**: Simulated local sub-10B models with budget constraints

## API Endpoints

### POST /compose
Compose final text from draft with helper critiques.

**Request:**
```json
{
  "prompt": "Draft text to improve",
  "persona": "Target persona (e.g., 'Senior Project Manager')",
  "tone_policy": ["professional", "concise"],
  "budgets": {
    "time_ms": 1500,
    "max_helpers": 2,
    "template": "persona_preserving"
  }
}
```

**Response:**
```json
{
  "final_text": "Improved final text with persona preserved",
  "processing_time_ms": 450.2,
  "helpers_used": 2,
  "tokens_used": 240
}
```

### GET /health
Health check endpoint.

### GET /templates
List available merge templates.

## Key Features

### Budget Enforcement
- **Helper Token Cap**: ≤ 120 tokens per helper
- **Time Budget**: Default 1500ms, strictly enforced
- **Helper Limit**: Configurable max helpers (default: 3)

### Clean Output
- **No Helper Chatter**: Strips AI self-references, tool language, meta-commentary
- **Persona Preservation**: Maintains target persona throughout output
- **Deterministic Merging**: Consistent results with same inputs

### Merge Templates
1. **persona_preserving**: Maintains original persona while incorporating critiques
2. **concise_executive**: Produces brief, professional communication
3. **creative_enhancement**: Adds creative elements and vivid language

## Helper Types
- **ConciseEditor**: Focuses on clarity and brevity
- **CreativeEnhancer**: Adds imagery and engagement
- **GeneralReviewer**: Provides balanced improvement suggestions

## Performance
- **Latency**: < 50ms per call (typical)
- **Throughput**: Handles multiple concurrent requests
- **Resource Usage**: CPU-only, no GPU requirements

## Usage Examples

### Basic Composition
```python
import requests

response = requests.post("http://localhost:8104/compose", json={
    "prompt": "Write a product description",
    "persona": "Marketing Specialist",
    "tone_policy": ["engaging", "professional"]
})
```

### With Budget Constraints
```python
response = requests.post("http://localhost:8104/compose", json={
    "prompt": "Draft email to client",
    "persona": "Account Executive",
    "tone_policy": ["courteous", "concise"],
    "budgets": {
        "time_ms": 1000,
        "max_helpers": 1,
        "template": "concise_executive"
    }
})
```

## Development

### Running the Service
```bash
cd 04-hidden-multi-expert-merger
python start.py
```

### Testing
```bash
python test_api.py
```

### Requirements
- Python 3.10+
- FastAPI
- Uvicorn
- Pydantic

## Integration
This service integrates with other OpenWebUI Suite services:
- Receives drafts from **Pipelines Gateway** (port 8088)
- Uses affect analysis from **Feeling Engine** (port 8103)
- Can be orchestrated with **Intent Router** (port 8101) and **Memory 2.0** (port 8102)
