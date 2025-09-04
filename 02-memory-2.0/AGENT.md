# Memory 2.0 Agent - ✅ COMPLETED

## 📋 Overview

**Memory 2.0** is a persistent memory system for the OpenWebUI Suite that provides intelligent storage and retrieval of user information through a dual-layer architecture:

1. **Traits Storage**: Key-value pairs in SQLite for user characteristics (preferences, occupation, location, etc.)
2. **Episodic Storage**: Semantic memory of conversation events with summaries

## 🎯 Key Features

- **Dual Memory Architecture**: SQL for traits + SQLite for episodes
- **PII Filtering**: Automatic detection and filtering of personally identifiable information
- **Memory Write Policy**: Only stores high-confidence memories (>0.7 confidence) 
- **Compact Summaries**: Summarizes memories to ≤200 tokens
- **Trait Extraction**: Rule-based extraction of user characteristics
- **Text Search**: Simple search functionality across stored episodes

## 🚀 Status: ✅ COMPLETED

The Memory 2.0 service is fully implemented and tested with:
- ✅ Dual storage architecture (traits + episodes)
- ✅ PII filtering and confidence thresholds  
- ✅ RESTful API with comprehensive endpoints
- ✅ SQLite database with proper schema
- ✅ Memory extraction and summarization
- ✅ Text search and retrieval
- ✅ Service startup and health monitoring
- ✅ API testing and validation

## API

### Write Memory Candidates
**POST /mem/candidates**
```json
{
  "user_id": "string",
  "text": "string", 
  "tags": ["array"],
  "confidence": 0.85
}
```

### Retrieve Relevant Memories  
**GET /mem/retrieve?user_id={id}&intent={intent}&k=4**
```json
{
  "traits": [{"key": "string", "value": "string", "confidence": 0.9}],
  "episodes": [{"text": "string", "tags": ["array"], "timestamp": "iso"}]
}
```

### Get Memory Summary
**GET /mem/summary?user_id={id}**
```json
{
  "summary": "Compact summary ≤200 tokens",
  "traits_count": 15,
  "episodes_count": 42,
  "last_updated": "iso"
}
```

## Schema

### Traits (SQL)
```sql
traits(
  user_id VARCHAR(255),
  key VARCHAR(255), 
  value TEXT,
  confidence FLOAT,
  updated_at TIMESTAMP,
  PRIMARY KEY (user_id, key)
)
```

### Episodes (Vector DB)
```sql
episodes(
  id UUID PRIMARY KEY,
  user_id VARCHAR(255),
  text TEXT,
  tags JSON,
  timestamp TIMESTAMP,
  embedding VECTOR(384)
)
```

## Folder Structure
```
/src/app.py           # FastAPI application
/src/db.sql           # Database schema
/src/embeddings.py    # Vector embedding service
/src/memory.py        # Memory management logic
/src/traits.py        # Traits storage (SQL)
/src/episodes.py      # Episodic storage (vector)
/docker-compose.yml   # Postgres + Vector DB
/requirements.txt     # Dependencies
/tests/               # Test suite
```

## Run
```bash
# Start databases
docker compose up -d

# Run service
uvicorn src.app:app --port 8102
```

## Tests

- Write 3 candidates
- Retrieve top-K relevant memories  
- Generate summary ≤200 tokens
- Test memory write policies
- Validate PII filtering

## Dev Prompt

Implement memory write policy (ignore low-confidence, PII). Summarize traits+episodic into ≤200 tokens.

## Features

### 🧠 **Dual Memory Architecture**
- **Traits**: Key-value facts stored in SQL (PostgreSQL)
- **Episodes**: Semantic memories in vector database (Chroma/Weaviate)
- **Hybrid Retrieval**: Combine structured and semantic search

### 🔍 **Intelligent Retrieval**
- **Intent-based**: Filter memories by user intent
- **Semantic Search**: Vector similarity for episodes
- **Trait Matching**: Exact and fuzzy key matching
- **Relevance Ranking**: Confidence-weighted results

### 📝 **Memory Write Policies**
- **Confidence Filtering**: Ignore low-confidence memories
- **PII Detection**: Filter sensitive information
- **Deduplication**: Prevent redundant storage
- **Trait Extraction**: Auto-extract key-value pairs

### 📊 **Compact Summaries**
- **Token Limit**: ≤200 tokens per summary
- **Trait Synthesis**: Key facts about user
- **Episode Highlights**: Important interactions
- **Temporal Awareness**: Recent vs. historical context

## Implementation Strategy

### 1. **Memory Write Pipeline**
```
Input → PII Filter → Confidence Check → Trait Extract → Vector Embed → Store
```

### 2. **Memory Retrieval Pipeline** 
```
Query → Intent Parse → Trait Search + Semantic Search → Rank → Summarize
```

### 3. **Summary Generation**
```
Traits + Episodes → Template Fill → Token Count → Compress → Return
```

## Configuration

### Environment Variables
- `POSTGRES_URL`: Database connection string
- `VECTOR_DB_URL`: Vector database endpoint  
- `EMBEDDING_MODEL`: Model for text embeddings
- `PII_THRESHOLD`: Confidence threshold for PII detection
- `MEMORY_THRESHOLD`: Minimum confidence for storage

### Vector Database Options
- **Chroma**: Lightweight, embeddable
- **Weaviate**: Production-scale with GraphQL
- **Qdrant**: High-performance vector search

## Example Usage

### Store Memory
```bash
curl -X POST http://localhost:8102/mem/candidates \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "text": "I love hiking in the mountains on weekends",
    "tags": ["hobby", "outdoor", "weekend"],
    "confidence": 0.9
  }'
```

### Retrieve Memories
```bash
curl "http://localhost:8102/mem/retrieve?user_id=user123&intent=hobby&k=4"
```

### Get Summary
```bash
curl "http://localhost:8102/mem/summary?user_id=user123"
```

## Performance Targets

- **Write Latency**: < 100ms per candidate
- **Retrieval Latency**: < 50ms for summary
- **Storage Efficiency**: Deduplicated, compressed
- **Accuracy**: > 90% relevant retrieval

## Security & Privacy

- **PII Detection**: Automatic filtering of sensitive data
- **User Isolation**: Strict user-based access control
- **Data Retention**: Configurable memory expiration
- **Encryption**: At-rest and in-transit protection
