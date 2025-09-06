from fastapi.testclient import TestClient
from src.server import app

client = TestClient(app)


def test_health():
    r = client.get('/health')
    assert r.status_code == 200
    j = r.json()
    assert 'service' in j and j['service'] == 'pipelines-gateway'


def test_chat_minimal():
    body = {
        "messages": [
            {"role": "user", "content": "Hello there"}
        ],
        "user": "test"
    }
    r = client.post('/v1/chat/completions', json=body)
    assert r.status_code == 200
    j = r.json()
    assert 'choices' in j
    assert j['choices'][0]['message']['role'] == 'assistant'


def test_streaming_endpoint():
    body = {
        "messages": [
            {"role": "user", "content": "Stream please"}
        ]
    }
    r = client.post('/v1/chat/completions/stream', json=body)
    # For now just check endpoint returns 200
    assert r.status_code == 200
