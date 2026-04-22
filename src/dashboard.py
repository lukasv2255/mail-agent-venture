"""
Web dashboard — schvalování emailů přes prohlížeč.

Běží jako FastAPI server ve vedlejším vlákně vedle Telegram bota.
Přístup: http://localhost:8080

Env proměnné:
  PORT             (Railway web port, má přednost)
  DASHBOARD_PORT   (lokální fallback, default: 8081)
  DASHBOARD_TOKEN  (volitelné heslo pro přístup)
"""
import asyncio
import hashlib
import json
import logging
import os
import threading
from pathlib import Path
from typing import Union

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse

from src.config import LOG_DIR, RESPONDER_HISTORY_LOG, SORTER_HISTORY_LOG, TEMPLATES_DIR
from src.notifier import get_pending_item, get_queue_remaining, resolve_approval, get_alerts, clear_alert, get_unpin_callback

logger = logging.getLogger(__name__)

app = FastAPI()

DASHBOARD_TOKEN = os.getenv("DASHBOARD_TOKEN", "")
MAIL_CLIENT = os.getenv("MAIL_CLIENT", "gmail")
DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"

# Callback nastavený z main.py — spustí run_check
_check_callback = None
_main_loop = None


def _first_existing_path(*paths: Union[Path, str]) -> Path:
    for path in paths:
        candidate = Path(path)
        if candidate.exists():
            return candidate
    return Path(paths[0])


def set_check_callback(fn):
    global _check_callback, _main_loop
    _check_callback = fn
    _main_loop = asyncio.get_running_loop()


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
    return HTMLResponse(content=(TEMPLATES_DIR / "dashboard.html").read_text(encoding="utf-8"))


@app.get("/api/status")
def api_status(request: Request):
    _check_token(request)
    item = get_pending_item()
    auto_respond = os.getenv("AUTO_RESPOND", "false").lower() == "true"
    return {
        "mail_client": MAIL_CLIENT,
        "dry_run": DRY_RUN,
        "auto_respond": auto_respond,
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
    if _main_loop is None:
        raise HTTPException(status_code=503, detail="Main loop není dostupný.")
    asyncio.run_coroutine_threadsafe(_check_callback(), _main_loop)
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


@app.get("/api/history")
def api_history(request: Request, page: int = 1, per_page: int = 50, filter: str = "all"):
    _check_token(request)
    history_file = _first_existing_path(RESPONDER_HISTORY_LOG, LOG_DIR / "responses.jsonl")
    if not history_file.exists():
        return {"items": [], "total": 0, "page": page, "per_page": per_page, "pages": 0}
    lines = history_file.read_text(encoding="utf-8").splitlines()
    items = []
    for line in lines:
        try:
            items.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    items.reverse()  # nejnovější první

    if filter == "esc":
        items = [i for i in items if i.get("outcome") == "escalated"]
    elif filter == "unk":
        items = [i for i in items if i.get("outcome") == "unknown"]
    elif filter == "auto":
        items = [i for i in items if i.get("outcome") == "auto"]
    elif filter == "resolved":
        items = [i for i in items if i.get("outcome") in ("approved", "auto")]

    total = len(items)
    pages = max(1, (total + per_page - 1) // per_page)
    page = max(1, min(page, pages))
    start = (page - 1) * per_page
    return {
        "items": items[start:start + per_page],
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": pages,
    }


def _sorter_semantic_key(item: dict) -> str:
    value = "\n".join([
        item.get("from", "").strip().lower(),
        item.get("subject", "").strip().lower(),
        item.get("body", "")[:500].strip().lower(),
    ])
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _dedupe_sorter_items(items: list[dict]) -> list[dict]:
    seen = set()
    deduped = []
    for item in items:
        key = item.get("email_key") or item.get("message_id") or item.get("semantic_key")
        if not key:
            key = _sorter_semantic_key(item)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


@app.get("/api/sorter-history")
def api_sorter_history(request: Request, page: int = 1, per_page: int = 50, filter: str = "all"):
    _check_token(request)
    history_file = _first_existing_path(SORTER_HISTORY_LOG, LOG_DIR / "sorter.jsonl")
    if not history_file.exists():
        return {"items": [], "total": 0, "page": page, "per_page": per_page, "pages": 0}
    lines = history_file.read_text(encoding="utf-8").splitlines()
    items = []
    for line in lines:
        try:
            items.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    items.reverse()
    items = _dedupe_sorter_items(items)

    if filter == "kept":
        items = [i for i in items if i.get("outcome") == "kept"]
    elif filter == "moved":
        items = [i for i in items if i.get("outcome") == "moved"]
    elif filter == "ai":
        items = [i for i in items if i.get("method") == "ai"]

    total = len(items)
    pages = max(1, (total + per_page - 1) // per_page)
    page = max(1, min(page, pages))
    start = (page - 1) * per_page
    return {
        "items": items[start:start + per_page],
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": pages,
    }


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
    port = int(os.getenv("PORT") or os.getenv("DASHBOARD_PORT", "8081"))
    config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="warning")
    server = uvicorn.Server(config)

    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    logger.info(f"Dashboard spuštěn na http://localhost:{port}")
