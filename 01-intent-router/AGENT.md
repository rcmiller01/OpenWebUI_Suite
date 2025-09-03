# Intent Router Agent

## Goal
Tiny CPU classifier + rules to choose lane: {emotional, technical, recipes, finance, mm_image, mm_audio, general} and needs_remote flag.

## Inputs/Outputs

**Input:**
```json
{
  "text": "string",
  "last_intent": "string (optional)",
  "attachments": ["array of attachment info (optional)"]
}
```

**Output:**
```json
{
  "intent": "emotional|technical|recipes|finance|mm_image|mm_audio|general",
  "confidence": 0.95,
  "needs_remote": true
}
```

## API

- **POST /classify** → Returns classification JSON above
- **GET /health** → Health check endpoint

## Model
Any tiny transformer or ruleset; keep wheel under 100MB total.

## Folder Structure
```
/src/app.py           # FastAPI application
/src/classifier.py    # Classification logic
/src/rules.py         # Rule-based backstops
/src/model.bin        # Optional tiny model (if used)
/requirements.txt     # Dependencies
/Dockerfile          # Container deployment
/tests/              # Test suite
```

## Run
```bash
uvicorn src.app:app --port 8101
```

## Tests

- Route sample emotional text → emotional
- Code snippet → technical  
- Image attached → mm_image
- Long/complex prompts → needs_remote=true

## Dev Prompt

Build a fast classifier service with rule backstops and confidence thresholds. Return needs_remote=true for long/complex prompts.

## Features

### 🎯 **Intent Classification**
- **emotional**: Feelings, relationships, personal support
- **technical**: Code, programming, technical questions
- **recipes**: Cooking, food preparation, ingredients
- **finance**: Money, investments, budgeting, economics
- **mm_image**: Image processing, visual content
- **mm_audio**: Audio processing, speech, music
- **general**: Everything else

### 🚀 **Performance Targets**
- **Latency**: < 50ms average response time
- **Size**: < 100MB total service footprint
- **CPU**: Optimized for CPU inference
- **Accuracy**: > 85% on intent classification

### 🧠 **Classification Strategy**
1. **Rule-based** pre-filtering for obvious cases
2. **Keyword matching** for domain-specific terms
3. **Pattern recognition** for code, URLs, etc.
4. **Fallback model** for ambiguous cases
5. **Confidence scoring** with thresholds

### 📊 **Remote Processing Logic**
- **Text length** > 1000 characters
- **Complex reasoning** patterns detected
- **Multiple intents** detected (confidence < 0.8)
- **Attachment processing** required
- **Context switching** from last_intent

## Implementation Plan

1. **Rule Engine**: Fast pattern matching for obvious cases
2. **Keyword Classifier**: Domain-specific vocabulary matching  
3. **Lightweight Model**: Tiny transformer for edge cases
4. **Confidence Scoring**: Multi-signal confidence calculation
5. **Remote Logic**: Heuristics for complex request detection

## Example Usage

```bash
# Emotional intent
curl -X POST http://localhost:8101/classify \
  -H "Content-Type: application/json" \
  -d '{"text": "I feel really sad and need someone to talk to"}'

# Technical intent  
curl -X POST http://localhost:8101/classify \
  -H "Content-Type: application/json" \
  -d '{"text": "How do I implement a binary search in Python?"}'

# Multi-modal image
curl -X POST http://localhost:8101/classify \
  -H "Content-Type: application/json" \
  -d '{"text": "What is in this picture?", "attachments": [{"type": "image"}]}'
```

## Response Examples

```json
{
  "intent": "emotional",
  "confidence": 0.92,
  "needs_remote": false
}

{
  "intent": "technical", 
  "confidence": 0.88,
  "needs_remote": true
}

{
  "intent": "mm_image",
  "confidence": 0.95,
  "needs_remote": true
}
```
