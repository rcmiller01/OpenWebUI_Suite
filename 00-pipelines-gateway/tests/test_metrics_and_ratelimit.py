from fastapi.testclient import TestClient
from src.server import app, _metrics  # type: ignore

client = TestClient(app)


def test_metrics_endpoint_basic():
    r = client.get('/metrics')
    assert r.status_code == 200
    body = r.text
    assert 'http_requests_total' in body
    assert body.endswith('\n')


def test_metrics_counters_increment_chat():
    before = _metrics.get('chat_completions_total', 0)
    payload = {"messages": [{"role": "user", "content": "Hi"}]}
    r = client.post('/v1/chat/completions', json=payload)
    assert r.status_code == 200
    after = _metrics.get('chat_completions_total', 0)
    assert after == before + 1


def test_rate_limit_simulated(monkeypatch):
    # Simulate rate limit: first request allowed,
    # second denied by patched limiter
    from src import server as srv  # type: ignore

    # monkeypatch the limiter to return False on second call
    calls = {"n": 0}

    async def fake_limiter(request):
        calls["n"] += 1
        return calls["n"] == 1
    monkeypatch.setattr(srv, '_rate_limiter', fake_limiter)

    payload = {"messages": [{"role": "user", "content": "Hi"}]}
    r1 = client.post('/v1/chat/completions', json=payload)
    assert r1.status_code == 200
    r2 = client.post('/v1/chat/completions', json=payload)
    assert r2.status_code == 429
    # metrics should reflect a rate limited event
    assert _metrics['rate_limited_total'] >= 1
