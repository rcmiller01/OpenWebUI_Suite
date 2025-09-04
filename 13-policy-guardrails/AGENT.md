# 13-Policy-Guardrails Agent

## Overview

The Policy Guardrails service provides deterministic policy enforcement for the OpenWebUI Suite. It implements lane-specific prompt engineering, topic filtering, schema validation, and content repair mechanisms without requiring any LLM calls. All operations are performed using fast string and JSON processing.

## Architecture

- **Lane System**: Configurable policy lanes for different interaction types
- **Prompt Engineering**: Template-based system prompt construction
- **Schema Validation**: JSON schema enforcement for structured outputs
- **Content Filtering**: Topic-based content filtering and repair
- **Deterministic Processing**: No LLM dependencies, pure algorithmic processing
- **High Performance**: Optimized for low-latency policy enforcement

## Lane System

### Supported Lanes

#### Technical Lane

- **Purpose**: Technical assistance and code generation
- **Schema**: JSON schema for structured technical responses
- **Filters**: Code quality, security, and best practices
- **Validators**: Syntax validation, import checking, security scanning

#### Emotional Lane

- **Purpose**: Emotional support and empathetic responses
- **Schema**: Natural language with length constraints (3-5 sentences)
- **Filters**: Emotional appropriateness, tone consistency
- **Validators**: Length validation, emotional tone analysis

#### Creative Lane

- **Purpose**: Creative writing and ideation
- **Schema**: Flexible narrative structure
- **Filters**: Originality, coherence, engagement
- **Validators**: Structure validation, creativity metrics

#### Analytical Lane

- **Purpose**: Data analysis and reasoning
- **Schema**: Structured analytical framework
- **Filters**: Logical consistency, evidence-based reasoning
- **Validators**: Logical flow, evidence validation

## API Endpoints

### POST /policy/apply

Apply policy transformations to generate final system prompts and validators.

**Request:**

```json
{
  "lane": "technical|emotional|creative|analytical",
  "system": "Base system prompt",
  "user": "User message",
  "affect": {
    "emotion": "neutral",
    "intensity": 0.5
  },
  "drive": {
    "energy": 0.6,
    "focus": 0.8
  }
}
```

**Response:**

```json
{
  "system_final": "Enhanced system prompt with policy constraints",
  "validators": [
    {
      "type": "schema",
      "schema": {...},
      "description": "JSON schema for response validation"
    },
    {
      "type": "filter",
      "pattern": "regex_pattern",
      "description": "Content filter pattern"
    }
  ]
}
```

### POST /policy/validate

Validate content against lane policies and provide repair suggestions.

**Request:**

```json
{
  "lane": "technical|emotional|creative|analytical",
  "text": "Content to validate"
}
```

**Response:**

```json
{
  "ok": true|false,
  "repairs": [
    {
      "type": "filter",
      "issue": "Content violates policy",
      "repair": "Suggested repair action",
      "severity": "high|medium|low"
    }
  ]
}
```

## Policy Templates

### Technical Lane Template

```text
You are a technical assistant. Follow these guidelines:

1. Provide accurate, well-structured technical information
2. Include code examples when relevant
3. Explain concepts clearly and concisely
4. Follow security best practices
5. Use proper formatting for code and data structures

Response must conform to this JSON schema:
{schema}

Current context:
- User affect: {emotion} (intensity: {intensity})
- Drive state: Energy {energy}, Focus {focus}
```

### Emotional Lane Template

```text
You are an empathetic assistant providing emotional support.

Guidelines:
1. Show genuine empathy and understanding
2. Keep responses to 3-5 sentences
3. Use warm, supportive language
4. Validate feelings without judgment
5. Offer gentle guidance when appropriate

Current emotional context:
- User affect: {emotion} (intensity: {intensity})
- Drive state: Energy {energy}, Focus {focus}
```

## Schema Definitions

### Technical Response Schema

```json
{
  "type": "object",
  "properties": {
    "explanation": {
      "type": "string",
      "description": "Clear explanation of the technical concept"
    },
    "code": {
      "type": "string",
      "description": "Code example if applicable"
    },
    "best_practices": {
      "type": "array",
      "items": {"type": "string"},
      "description": "List of best practices"
    },
    "security_notes": {
      "type": "array",
      "items": {"type": "string"},
      "description": "Security considerations"
    }
  },
  "required": ["explanation"]
}
```

### Emotional Response Schema

```json
{
  "type": "object",
  "properties": {
    "acknowledgment": {
      "type": "string",
      "description": "Acknowledgment of user's feelings"
    },
    "support": {
      "type": "string",
      "description": "Supportive message"
    },
    "guidance": {
      "type": "string",
      "description": "Gentle guidance if appropriate"
    }
  },
  "additionalProperties": false
}
```

## Content Filters

### Technical Filters

- **Security Patterns**: Detect insecure code patterns
- **Import Validation**: Check for valid module imports
- **Syntax Validation**: Basic syntax checking
- **Best Practices**: Enforce coding standards

### Emotional Filters

- **Length Control**: Enforce 3-5 sentence limit
- **Tone Consistency**: Maintain supportive tone
- **Appropriateness**: Filter inappropriate content
- **Empathy Validation**: Ensure empathetic language

### Creative Filters

- **Originality Check**: Detect plagiarism patterns
- **Coherence Validation**: Ensure logical flow
- **Engagement Metrics**: Check for engaging content
- **Structure Validation**: Validate narrative structure

## Validation Engine

### Schema Validation

```python
def validate_schema(text: str, schema: dict) -> bool:
    """Validate JSON text against schema"""
    try:
        data = json.loads(text)
        return validate_json_schema(data, schema)
    except json.JSONDecodeError:
        return False
```

### Content Filtering

