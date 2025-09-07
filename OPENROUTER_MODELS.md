# OpenRouter Model Configuration - Quick Reference

## Updated Real Model Names

The OpenWebUI Suite has been updated with real OpenRouter model names instead of placeholder slugs. Here are the current configurations:

### Default Gateway Model
- `OPENROUTER_MODEL_DEFAULT=openai/gpt-4o-mini` (fast, cost-effective default)

### Model Priority Lists

#### Technical Queries (`OPENROUTER_PRIORITIES_TECH`)
```
openai/gpt-4o,anthropic/claude-3-5-sonnet-20241022,google/gemini-pro-1.5,meta-llama/llama-3.1-70b-instruct,qwen/qwen-2.5-72b-instruct
```
- Optimized for coding, debugging, technical analysis
- Prioritizes capability over cost

#### Legal Queries (`OPENROUTER_PRIORITIES_LEGAL`)
```
anthropic/claude-3-5-sonnet-20241022,openai/gpt-4o,cohere/command-r-plus,meta-llama/llama-3.1-70b-instruct
```
- Claude first for excellent reasoning and analysis
- Good for contract review, compliance, legal research

#### Psychotherapy (`OPENROUTER_PRIORITIES_PSYCHOTHERAPY`)
```
anthropic/claude-3-5-sonnet-20241022,openai/gpt-4o,meta-llama/llama-3.1-70b-instruct
```
- Prioritizes empathetic, conversational models
- Used with `empathy_therapist` emotion template

#### Regulated Data (`OPENROUTER_PRIORITIES_REGULATED`)
```
meta-llama/llama-3.1-8b-instruct,microsoft/phi-3-mini-128k-instruct,qwen/qwen-2.5-7b-instruct
```
- Smaller, cheaper models for sensitive data
- Often routed to local models instead

## Model Characteristics

| Model | Best For | Cost | Context |
|-------|----------|------|---------|
| `openai/gpt-4o` | General excellence, technical tasks | High | 128k |
| `openai/gpt-4o-mini` | Fast, cost-effective general use | Low | 128k |
| `anthropic/claude-3-5-sonnet-20241022` | Reasoning, analysis, empathy | High | 200k |
| `google/gemini-pro-1.5` | Multimodal, long context | Medium | 1M |
| `meta-llama/llama-3.1-70b-instruct` | Open source, good balance | Medium | 128k |
| `qwen/qwen-2.5-72b-instruct` | Coding, mathematical reasoning | Medium | 32k |
| `cohere/command-r-plus` | RAG, retrieval, legal analysis | Medium | 128k |
| `meta-llama/llama-3.1-8b-instruct` | Fast, efficient, regulated data | Low | 128k |
| `microsoft/phi-3-mini-128k-instruct` | Very efficient, large context | Low | 128k |
| `qwen/qwen-2.5-7b-instruct` | Basic tasks, regulated data | Low | 32k |

## Configuration Files Updated

1. **`compose.prod.yml`** - Docker Compose environment variables
2. **`.env.template`** - Template with OpenRouter section
3. **`.env.example`** - Example configuration with real models
4. **`openrouter_models.env`** - Ready-to-copy configuration
5. **`01-intent-router/src/rules.py`** - Hardcoded fallback models
6. **`00-pipelines-gateway/src/providers/openrouter.py`** - Default model

## Quick Setup

1. Copy `openrouter_models.env` content to your `.env` file
2. Replace `your_openrouter_api_key_here` with your actual API key
3. Adjust model priorities based on your OpenRouter account access
4. Deploy with `make deploy-check`

## Model Selection Logic

The system automatically selects models based on content classification:

1. **Content Analysis**: Intent router classifies user input into families
2. **Provider Selection**: Choose OpenRouter vs local based on sensitivity
3. **Model Priority**: Try models in priority order until one succeeds
4. **Fallback Handling**: Automatic retry on rate limits and errors
5. **Cost Optimization**: Balance capability vs cost for each use case

## Compliance Notes

- **Regulated Data**: Automatically routed to local models when `ALLOW_EXTERNAL_FOR_REGULATED=0`
- **HIPAA/PCI/GDPR**: Sensitive patterns trigger local-only routing
- **Fallback**: If all external models fail, system falls back to local models
- **Audit Trail**: All routing decisions are logged for compliance tracking

This configuration provides production-ready intelligent routing with real model names that should be available in most OpenRouter accounts.
