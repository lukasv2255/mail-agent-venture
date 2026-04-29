"""
Testy pro zobrazení připnutých ESC a UNK emailů v dashboardu a jejich odepnutí.

Testuje API endpointy /api/status (alerts) a /api/alert/dismiss/{index}.
Spuštění: python -m pytest tests/responder/test_dashboard_alerts.py -v
"""
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import src.notifier as notifier
from src.dashboard import app

client = TestClient(app)

ESC_EMAIL = {
    "from": "jan.novak@example.com",
    "subject": "Poškozený produkt - reklamace",
    "body": "Objednávka 1102 dorazila poškozená, chci okamžitou náhradu.",
}

UNK_EMAIL = {
    "from": "reklama@firma.cz",
    "subject": "Spolupráce — nabídka reklamy",
    "body": "Nabízíme reklamní plochy na fitness portálech.",
}


@pytest.fixture(autouse=True)
def clear_alerts():
    """Před každým testem vyprázdni seznam alertů."""
    notifier._alerts.clear()
    yield
    notifier._alerts.clear()


# ---------------------------------------------------------------------------
# Zobrazení alertů v /api/status
# ---------------------------------------------------------------------------

def test_status_no_alerts_returns_empty_list():
    resp = client.get("/api/status")
    assert resp.status_code == 200
    assert resp.json()["alerts"] == []


def test_status_shows_esc_alert():
    notifier.add_alert(ESC_EMAIL, "ESC", message_id=101)

    resp = client.get("/api/status")
    assert resp.status_code == 200
    alerts = resp.json()["alerts"]

    assert len(alerts) == 1
    assert alerts[0]["email_type"] == "ESC"
    assert alerts[0]["from"] == ESC_EMAIL["from"]
    assert alerts[0]["subject"] == ESC_EMAIL["subject"]


def test_status_shows_unk_alert():
    notifier.add_alert(UNK_EMAIL, "UNK", message_id=202)

    resp = client.get("/api/status")
    assert resp.status_code == 200
    alerts = resp.json()["alerts"]

    assert len(alerts) == 1
    assert alerts[0]["email_type"] == "UNK"
    assert alerts[0]["from"] == UNK_EMAIL["from"]


def test_status_shows_both_esc_and_unk():
    notifier.add_alert(ESC_EMAIL, "ESC", message_id=101)
    notifier.add_alert(UNK_EMAIL, "UNK", message_id=202)

    resp = client.get("/api/status")
    alerts = resp.json()["alerts"]

    assert len(alerts) == 2
    types = {a["email_type"] for a in alerts}
    assert types == {"ESC", "UNK"}


def test_status_alert_body_is_truncated_to_300_chars():
    long_email = {**ESC_EMAIL, "body": "x" * 500}
    notifier.add_alert(long_email, "ESC")

    alerts = client.get("/api/status").json()["alerts"]
    assert len(alerts[0]["body"]) <= 300


# ---------------------------------------------------------------------------
# Odepnutí alertu přes /api/alert/dismiss/{index}
# ---------------------------------------------------------------------------

def test_dismiss_removes_esc_alert():
    notifier.add_alert(ESC_EMAIL, "ESC", message_id=101)

    resp = client.post("/api/alert/dismiss/0")
    assert resp.status_code == 200
    assert resp.json()["ok"] is True

    # alert musí být pryč
    alerts = client.get("/api/status").json()["alerts"]
    assert alerts == []


def test_dismiss_removes_unk_alert():
    notifier.add_alert(UNK_EMAIL, "UNK", message_id=202)

    resp = client.post("/api/alert/dismiss/0")
    assert resp.status_code == 200

    alerts = client.get("/api/status").json()["alerts"]
    assert alerts == []


def test_dismiss_correct_index_when_multiple_alerts():
    notifier.add_alert(ESC_EMAIL, "ESC", message_id=101)
    notifier.add_alert(UNK_EMAIL, "UNK", message_id=202)

    # odepni první alert (index 0 = ESC)
    client.post("/api/alert/dismiss/0")

    alerts = client.get("/api/status").json()["alerts"]
    assert len(alerts) == 1
    assert alerts[0]["email_type"] == "UNK"


def test_dismiss_out_of_range_index_returns_ok():
    # žádné alerty — dismiss na index 99 nesmí crashnout
    resp = client.post("/api/alert/dismiss/99")
    assert resp.status_code == 200


def test_dismiss_calls_unpin_callback():
    captured = []

    async def fake_unpin(msg_id):
        captured.append(msg_id)

    notifier.set_unpin_callback(fake_unpin)
    notifier.add_alert(ESC_EMAIL, "ESC", message_id=555)

    client.post("/api/alert/dismiss/0")

    assert captured == [555]
    notifier.set_unpin_callback(None)


def test_dismiss_without_message_id_does_not_call_unpin():
    called = []

    async def fake_unpin(msg_id):
        called.append(msg_id)

    notifier.set_unpin_callback(fake_unpin)
    # message_id=None → unpin se nevolá
    notifier.add_alert(ESC_EMAIL, "ESC", message_id=None)

    client.post("/api/alert/dismiss/0")

    assert called == []
    notifier.set_unpin_callback(None)
