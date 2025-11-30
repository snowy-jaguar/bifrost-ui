# Bifrost Gateway UI

Web interface for the Bifrost Gateway API with session-based authentication, config preview, and GetHomepage integration.

> **Note:** This repo is part of the [bifrost-gateway](https://github.com/snowy-jaguar/bifrost-gateway) monorepo.

## Features

- Server-side API token proxy (token never exposed to browser)
- Session-based login with password authentication
- WireGuard config management dashboard
- Config preview with private key masking
- GetHomepage custom API endpoint (`/homepage/custom`)
- Upload, activate, delete WireGuard configs

## Quick Start

### Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### Run (development)

```bash
export BIFROST_API_BASE_URL=http://127.0.0.1:8000
export BIFROST_UI_TOKEN=your_api_token_here
export GATEWAY_UI_PASSWORD=your_ui_password
export GATEWAY_UI_SESSION_KEY=your_session_secret_key
uvicorn bifrost_ui.app:app --reload --port 8080
```

Then visit http://localhost:8080 and log in with the password you set.

## Environment Variables

- `BIFROST_API_BASE_URL` - Base URL of the gateway API (default: `http://127.0.0.1:8000`)
- `BIFROST_UI_TOKEN` (required) - API token for server-side proxy calls to the API
- `GATEWAY_UI_PASSWORD` - Password for UI login (default: `changeme`)
- `GATEWAY_UI_SESSION_KEY` - Secret key for session encryption (default: `dev-session-secret`)

## Endpoints

- `GET /` - Dashboard (requires login)
- `GET /login` - Login page
- `POST /login` - Authenticate with password
- `POST /logout` - Clear session
- `GET /api/wg/preview?name=<config>` - Preview config with masked keys
- `GET /homepage/custom` - GetHomepage-compatible JSON endpoint
- Proxy endpoints: `/api/wg/list`, `/api/status`, `/api/wg/activate`, `/api/wg/delete`, `/api/wg/upload`

## Deployment

### Systemd Service

Create `/etc/systemd/system/bifrost-ui.service`:

```ini
[Unit]
Description=Bifrost Gateway UI
After=network.target

[Service]
User=bifrost
WorkingDirectory=/opt/bifrost/gateway-ui
Environment=BIFROST_API_BASE_URL=http://127.0.0.1:8000
Environment=BIFROST_UI_TOKEN=your_api_token_here
Environment=GATEWAY_UI_PASSWORD=your_secure_password
Environment=GATEWAY_UI_SESSION_KEY=your_long_random_secret
ExecStart=/usr/bin/uvicorn bifrost_ui.app:app --host 0.0.0.0 --port 8080
Restart=always

[Install]
WantedBy=multi-user.target
```

### Docker

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install -e .
CMD ["uvicorn", "bifrost_ui.app:app", "--host", "0.0.0.0", "--port", "8080"]
```

## Testing

```bash
pytest
```
