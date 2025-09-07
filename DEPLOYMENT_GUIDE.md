# OpenWebUI Suite - Enhanced Routing System

A production-ready intelligent content routing system for OpenWebUI with emotional intelligence, compliance controls, and cost optimization.

## 🎯 Key Features

### Intelligent Routing System
- **Family-based Classification**: Automatically routes content to appropriate providers based on content family (TECH, LEGAL, REGULATED, PSYCHOTHERAPY, etc.)
- **Enhanced Regex Patterns**: Sophisticated pattern matching for compliance detection and content classification
- **Precedence Ordering**: PSY > REG > LEGAL > TECH > PRECISION > OPEN_ENDED for accurate classification

### Emotional Intelligence
- **5 Emotion Templates**: From no augmentation to therapeutic empathy
- **Dynamic Template Selection**: Automatic emotion template selection based on content family
- **System Prompt Augmentation**: Seamless integration with existing prompts

### Cost Optimization
- **Model Priority Fallback**: Automatic fallback through configurable model priority lists
- **OpenRouter Integration**: Cost-effective model routing with retry logic
- **Rate Limit Handling**: Intelligent retry for 402/408/409/429/5xx status codes

### Compliance & Security
- **Regulated Data Controls**: Automatic local routing for sensitive content
- **Policy Guardrails**: Built-in compliance checks for GDPR, HIPAA, PCI
- **Data Classification**: Real-time content sensitivity analysis

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.10+ (for validation scripts)
- 8GB+ RAM recommended

### Deployment

1. **Clone and Deploy**:
   ```bash
   git clone <your-repo>
   cd OpenWebUI_Suite
   make deploy-check  # Deploy core services + validate
   ```

2. **Full Stack Deployment**:
   ```bash
   make full-deploy-check  # Deploy all services + sanity check
   ```

3. **Manual Deployment**:
   ```bash
   # Core services only
   make up PROFILE=core
   
   # All services
   make up PROFILE=all
   
   # Validate deployment
   make validate
   ```

## 📊 Service Architecture

### Core Services (Profile: core)
- **Gateway** (8000): Main API gateway with projects and health endpoints
- **Intent Router** (8101): Enhanced family-based classification engine
- **Memory 2.0** (8102): Conversation memory and context management
- **Feeling Engine** (8103): Emotion template system for prompt augmentation

### Extended Services
- **Multi-Expert Merger** (8104): Response aggregation and quality control
- **Drive State** (8105): Motivational state tracking
- **BYOF Tool Hub** (8106): Custom tool integration
- **Tandoor Sidecar** (8107): Recipe and cooking assistant
- **OpenBB Sidecar** (8108): Financial data integration
- **Proactive Daemon** (8109): Background task management
- **Multimodal Router** (8110): Image/video processing pipeline
- **STT/TTS Gateway** (8111): Speech processing
- **Avatar Overlay** (8112): Visual avatar system
- **Policy Guardrails** (8113): Compliance enforcement
- **Telemetry Cache** (8114): Monitoring and metrics
- **FastVLM Sidecar** (8115): Vision-language model processing

## 🧠 Enhanced Routing Examples

### Family Classification

```python
# TECH Query → OpenRouter + No Emotion
"How do I fix this Python error?"
→ Family: TECH, Provider: OpenRouter, Template: none

# PSYCHOTHERAPY → OpenRouter + Empathy
"I'm feeling anxious about my presentation"
→ Family: PSYCHOTHERAPY, Provider: OpenRouter, Template: empathy_therapist

# LEGAL → OpenRouter + No Emotion  
"What are the GDPR requirements for data processing?"
→ Family: LEGAL, Provider: OpenRouter, Template: none

# REGULATED → Local + No Emotion
"Patient John Smith, DOB 1985-03-15, presents with chest pain"
→ Family: REGULATED, Provider: local, Template: none
```

### Emotion Templates

1. **none**: No system prompt augmentation
2. **stakes**: Emphasizes importance and consequences
3. **self_monitor**: Encourages self-reflection and analysis
4. **standards**: Promotes high-quality standards
5. **empathy_therapist**: Therapeutic empathy and support

## 🔧 Configuration

### Environment Variables

```bash
# Model Priorities (comma-separated)
OPENROUTER_MODEL_PRIORITIES="openai/gpt-4o,anthropic/claude-3-5-sonnet-20241022"
LOCAL_MODEL_PRIORITIES="llama3.2:latest,qwen2.5:14b"

# Regulated Data Controls
REGULATED_DATA_LOCAL_ONLY="true"
REGULATED_DATA_MODEL_OVERRIDE="llama3.2:latest"

# Service URLs
MEMORY_SERVICE_URL="http://memory:8102"
FEELING_SERVICE_URL="http://feeling:8103"

# API Keys
OPENROUTER_API_KEY="your-key-here"
```

### Docker Compose Profiles

