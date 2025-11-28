# Gateway UI (gateway-ui)

This is a minimal FastAPI-based UI that proxies to the secured Bifrost Gateway API.

Environment

- `BIFROST_API_BASE_URL` - base URL of the gateway API (default: `http://127.0.0.1:8000`)
- `BIFROST_UI_TOKEN` - API token used by the UI when calling the secured API (required)

Run (development)

```bash
export BIFROST_API_BASE_URL=http://127.0.0.1:8000
export BIFROST_UI_TOKEN=your_api_token_here
uvicorn bifrost_ui.app:app --reload --port 8080
```

Systemd example

Create `/etc/systemd/system/gateway-ui.service` with the following content and set env vars in a drop-in file or systemd environment file.

```
[Unit]
Description=Bifrost Gateway UI
After=network.target

[Service]
User=root
WorkingDirectory=/opt/bifrost/gateway-ui
Environment=BIFROST_API_BASE_URL=http://127.0.0.1:8000
Environment=BIFROST_UI_TOKEN=your_api_token_here
ExecStart=/usr/bin/uvicorn bifrost_ui.app:app --host 0.0.0.0 --port 8080
Restart=always

[Install]
WantedBy=multi-user.target
```
