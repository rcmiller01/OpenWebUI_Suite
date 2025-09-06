import pytest
from fastapi.testclient import TestClient
from src.server import app


class Dummy:
    def __init__(self, resp):
        self.resp = resp

    async def get(self, path, **params):
        if isinstance(self.resp, dict):
            return self.resp.get(path, {})
        return self.resp

    async def post(self, path, payload):
        # naive branching based on path semantics
        if 'intent_router' in path or path.endswith('/classify'):
            return {"intent": "general"}
        if path.endswith('/compose'):
            return {"text": payload.get('prompt', 'merged')}
        if path.endswith('/tools/exec'):
            return {"ok": True, "result": 42}
        if path.endswith('/policy/apply'):
            return {"system_final": payload.get("system"), "validators": []}
        if path.endswith('/policy/validate'):
            return {"ok": True}
        return {"ok": True}


@pytest.fixture(autouse=True)
async def mock_services(monkeypatch):
    services = {
        'intent_router': Dummy({}),
        'memory': Dummy({
            '/mem/retrieve': {"items": []},
            '/mem/summary': {"summary": ""}
        }),
        'feeling': Dummy({}),
        'merger': Dummy({}),
        'drive': Dummy({
            '/drive/get': {},
            '/drive/policy': {"hints": {}}
        }),
        'tools': Dummy({'/tools': {"tools": []}}),
        'tandoor': Dummy({}),
        'openbb': Dummy({}),
        'multimodal': Dummy({}),
        'stt_tts': Dummy({}),
        'policy': Dummy({}),
        'telemetry': Dummy({}),
        'fastvlm': Dummy({}),
    }
    app.state.services = services
    yield


@pytest.fixture
def client():
    return TestClient(app)
