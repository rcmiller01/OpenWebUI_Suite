# Enhanced Intent Router and Emotion Templates Implementation

## Overview

This implementation adds sophisticated content family classification and emotion template routing to the OpenWebUI Suite, enabling:

1. **Family-based Content Classification** - Routes inputs based on content type (TECH, LEGAL, REGULATED, etc.)
2. **Emotion Template Augmentation** - Applies appropriate emotional context to system prompts
3. **Model Priority Routing** - Tries models in preference order with fallback
4. **Compliance Controls** - Keeps regulated data local by default

## Key Components

### 1. Feeling Engine - Emotion Templates

**File**: `03-feeling-engine/emotion_templates.json`

Available templates:
- `none` - No emotional augmentation
- `stakes` - High-stakes diligence mode
- `self_monitor` - Self-monitoring and verification
- `standards` - Professional standard response
- `empathy_therapist` - Therapeutic empathy (non-diagnostic)

**New Endpoints**:
- `POST /augment` - Apply emotion template to system prompt
- `GET /templates` - List available templates

### 2. Intent Router - Family Classification

**File**: `01-intent-router/src/rules.py`

Content families with automatic classification:
- `TECH` - Code, debugging, programming (→ OpenRouter, no emotion)
- `LEGAL` - Contracts, compliance, legal terms (→ OpenRouter, no emotion)
- `REGULATED` - SOX, PCI-DSS, HIPAA, etc. (→ Local by default, no emotion)
- `PSYCHOTHERAPY` - Mental health, therapy, emotions (→ OpenRouter, empathy template)
- `GENERAL_PRECISION` - Math, proofs, step-by-step (→ Local, self-monitor template)
- `OPEN_ENDED` - General conversation (→ Local, stakes template)

**New Endpoints**:
- `POST /route` - Get routing recommendations based on content family

### 3. Gateway - OpenRouter Provider

**File**: `00-pipelines-gateway/src/providers/openrouter.py`

Features:
- Model priority with automatic fallback
- Retry logic for rate limits and errors
- Health checking and monitoring

## Configuration

### Environment Variables

```bash
# OpenRouter API
OPENROUTER_API_KEY=your_api_key
OPENROUTER_API_BASE=https://openrouter.ai/api/v1/chat/completions
OPENROUTER_MODEL_DEFAULT=openrouter/auto
OPENROUTER_TIMEOUT=60

# Model Priorities (comma-separated)
OPENROUTER_PRIORITIES_TECH=qwen/qwen-2.5-coder-32b-instruct:free,qwen/qwen-2.5-coder-32b-instruct,...
OPENROUTER_PRIORITIES_LEGAL=anthropic/claude-3.5-sonnet:free,anthropic/claude-3.5-sonnet,...
OPENROUTER_PRIORITIES_PSYCHOTHERAPY=anthropic/claude-3.5-sonnet:free,...
OPENROUTER_PRIORITIES_REGULATED=  # Empty = local only

# Compliance
ALLOW_EXTERNAL_FOR_REGULATED=0  # 0=local only, 1=allow external

# Service URLs
FEELING_URL=http://feeling:8103
INTENT_URL=http://intent:8101
```

### Docker Compose Updates

Both intent router and gateway services now include the new environment variables for seamless integration.

## Usage Examples

### 1. Route a User Input

```python
import requests

# Get routing recommendation
response = requests.post("http://localhost:8101/route", json={
    "user_text": "How do I fix this Python error?",
    "tags": []
})

result = response.json()
# {
#   "family": "TECH",
#   "emotion_template_id": "none", 
#   "provider": "openrouter",
#   "openrouter_model_priority": ["qwen/qwen-2.5-coder-32b-instruct:free", ...],
#   "tags": ["no_emotion"]
# }
```

### 2. Apply Emotion Template

```python
# Augment system prompt with emotion template
response = requests.post("http://localhost:8103/augment", json={
    "system_prompt": "You are a helpful AI assistant.",
    "emotion_template_id": "empathy_therapist"
})

result = response.json()
# {
#   "system_prompt": "You are a helpful AI assistant.\n\nUse a supportive, nonjudgmental tone...",
#   "template_id": "empathy_therapist",
#   "template_label": "Therapeutic empathy (supportive, non-diagnostic)"
# }
```

### 3. Full Pipeline Integration

```python
# 1. Get routing decision
route = requests.post("http://localhost:8101/route", json={"user_text": user_input}).json()

# 2. Apply emotion template
augmented = requests.post("http://localhost:8103/augment", json={
    "system_prompt": base_prompt,
    "emotion_template_id": route["emotion_template_id"]
}).json()

# 3. Call appropriate provider
if route["provider"] == "openrouter":
    from providers import openrouter
    response = openrouter.chat(
        messages=[
            {"role": "system", "content": augmented["system_prompt"]},
            {"role": "user", "content": user_input}
        ],
        model_priority=route["openrouter_model_priority"]
    )
else:
    response = call_local_llm(messages)
```

## Compliance Features

### Regulated Data Protection

- **Automatic Detection**: Regex patterns identify SOX, PCI-DSS, HIPAA, FERPA, etc.
- **Local-First**: Regulated content stays local by default
- **Override Control**: `ALLOW_EXTERNAL_FOR_REGULATED=1` enables external APIs (⚠️ compliance risk)
- **Audit Trail**: All routing decisions logged with reasoning

### Content Family Safeguards

- **TECH/LEGAL/REGULATED**: Automatically tagged with `no_emotion` to prevent inappropriate tone
- **PSYCHOTHERAPY**: Uses empathy template but remains non-diagnostic
- **Transparent Routing**: All decisions include reasoning for audit

## Testing

Run the comprehensive test suite:

```bash
python test_enhanced_routing.py
```

Tests cover:
- Family classification accuracy
- Emotion template application
- Model priority fallback
- Service health checks
- End-to-end routing pipeline

## Benefits

1. **Content-Aware Routing**: Right model for the right content type
2. **Cost Optimization**: Free models first, paid models as fallback
3. **Compliance Ready**: Regulated data protection built-in
4. **Emotional Intelligence**: Appropriate tone for context
5. **Transparent Decisions**: Full audit trail for all routing choices
6. **Extensible Design**: Easy to add new families, templates, and providers

This implementation provides a production-ready foundation for intelligent content routing with compliance safeguards and emotional intelligence.
