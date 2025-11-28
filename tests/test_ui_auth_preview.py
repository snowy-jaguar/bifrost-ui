import os
import importlib
from fastapi.testclient import TestClient


def setup_env(monkeypatch):
    monkeypatch.setenv("BIFROST_API_BASE_URL", "http://127.0.0.1:8000")
    monkeypatch.setenv("BIFROST_UI_TOKEN", "ui-token")
    monkeypatch.setenv("GATEWAY_UI_PASSWORD", "testpass")
    monkeypatch.setenv("GATEWAY_UI_SESSION_KEY", "test-session-key")


def test_login_and_dashboard(monkeypatch):
    setup_env(monkeypatch)
    # import after env set
    import bifrost_ui.app as gui
    importlib.reload(gui)

    async def fake_get(path):
        if path == "/wg/list":
            return {"configs": ["a.conf"]}
        if path == "/status/system":
            return {"active_wg": "a.conf", "uptime_seconds": 123}
        return {}

    monkeypatch.setattr(gui, "api_get", fake_get)

    client = TestClient(gui.app)

    # try accessing dashboard without login -> should be 403
    r = client.get("/")
    assert r.status_code == 403

    # login
    resp = client.post("/login", data={"password": "testpass"})
    assert resp.status_code in (200, 303)

    # now access dashboard
    r = client.get("/")
    assert r.status_code == 200
    assert "a.conf" in r.text


def test_preview_masks_private_key(monkeypatch):
    setup_env(monkeypatch)
    import bifrost_ui.app as gui
    importlib.reload(gui)

    sample = "[Interface]\nPrivateKey = ABCDEFGHIJKLMNOPQRSTUVWXYZ\nAddress = 10.0.0.1/24\n[Peer]\nPublicKey = AAAABBBBCCCC\n"

    async def fake_get(path):
        if path.startswith("/wg/get"):
            return {"name": "a.conf", "contents": sample}
        return {}

    monkeypatch.setattr(gui, "api_get", fake_get)

    client = TestClient(gui.app)
    # login
    resp = client.post("/login", data={"password": "testpass"})
    assert resp.status_code in (200, 303)

    # request preview
    resp = client.get("/api/wg/preview?name=a.conf")
    assert resp.status_code == 200
    j = resp.json()
    assert "head" in j
    assert "PrivateKey" in j["head"]
    assert "*****" in j["head"] or "*****" in j["tail"]