```python
def apply_filters(text: str, filters: list) -> list:
    """Apply content filters and return issues"""
    issues = []
    for filter_config in filters:
        if filter_config["type"] == "regex":
            if re.search(filter_config["pattern"], text):
                issues.append({
                    "type": "filter",
                    "issue": filter_config["description"],
                    "severity": filter_config["severity"]
                })
    return issues
```

### Repair Suggestions

```python
def generate_repairs(issues: list, lane: str) -> list:
    """Generate repair suggestions for validation issues"""
    repairs = []
    for issue in issues:
        repair = {
            "type": issue["type"],
            "issue": issue["issue"],
            "repair": get_repair_suggestion(issue, lane),
            "severity": issue["severity"]
        }
        repairs.append(repair)
    return repairs
```

## Configuration

### Lane Configuration

```json
{
  "lanes": {
    "technical": {
      "template": "technical_template.txt",
      "schema": "technical_schema.json",
      "filters": ["security", "syntax", "imports"],
      "max_length": 2000
    },
    "emotional": {
      "template": "emotional_template.txt",
      "schema": "emotional_schema.json",
      "filters": ["length", "tone", "appropriateness"],
      "max_sentences": 5
    }
  }
}
```

### Filter Definitions

```json
{
  "filters": {
    "security": {
      "patterns": [
        "eval\\(",
        "exec\\(",
        "password.*=.*['\"]"
      ],
      "severity": "high"
    },
    "length": {
      "max_sentences": 5,
      "severity": "medium"
    }
  }
}
```

## Performance Optimization

### Caching Strategy

- **Template Caching**: Cache compiled templates
- **Schema Caching**: Cache parsed JSON schemas
- **Filter Caching**: Cache compiled regex patterns
- **Result Caching**: Cache validation results for repeated content

### Processing Pipeline

1. **Input Validation**: Fast input sanitization
2. **Template Processing**: String interpolation
3. **Schema Application**: JSON schema validation
4. **Filter Application**: Regex pattern matching
5. **Repair Generation**: Deterministic repair suggestions

### Memory Management

- **Object Pooling**: Reuse validation objects
- **String Interning**: Intern frequently used strings
- **Garbage Collection**: Aggressive cleanup of temporary objects

## Development

### Local Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn src.app:app --reload --port 8113

# Run tests
python -m pytest tests/
```

### Testing Strategy

```python
def test_technical_lane():
    """Test technical lane policy application"""
    request = {
        "lane": "technical",
        "system": "You are a helpful assistant",
        "user": "How do I write a Python function?",
        "affect": {"emotion": "curious", "intensity": 0.7},
        "drive": {"energy": 0.8, "focus": 0.9}
    }

    response = apply_policy(request)
    assert "JSON schema" in response["system_final"]
    assert len(response["validators"]) > 0

def test_emotional_lane():
    """Test emotional lane validation"""
    text = "I understand you're feeling sad. It's okay to feel this way. Would you like to talk about what's bothering you? Remember that you're not alone in this."

    result = validate_content("emotional", text)
    assert result["ok"] == True

def test_drift_repair():
    """Test content drift detection and repair"""
    text = "Here's some code: eval(user_input)"  # Security violation

    result = validate_content("technical", text)
    assert result["ok"] == False
    assert len(result["repairs"]) > 0
    assert "security" in str(result["repairs"])
```

## Integration Points

### Pipelines Gateway Integration

```python
# Apply policy before sending to LLM
policy_result = requests.post("http://localhost:8113/policy/apply", json={
    "lane": "technical",
    "system": base_system,
    "user": user_message,
    "affect": affect_data,
    "drive": drive_data
})

enhanced_system = policy_result["system_final"]
validators = policy_result["validators"]
```

### Validation Integration

```python
# Validate LLM response
validation_result = requests.post("http://localhost:8113/policy/validate", json={
    "lane": "technical",
    "text": llm_response
})

if not validation_result["ok"]:
    # Apply repairs or reject response
    repairs = validation_result["repairs"]
    # Handle validation failures
```

## Error Handling

### Validation Errors

- **Schema Mismatch**: JSON doesn't match required schema
- **Filter Violation**: Content violates policy filters
- **Length Violation**: Content exceeds length limits
- **Format Error**: Invalid request format

### Recovery Strategies

- **Graceful Degradation**: Continue with base policies on failure
- **Repair Suggestions**: Provide actionable repair instructions
- **Fallback Templates**: Use default templates when custom ones fail
- **Logging**: Comprehensive error logging for debugging

## Monitoring and Metrics

### Performance Metrics

- **Processing Time**: Track policy application latency
- **Validation Success Rate**: Monitor validation accuracy
- **Filter Hit Rate**: Track filter effectiveness
- **Cache Hit Rate**: Monitor caching efficiency

### Health Checks

```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "lanes_loaded": len(lane_configs),
        "filters_loaded": len(filter_configs)
    }
```

## Security Considerations

### Input Validation

- **Sanitization**: Sanitize all input strings
- **Length Limits**: Enforce maximum input lengths
- **Type Checking**: Validate input data types
- **Schema Validation**: Strict JSON schema enforcement

### Content Security

- **Filter Evasion**: Detect and prevent filter bypass attempts
- **Injection Prevention**: Prevent code injection in templates
- **Data Leakage**: Prevent sensitive data exposure
- **Rate Limiting**: Implement request rate limiting

## Future Enhancements

- **Dynamic Policies**: Runtime policy updates
- **Custom Lanes**: User-defined policy lanes
- **Advanced Filters**: ML-based content filtering
- **Multi-language Support**: Support for multiple languages
- **Policy Analytics**: Detailed policy effectiveness metrics
- **Integration APIs**: REST and GraphQL API support
