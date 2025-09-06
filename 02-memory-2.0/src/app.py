#!/usr/bin/env python3
"""
Memory 2.0 service for the OpenWebUI Suite

Provides persistent memory with two storage layers:
1. Traits: Key-value storage in SQLite for user characteristics
2. Episodes: Semantic memory in SQLite for conversation events

Memory Write Policy:
- Filter out PII before storing
- Only store high-confidence memories (>0.7 confidence)
- Summarize memories to ≤200 tokens

API Endpoints:
- POST /mem/candidates - Identify memory candidates from conversation
- GET /mem/retrieve - Retrieve memories based on query/context
- GET /mem/summary - Get memory summary for user
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import sqlite3
import json
import re
import hashlib
import time
from datetime import datetime, timezone
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Memory 2.0",
    description="Persistent memory service with traits and episodes",
    version="1.0.0"
)


@app.get("/healthz")
async def healthz():
    return {"ok": True, "service": "memory-2.0"}

# Database initialization
def init_database():
    """Initialize SQLite database for memory storage"""
    conn = sqlite3.connect('memory.db')
    cursor = conn.cursor()
    
    # Create traits table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS traits (
            user_id TEXT,
            key TEXT,
            value TEXT,
            confidence REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, key)
        )
    ''')
    
    # Create episodes table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS episodes (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            content TEXT,
            summary TEXT,
            confidence REAL,
            tags TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("Database initialized")

# Initialize on startup
init_database()

# Models
class MemoryCandidate(BaseModel):
    content: str = Field(..., description="Content to analyze")
    user_id: str = Field(..., description="User identifier")
    context: Optional[Dict[str, Any]] = Field(default=None)

class MemorySummary(BaseModel):
    user_id: str
    trait_count: int
    episode_count: int
    recent_traits: List[Dict[str, Any]]
    recent_episodes: List[Dict[str, Any]]
    summary: str

# Utility functions
def detect_pii(text: str) -> List[str]:
    """Simple PII detection"""
    pii_patterns = {
        'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
        'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
        'credit_card': r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'
    }
    
    detected = []
    for pii_type, pattern in pii_patterns.items():
        if re.search(pattern, text):
            detected.append(pii_type)
    
    return detected

def filter_pii(text: str) -> str:
    """Remove PII from text"""
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', text)
    text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]', text)
    text = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]', text)
    text = re.sub(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', '[CREDIT_CARD]', text)
    return text

def extract_traits(content: str) -> List[Dict[str, Any]]:
    """Extract trait candidates from content"""
    traits = []
    
    trait_patterns = [
        (r"(?:I am|I'm)\s+(\w+)", "personality", 0.7),
        (r"I (?:like|love|enjoy)\s+([^.!?]+)", "preference", 0.6),
        (r"I (?:work|am employed)\s+(?:as|at)\s+([^.!?]+)", "occupation", 0.8),
        (r"I live in\s+([^.!?]+)", "location", 0.8),
        (r"My (?:name is|name's)\s+(\w+)", "name", 0.9),
        (r"I (?:hate|dislike|don't like)\s+([^.!?]+)", "dislike", 0.6),
    ]
    
    for pattern, trait_type, confidence in trait_patterns:
        matches = re.finditer(pattern, content, re.IGNORECASE)
        for match in matches:
            value = match.group(1).strip()
            if len(value) > 0:
                traits.append({
                    "key": trait_type,
                    "value": value,
                    "confidence": confidence
                })
    
    return traits

def summarize_content(content: str, max_tokens: int = 200) -> str:
    """Simple summarization by truncating and keeping key sentences"""
    sentences = re.split(r'[.!?]+', content)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
    
    current_length = 0
    result_sentences = []
    
    for sentence in sentences:
        estimated_tokens = len(sentence) // 4
        if current_length + estimated_tokens <= max_tokens:
            result_sentences.append(sentence)
            current_length += estimated_tokens
        else:
            break
    
    summary = '. '.join(result_sentences)
    if len(summary) > 0 and not summary.endswith('.'):
        summary += '.'
    
    return summary or content[:max_tokens * 4]

def generate_episode_id(user_id: str, content: str) -> str:
    """Generate unique episode ID"""
    content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
    timestamp = int(datetime.now(timezone.utc).timestamp())
    return f"{user_id}_{timestamp}_{content_hash}"

# Database operations
def store_trait(user_id: str, key: str, value: str, confidence: float):
    """Store or update a trait in the database"""
    conn = sqlite3.connect('memory.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR REPLACE INTO traits (user_id, key, value, confidence, updated_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, key, value, confidence, datetime.now(timezone.utc).isoformat()))
    
    conn.commit()
    conn.close()

def store_episode(user_id: str, content: str, summary: str, confidence: float, tags: List[str] = None) -> str:
    """Store an episode in the database"""
    episode_id = generate_episode_id(user_id, content)
    tags_json = json.dumps(tags or [])
    
    conn = sqlite3.connect('memory.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO episodes (id, user_id, content, summary, confidence, tags)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (episode_id, user_id, content, summary, confidence, tags_json))
    
    conn.commit()
    conn.close()
    
    return episode_id

def get_traits(user_id: str, min_confidence: float = 0.0) -> List[Dict[str, Any]]:
    """Retrieve traits for a user"""
    conn = sqlite3.connect('memory.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT key, value, confidence, created_at, updated_at
        FROM traits
        WHERE user_id = ? AND confidence >= ?
        ORDER BY updated_at DESC
    ''', (user_id, min_confidence))
    
    results = []
    for row in cursor.fetchall():
        results.append({
            "key": row[0],
            "value": row[1],
            "confidence": row[2],
            "created_at": row[3],
            "updated_at": row[4]
        })
    
    conn.close()
    return results

def get_episodes(user_id: str, min_confidence: float = 0.0, limit: int = 10) -> List[Dict[str, Any]]:
    """Retrieve episodes for a user"""
    conn = sqlite3.connect('memory.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, content, summary, confidence, tags, created_at
        FROM episodes
        WHERE user_id = ? AND confidence >= ?
        ORDER BY created_at DESC
        LIMIT ?
    ''', (user_id, min_confidence, limit))
    
    results = []
    for row in cursor.fetchall():
        results.append({
            "id": row[0],
            "content": row[1],
            "summary": row[2],
            "confidence": row[3],
            "tags": json.loads(row[4]),
            "created_at": row[5]
        })
    
    conn.close()
    return results

def search_episodes(user_id: str, query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Simple text search in episodes"""
    conn = sqlite3.connect('memory.db')
    cursor = conn.cursor()
    
    search_term = f"%{query}%"
    cursor.execute('''
        SELECT id, content, summary, confidence, tags, created_at
        FROM episodes
        WHERE user_id = ? AND (content LIKE ? OR summary LIKE ?)
        ORDER BY created_at DESC
        LIMIT ?
    ''', (user_id, search_term, search_term, limit))
    
    results = []
    for row in cursor.fetchall():
        results.append({
            "id": row[0],
            "content": row[1],
            "summary": row[2],
            "confidence": row[3],
            "tags": json.loads(row[4]),
            "created_at": row[5]
        })
    
    conn.close()
    return results

