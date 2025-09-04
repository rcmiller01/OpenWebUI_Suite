# Drive State Service

## Overview
The Drive State service simulates user mood and needs with 5 core drives that evolve over time through bounded random walk and event reactions. Drives decay slowly toward baseline values while responding to external events.

## Architecture
- **Port**: 8105
- **Framework**: FastAPI with JSON persistence
- **Drives**: energy, sociability, curiosity, empathy_reserve, novelty_seek ∈ [0..1]
- **Simulation**: Bounded random walk with time-based decay to baseline (0.5)

## Core Drives

### Energy [0..1]
- Physical and mental energy level
- High: Detailed, energetic responses
- Low: Brief, focused responses

### Sociability [0..1]
- Desire for social interaction
- High: Friendly, conversational elements
- Low: Minimize social chit-chat

### Curiosity [0..1]
- Interest in learning and exploration
- High: Include facts and connections
- Low: Stick to practical information

### Empathy Reserve [0..1]
- Capacity for emotional support
- High: Show understanding and awareness
- Low: Focus on solutions over emotion

### Novelty Seek [0..1]
- Desire for new experiences
- High: Introduce novel ideas
- Low: Use familiar approaches

## API Endpoints

### GET /drive/get?user_id={id}
Get current drive state for user.

**Response:**
```json
{
  "user_id": "user123",
  "energy": 0.65,
  "sociability": 0.42,
  "curiosity": 0.78,
  "empathy_reserve": 0.31,
  "novelty_seek": 0.59,
  "timestamp": 1703123456.789
}
```

### POST /drive/update
Update drive state with deltas.

**Request:**
```json
{
  "delta": {
    "energy": 0.1,
    "sociability": -0.05
  },
  "reason": "Completed challenging task"
}
```

**Response:** Updated drive state (same format as GET)

### POST /drive/policy?user_id={id}
Get style policy based on current drive state.

**Response:**
```json
{
  "energy_level": "moderate",
  "social_style": "low",
  "curiosity_level": "high",
  "empathy_approach": "low",
  "novelty_preference": "moderate",
  "style_hints": [
    "Keep responses brief and focused",
    "Include interesting facts and connections",
    "Focus on solutions over emotional support"
  ]
}
```

### GET /drive/history?user_id={id}&limit={n}
Get drive state history (currently returns current state).

## Simulation Mechanics

### Bounded Random Walk
- Small random changes (±0.02) applied periodically
- Values clamped to [0..1] range
- Creates natural variation over time

### Time-Based Decay
- Slow decay toward baseline (0.5) when inactive
- Decay rate: 0.001 per second
- Prevents drives from getting stuck at extremes

### Event Reactions
- External events can modify drives via API
- Changes are immediate but subject to clamping
- Decay continues to pull toward baseline

## Storage
Drive states are persisted in `drive_states.json`:
```json
{
  "user123": {
    "user_id": "user123",
    "energy": 0.65,
    "sociability": 0.42,
    "curiosity": 0.78,
    "empathy_reserve": 0.31,
    "novelty_seek": 0.59,
    "timestamp": 1703123456.789
  }
}
```

## Usage Examples

### Basic State Retrieval
```python
import requests

response = requests.get("http://localhost:8105/drive/get?user_id=user123")
state = response.json()
print(f"Energy level: {state['energy']}")
```

### Event-Driven Updates
```python
# User completed a long coding session
requests.post("http://localhost:8105/drive/update?user_id=user123", json={
    "delta": {"energy": -0.2, "sociability": -0.1},
    "reason": "Long coding session completed"
})

# User expressed sadness
requests.post("http://localhost:8105/drive/update?user_id=user123", json={
    "delta": {"empathy_reserve": 0.3},
    "reason": "User expressed sadness"
})
```

### Style Policy Integration
```python
policy = requests.post("http://localhost:8105/drive/policy?user_id=user123").json()
style_hints = policy['style_hints']
# Use hints to adjust response style
```

## Test Scenarios

### Long Tech Session
- **Effect**: ↓ sociability (user becomes less social after focused work)
- **Implementation**: Multiple small negative deltas to sociability

### User Sadness Event
- **Effect**: ↑ empathy_reserve (AI becomes more emotionally supportive)
- **Implementation**: Positive delta to empathy_reserve

## Development

### Running the Service
```bash
cd 05-drive-state
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
- **Feeling Engine** (port 8103) - Can use affect analysis to update drives
- **Intent Router** (port 8101) - Can route based on drive state
- **Memory 2.0** (port 8102) - Can store drive-aware interactions
- **Pipelines Gateway** (port 8088) - Can incorporate drive state in responses