```bash
# Core only (minimal deployment)
docker compose --profile core up -d

# Add memory services
docker compose --profile core --profile memory up -d

# Add emotional intelligence
docker compose --profile core --profile affect up -d

# Full deployment
docker compose --profile core --profile memory --profile affect --profile policy --profile tools up -d
```

## 🔍 Validation & Monitoring

### Quick Validation
```bash
make validate  # Fast core service check + routing test
```

### Comprehensive Sanity Check
```bash
make sanity  # All services + integration tests
```

### Manual Testing

```bash
# Test intent classification
curl -X POST http://localhost:8101/route \
  -H "Content-Type: application/json" \
  -d '{"user_text": "How do I fix this Python error?"}'

# Test emotion templates
curl http://localhost:8103/templates

# Test system prompt augmentation
curl -X POST http://localhost:8103/augment \
  -H "Content-Type: application/json" \
  -d '{"system_prompt": "You are helpful", "emotion_template_id": "empathy_therapist"}'
```

### Monitoring

- **Prometheus**: http://localhost:9090 (all 16 services monitored)
- **Service Health**: Each service exposes `/healthz` endpoint
- **Metrics**: Telemetry service at http://localhost:8114/metrics

## 📈 Performance & Scaling

### Resource Requirements

| Profile | Services | Memory | CPU | Storage |
|---------|----------|--------|-----|---------|
| core    | 4        | 2GB    | 2   | 1GB     |
| memory  | +2       | +1GB   | +1  | +2GB    |
| affect  | +3       | +1GB   | +1  | +500MB  |
| full    | 16       | 8GB    | 4   | 10GB    |

### Scaling Options

1. **Horizontal**: Use Docker Swarm or Kubernetes for multi-node deployment
2. **Vertical**: Increase container resource limits in compose.prod.yml
3. **GPU**: Use `make gpu-build` for CUDA-enabled vision/speech services

## 🛠️ Development

### Local Development

```bash
# Start core services for development
make dev:core

# Format and lint code
make format
make lint

# Run tests
make test

# Build images
make build
```

### Adding New Services

1. Create service directory: `XX-service-name/`
2. Add Dockerfile and requirements.txt
3. Update docker-compose.unified.yml with service definition
4. Add health checks and monitoring
5. Update Makefile if needed

## 🔒 Security

### Data Protection
- Regulated data automatically routed to local models
- No PHI/PII sent to external providers when detected
- Configurable data classification rules

### API Security
- Health check endpoints are public
- Service-to-service communication over Docker network
- Environment variable based configuration

### Compliance
- GDPR: EU data protection detection and local routing
- HIPAA: Healthcare data identification and isolation
- PCI: Financial data pattern matching

## 📚 API Reference

### Intent Router (8101)

```bash
POST /route
{
  "user_text": "string",
  "tags": ["optional", "array"]
}

Response:
{
  "family": "TECH|LEGAL|REGULATED|PSYCHOTHERAPY|GENERAL_PRECISION|OPEN_ENDED",
  "provider": "openrouter|local",
  "emotion_template_id": "none|stakes|self_monitor|standards|empathy_therapist",
  "confidence": 0.95,
  "matched_patterns": ["list", "of", "patterns"]
}
```

### Feeling Engine (8103)

```bash
GET /templates
Response:
{
  "templates": [...],
  "count": 5
}

POST /augment
{
  "system_prompt": "string",
  "emotion_template_id": "string"
}

Response:
{
  "augmented_prompt": "string",
  "template_used": {...}
}
```

## 🎮 Usage Examples

### Basic Chat Flow

1. User input → Intent Router classifies content family
2. Router selects provider (OpenRouter/local) and emotion template
3. Feeling Engine augments system prompt with selected template
4. Gateway routes to appropriate model with enhanced prompt
5. Response flows back through the chain

### Advanced Integrations

```python
# Python SDK example
import requests

# Classify and route
route = requests.post("http://localhost:8101/route", 
                     json={"user_text": "I need help with anxiety"}).json()

# Augment system prompt
augmented = requests.post("http://localhost:8103/augment", json={
    "system_prompt": "You are a helpful assistant",
    "emotion_template_id": route["emotion_template_id"]
}).json()

# Use enhanced prompt with selected provider
response = use_model(route["provider"], augmented["augmented_prompt"], user_input)
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Add tests for new functionality
4. Ensure all validation scripts pass
5. Submit pull request

## 📄 License

MIT License - see LICENSE file for details

## 🆘 Support

### Common Issues

1. **Service won't start**: Check Docker logs with `make logs SERVICE=service-name`
2. **Routing not working**: Verify intent router health and configuration
3. **Templates not loading**: Check feeling engine emotion_templates.json file
4. **High memory usage**: Consider using core profile only for development

### Debugging

```bash
# Check service health
make validate

# View logs
make logs SERVICE=intent-router

# Check configuration
make compose-validate

# Full system check
make sanity
```

For additional support, see AGENT.md files in each service directory.