# API Endpoints
@app.get("/")
async def root():
    """Root endpoint with service info"""
    return {
        "service": "Memory 2.0",
        "version": "1.0.0",
        "description": "Persistent memory system with traits and episodes",
        "endpoints": {
            "store": "/mem/candidates",
            "retrieve": "/mem/retrieve",
            "summary": "/mem/summary",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        conn = sqlite3.connect('memory.db')
        cursor = conn.cursor()
        cursor.execute('SELECT 1')
        conn.close()
        
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "version": "1.0.0",
            "database": "connected"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": time.time(),
            "error": str(e)
        }

@app.post("/mem/candidates")
async def store_memory_candidate(candidate: MemoryCandidate):
    """Store a memory candidate after applying write policies"""
    try:
        content = candidate.content
        user_id = candidate.user_id
        
        # Check for PII
        pii_detected = detect_pii(content)
        if pii_detected:
            content = filter_pii(content)
            logger.info(f"Filtered PII types: {pii_detected}")
        
        # Extract traits
        traits = extract_traits(content)
        stored_traits = 0
        
        for trait in traits:
            if trait["confidence"] >= 0.7:  # High confidence threshold
                store_trait(user_id, trait["key"], trait["value"], trait["confidence"])
                stored_traits += 1
        
        # Store as episode if content is substantial
        episode_created = False
        if len(content.strip()) > 20:  # Minimum content length
            summary = summarize_content(content)
            episode_confidence = 0.8  # Default episode confidence
            
            if episode_confidence >= 0.7:
                store_episode(user_id, content, summary, episode_confidence)
                episode_created = True
        
        return {
            "success": True,
            "stored": stored_traits > 0 or episode_created,
            "traits_extracted": stored_traits,
            "episode_created": episode_created,
            "pii_filtered": len(pii_detected) > 0,
            "pii_types": pii_detected
        }
        
    except Exception as e:
        logger.error(f"Error storing memory candidate: {e}")
        raise HTTPException(status_code=500, detail=f"Storage failed: {str(e)}")

@app.get("/mem/retrieve")
async def retrieve_memories(
    user_id: str,
    query: str = None,
    limit: int = 10,
    min_confidence: float = 0.5
):
    """Retrieve relevant memories based on user ID and optional query"""
    try:
        # Get traits
        traits = get_traits(user_id, min_confidence)
        
        # Get episodes
        if query:
            episodes = search_episodes(user_id, query, limit)
        else:
            episodes = get_episodes(user_id, min_confidence, limit)
        
        return {
            "user_id": user_id,
            "traits": traits[:limit],
            "episodes": episodes[:limit],
            "total_traits": len(traits),
            "total_episodes": len(episodes)
        }
        
    except Exception as e:
        logger.error(f"Error retrieving memories: {e}")
        raise HTTPException(status_code=500, detail=f"Retrieval failed: {str(e)}")

@app.get("/mem/summary", response_model=MemorySummary)
async def get_memory_summary(user_id: str):
    """Generate a compact memory summary (≤200 tokens)"""
    try:
        # Get recent traits and episodes
        traits = get_traits(user_id, 0.7)[:5]  # Top 5 high-confidence traits
        episodes = get_episodes(user_id, 0.7, 3)  # Top 3 recent episodes
        
        # Generate summary
        summary_parts = []
        
        if traits:
            trait_summary = "Key traits: " + ", ".join([f"{t['key']}: {t['value']}" for t in traits[:3]])
            summary_parts.append(trait_summary)
        
        if episodes:
            episode_summary = "Recent context: " + ". ".join([e['summary'] for e in episodes[:2]])
            summary_parts.append(episode_summary)
        
        summary = ". ".join(summary_parts)
        
        # Ensure summary is ≤200 tokens (rough estimate)
        if len(summary) > 800:  # ~200 tokens * 4 chars/token
            summary = summary[:800] + "..."
        
        return MemorySummary(
            user_id=user_id,
            trait_count=len(traits),
            episode_count=len(episodes),
            recent_traits=traits,
            recent_episodes=episodes,
            summary=summary
        )
        
    except Exception as e:
        logger.error(f"Error generating memory summary: {e}")
        raise HTTPException(status_code=500, detail=f"Summary generation failed: {str(e)}")

@app.delete("/mem/user/{user_id}")
async def delete_user_memories(user_id: str):
    """Delete all memories for a specific user"""
    try:
        conn = sqlite3.connect('memory.db')
        cursor = conn.cursor()
        
        # Count before deletion
        cursor.execute('SELECT COUNT(*) FROM traits WHERE user_id = ?', (user_id,))
        trait_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM episodes WHERE user_id = ?', (user_id,))
        episode_count = cursor.fetchone()[0]
        
        # Delete
        cursor.execute('DELETE FROM traits WHERE user_id = ?', (user_id,))
        cursor.execute('DELETE FROM episodes WHERE user_id = ?', (user_id,))
        
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "deleted_traits": trait_count,
            "deleted_episodes": episode_count,
            "user_id": user_id
        }
        
    except Exception as e:
        logger.error(f"Error deleting user memories: {e}")
        raise HTTPException(status_code=500, detail=f"Deletion failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8102)
