"""
Web dashboard — schvalování emailů přes prohlížeč.

Běží jako FastAPI server ve vedlejším vlákně vedle Telegram bota.
Přístup: http://localhost:8080

Env proměnné:
  DASHBOARD_PORT   (default: 8080)
  DASHBOARD_TOKEN  (volitelné heslo pro přístup)
"""
import asyncio
import logging
import os
import threading

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse

from src.notifier import get_pending_item, get_queue_remaining, resolve_approval, get_alerts, clear_alert, get_unpin_callback

logger = logging.getLogger(__name__)

app = FastAPI()

DASHBOARD_TOKEN = os.getenv("DASHBOARD_TOKEN", "")
MAIL_CLIENT = os.getenv("MAIL_CLIENT", "gmail")
DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"

# Callback nastavený z main.py — spustí run_check
_check_callback = None


def set_check_callback(fn):
    global _check_callback
    _check_callback = fn


def _check_token(request: Request):
    """Jednoduchá ochrana tokenem — volitelná."""
    if not DASHBOARD_TOKEN:
        return
    token = request.query_params.get("token") or request.headers.get("X-Token")
    if token != DASHBOARD_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    _check_token(request)
    return HTMLResponse(content=open("templates/dashboard.html", encoding="utf-8").read())


@app.get("/api/status")
def api_status(request: Request):
    _check_token(request)
    item = get_pending_item()
    return {
        "mail_client": MAIL_CLIENT,
        "dry_run": DRY_RUN,
        "queue_remaining": get_queue_remaining(),
        "alerts": get_alerts(),
        "pending": {
            "from": item["email"]["from"],
            "subject": item["email"]["subject"],
            "body": item["email"]["body"][:500],
            "email_type": item["email_type"],
            "draft": item["draft"],
        } if item else None,
    }


@app.post("/api/check")
async def api_check(request: Request):
    _check_token(request)
    if _check_callback is None:
        raise HTTPException(status_code=503, detail="Agent není připraven.")
    asyncio.create_task(_check_callback())
    return {"ok": True}


@app.post("/api/alert/dismiss/{index}")
async def api_dismiss_alert(index: int, request: Request):
    _check_token(request)
    alerts = get_alerts()
    if 0 <= index < len(alerts):
        msg_id = alerts[index].get("message_id")
        clear_alert(index)
        if msg_id:
            unpin = get_unpin_callback()
            if unpin:
                await unpin(msg_id)
    return {"ok": True}


@app.post("/api/approve")
async def api_approve(request: Request):
    _check_token(request)
    item = get_pending_item()
    if not item:
        raise HTTPException(status_code=404, detail="Žádný email nečeká na schválení.")
    await resolve_approval(True)
    return {"ok": True, "action": "approved"}


@app.post("/api/reject")
async def api_reject(request: Request):
    _check_token(request)
    item = get_pending_item()
    if not item:
        raise HTTPException(status_code=404, detail="Žádný email nečeká na schválení.")
    await resolve_approval(False)
    return {"ok": True, "action": "rejected"}


def start_dashboard():
    """Spustí dashboard server ve vedlejším vlákně."""
    port = int(os.getenv("DASHBOARD_PORT", "8080"))
    config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="warning")
    server = uvicorn.Server(config)

    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    logger.info(f"Dashboard spuštěn na http://localhost:{port}")
