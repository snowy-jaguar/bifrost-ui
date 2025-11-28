from __future__ import annotations

import os
import logging
from typing import Any

from fastapi import FastAPI, Request, HTTPException, Form, UploadFile, File, Depends
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
import httpx

logger = logging.getLogger("bifrost_ui")

BASE_URL = os.environ.get("BIFROST_API_BASE_URL", "http://127.0.0.1:8000")
UI_TOKEN = os.environ.get("BIFROST_UI_TOKEN")
if not UI_TOKEN:
    raise RuntimeError("BIFROST_UI_TOKEN is required for gateway-ui to talk to the API")
UI_PASSWORD = os.environ.get("GATEWAY_UI_PASSWORD", "changeme")
SESSION_KEY = os.environ.get("GATEWAY_UI_SESSION_KEY", "dev-session-secret")

app = FastAPI(title="Bifrost Gateway UI")
app.add_middleware(SessionMiddleware, secret_key=SESSION_KEY)
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

client = httpx.AsyncClient(timeout=10.0)


async def api_get(path: str) -> Any:
    url = BASE_URL.rstrip("/") + path
    headers = {"Authorization": f"Bearer {UI_TOKEN}"}
    resp = await client.get(url, headers=headers)
    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()


async def api_post(path: str, json: dict) -> Any:
    url = BASE_URL.rstrip("/") + path
    headers = {"Authorization": f"Bearer {UI_TOKEN}"}
    resp = await client.post(url, headers=headers, json=json)
    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    try:
        return resp.json()
    except Exception:
        return {"ok": True}


def require_login(request: Request):
    if not request.session.get("auth"):
        raise HTTPException(status_code=403, detail="Authentication required")


def mask_private_keys(contents: str) -> str:
    """Mask private keys in a WireGuard config for safe preview.

    Replaces values on lines starting with 'PrivateKey' with '*****...'.
    """
    out = []
    for line in contents.splitlines():
        if line.strip().startswith("PrivateKey"):
            parts = line.split("=", 1)
            if len(parts) == 2:
                out.append(parts[0] + "= *****")
                continue
        out.append(line)
    return "\n".join(out)


@app.get("/", response_class=HTMLResponse, dependencies=[Depends(require_login)])
async def dashboard(request: Request):
    # fetch list & active via API
    configs = []
    active = None
    try:
        data = await api_get("/wg/list")
        configs = data.get("configs", [])
    except Exception as e:
        logger.debug("Failed to fetch configs: %s", e)
    try:
        sys = await api_get("/status/system")
        active = sys.get("active_wg")
    except Exception:
        active = None

    return templates.TemplateResponse("dashboard.html", {"request": request, "configs": configs, "active": active})


@app.get("/api/wg/list")
async def proxy_list():
    return await api_get("/wg/list")


@app.get("/api/status")
async def proxy_status():
    return await api_get("/status/system")


@app.post("/api/wg/activate")
async def proxy_activate(name: str = Form(...)):
    return await api_post("/vpn/connect", {"name": name})


@app.post("/api/wg/delete")
async def proxy_delete(name: str = Form(...)):
    return await api_post("/wg/delete", {"name": name})


@app.post("/api/wg/upload")
async def proxy_upload(file: UploadFile = File(...)):
    contents = (await file.read()).decode("utf-8")
    filename = file.filename or "uploaded.conf"
    return await api_post("/wg/upload", {"name": filename, "contents": contents})


@app.get("/homepage/custom")
async def homepage_custom():
    # Compose a minimal public JSON suitable for GetHomepage widget
    try:
        sys = await api_get("/status/system")
    except Exception:
        sys = {}
    try:
        vpn = await api_get("/status/vpn")
    except Exception:
        vpn = {"connected": False}

    return JSONResponse({
        "service": "bifrost",
        "status": "ok",
        "uptime": sys.get("uptime_seconds"),
        "vpn_connected": vpn.get("connected", False),
        "vpn_region": vpn.get("active"),
    })


@app.get("/api/wg/preview")
async def proxy_preview(name: str, auth: None = Depends(require_login)):
    """Return a sanitized preview for a WireGuard config (masked private keys)."""
    data = await api_get(f"/wg/get?name={name}")
    contents = data.get("contents", "")
    masked = mask_private_keys(contents)
    # Provide first/last 5 lines and line count
    lines = masked.splitlines()
    preview = {
        "name": data.get("name"),
        "lines": len(lines),
        "head": "\n".join(lines[:5]),
        "tail": "\n".join(lines[-5:]) if len(lines) > 5 else "",
    }
    return JSONResponse(preview)


@app.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login")
async def login(request: Request, password: str = Form(...)):
    expected = UI_PASSWORD
    if password != expected:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"}, status_code=401)
    request.session["auth"] = True
    return RedirectResponse(url='/', status_code=303)


@app.post("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url='/login', status_code=303)

*** End Patch