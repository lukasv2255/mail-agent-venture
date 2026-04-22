"""
Týdenní test agenta — posílá ~100 emailů, monitoruje uptime, generuje report.

Spuštění:
  python3 tests/responder/projekt_01/run_week.py           # 7 dní, ~100 emailů
  python3 tests/responder/projekt_01/run_week.py --fast    # 30 minut, ~20 emailů
  python3 tests/responder/projekt_01/run_week.py --report  # jen report z existujících logů

Loguje:
  logs/responder/week_sent.jsonl   — každý odeslaný email
  logs/responder/uptime.jsonl      — start/stop/crash agenta

Na konci vypíše report do terminálu a uloží do logs/responder/week_report.txt
"""
import argparse
import asyncio
import base64
import json
import os
import random
import signal
import sys
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.config import LOG_DIR as ROOT_LOG_DIR
from src.gmail_client import get_gmail_service

TARGET = os.getenv("TEST_TARGET_EMAIL", os.getenv("GMAIL_ADDRESS", ""))
DASHBOARD_URL = "http://localhost:8081/api/status"
LOG_DIR = ROOT_LOG_DIR / "responder"
SENT_LOG = LOG_DIR / "week_sent.jsonl"
UPTIME_LOG = LOG_DIR / "uptime.jsonl"
REPORT_FILE = LOG_DIR / "week_report.txt"

# ── Šablony emailů — Projekt 01 (E-shop s doplňky stravy) ───────────────────
# Reálná data z KB: objednávky 4471, 2280, 9993, 1102, 3357, 7780
# Produkty: Whey Protein Vanilka/Čokoláda, Kreatin, BCAA, Multivitamín Sport

TEMPLATES = [
    # Objednávky — reálná čísla z KB
    {"id": "ORD-01", "type": "ORDER",
     "subject": "Dotaz na objednávku 4471",
     "body": "Dobrý den,\nchtěl bych se zeptat, kdy dorazí moje objednávka číslo 4471.\nDěkuji, Jan Novák"},
    {"id": "ORD-02", "type": "ORDER",
     "subject": "Kde je moje zásilka - obj. 2280",
     "body": "Dobrý den,\nobjednala jsem kreatin, objednávka č. 2280. Ještě jsem nedostala žádnou informaci o odeslání.\nEva Kovářová"},
    {"id": "ORD-03", "type": "ORDER",
     "subject": "Objednávka 9993 — kdy dorazí?",
     "body": "Dobrý den,\nzajímá mě stav mé objednávky č. 9993 (Multivitamín Sport). Sledovací číslo zásilky mi nefunguje.\nPetr Svoboda"},
    {"id": "ORD-04", "type": "ORDER",
     "subject": "Stav objednávky 1102",
     "body": "Dobrý den,\nchtěla bych vědět, kde je moje objednávka 1102 (BCAA). Tracking číslo pořád ukazuje 'v přepravě'.\nJana Nováková"},
    {"id": "ORD-05", "type": "ORDER",
     "subject": "Objednávka 3357 — storno?",
     "body": "Dobrý den,\nv systému vidím u objednávky 3357 stav 'stornováno', ale já nic nestornoval. Co se stalo?\nMartin Kříž"},
    {"id": "ORD-06", "type": "ORDER",
     "subject": "Objednávka 7780 — expedice?",
     "body": "Dobrý den,\nkdy bude expedována objednávka 7780? Prý do 3 dnů, ale už uplynul týden.\nLucie Horáková"},
    {"id": "ORD-07", "type": "ORDER",
     "subject": "Objednávka 9999",
     "body": "Dobrý den, kdy dorazí objednávka číslo 9999?"},

    # Produktové dotazy — konkrétní produkty z KB
    {"id": "PRD-01", "type": "PRODUCT",
     "subject": "Dotaz na protein — vegetariáni",
     "body": "Dobrý den,\nzajímá mě Whey Protein Vanilka. Kolik obsahuje bílkovin na porci a je vhodný pro vegetariány?\nDěkuji"},
    {"id": "PRD-02", "type": "PRODUCT",
     "subject": "Whey Protein Čokoláda — alergie na laktózu",
     "body": "Dobrý den,\njsem alergický na laktózu. Obsahuje váš Whey Protein Čokoláda laktózu? A je vhodný pro vegany?\nOndřej Beneš"},
    {"id": "PRD-03", "type": "PRODUCT",
     "subject": "Kreatin Monohydrát — jak dávkovat?",
     "body": "Dobrý den,\nkoupil jsem Kreatin Monohydrát 500g. Jak ho správně užívat, potřebuji loading phase nebo stačí 5g denně?\nPetr Svoboda"},
    {"id": "PRD-04", "type": "PRODUCT",
     "subject": "BCAA pro ženy — vhodné?",
     "body": "Dobrý den,\ncvičím 3x týdně, jsem žena 35 let. Má smysl užívat BCAA Aminokyseliny? V jakém množství a kdy?\nKateřina Dvořáková"},
    {"id": "PRD-05", "type": "PRODUCT",
     "subject": "Multivitamín Sport — těhotenství",
     "body": "Dobrý den,\njsem těhotná ve 2. trimestru. Je Multivitamín Sport 90 kapslí vhodný v těhotenství?\nMartina Procházková"},
    {"id": "PRD-06", "type": "PRODUCT",
     "subject": "Protein a diabetes 2. typu",
     "body": "Dobrý den,\nmám diabetes 2. typu a rád bych začal užívat váš protein. Je to bezpečné?\nJaroslav Horák"},

    # Vrácení zboží
    {"id": "RET-01", "type": "RETURN",
     "subject": "Chci vrátit zboží — obj. 4471",
     "body": "Dobrý den,\nobdržel jsem objednávku 4471 ale protein mi nechutná, chci ho vrátit. Jak mám postupovat?\nJan Novák"},
    {"id": "RET-02", "type": "RETURN",
     "subject": "Vrácení neotevřeného Kreatinu",
     "body": "Dobrý den,\nkoupil jsem Kreatin Monohydrát 500g, ale rozmyslel jsem si to. Produkt je neotevřený. Mohu ho vrátit?\nMartin Beneš"},

    # Eskalace — klíčová slova: nepřijatelné, reklamace, alergie
    {"id": "ESC-01", "type": "ESC",
     "subject": "Poškozený produkt - reklamace",
     "body": "Dobrý den,\nobjednávka 1102 dorazila s poškozeným obalem a část obsahu byla rozsypaná.\nToto je nepřijatelné, chci okamžitě náhradu nebo vrácení peněz.\nJana Nováková"},
    {"id": "ESC-02", "type": "ESC",
     "subject": "Alergie po Whey Protein Čokoláda — reklamace",
     "body": "Dobrý den,\npo konzumaci Whey Protein Čokoláda mám alergickou reakci — vyrážka a dýchací potíže. Byl jsem u lékaře.\nTrvám na okamžitém vrácení peněz a náhradě léčebných nákladů.\nMiroslav Kuba"},

    # Spam / nesouvisející
    {"id": "SPM-01", "type": "SPAM",
     "subject": "Spolupráce — nabídka reklamy",
     "body": "Dobrý den, nabízíme reklamní plochy na fitness portálech. Máte zájem o spolupráci?"},
    {"id": "SPM-02", "type": "SPAM",
     "subject": "Nabídka SEO — 1. strana Google",
     "body": "Dobrý den,\nnabízíme SEO optimalizaci pro e-shopy. Garantujeme výsledky do 30 dní.\nSEO Expres"},

    # Neznámé / automatické
    {"id": "UNK-01", "type": "UNK",
     "subject": "Automatická odpověď: dovolená",
     "body": "Jsem na dovolené do 30. dubna. Urgentní věci řeší kolega novak@firma.cz"},
    {"id": "UNK-02", "type": "UNK",
     "subject": "Newsletter: Fitness novinky duben",
     "body": "Přinášíme přehled novinek z fitness oboru za duben 2026.\nRedakce FitNews.cz"},
]

# ── Pravděpodobnostní váhy pro výběr šablony ────────────────────────────────
# Více ORDER/PRODUCT než ESC/SPAM — realističtější mix
WEIGHTS = {
    "ORDER": 30, "PRODUCT": 25, "RETURN": 15,
    "ESC": 10, "SPAM": 10, "UNK": 10,
}
_weighted_templates = []
for t in TEMPLATES:
    _weighted_templates.extend([t] * WEIGHTS.get(t["type"], 10))


# ── Logování ─────────────────────────────────────────────────────────────────

def log_event(log_file: Path, record: dict):
    log_file.parent.mkdir(parents=True, exist_ok=True)
    record["time"] = datetime.now(timezone.utc).isoformat()
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def read_log(log_file: Path) -> list:
    if not log_file.exists():
        return []
    records = []
    for line in log_file.read_text(encoding="utf-8").splitlines():
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return records


# ── Odesílání emailů ─────────────────────────────────────────────────────────

def send_email(service, template: dict, seq: int) -> dict:
    num = random.randint(1000, 9999)
    subject = template["subject"].replace("{num}", str(num))
    body = template["body"].replace("{num}", str(num))
    subject = f"[{template['id']}-{seq:03d}] {subject}"

    msg = EmailMessage()
    msg["To"] = TARGET
    msg["Subject"] = subject
    msg.set_content(body)
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    service.users().messages().send(userId="me", body={"raw": raw}).execute()

    record = {"event": "sent", "seq": seq, "id": template["id"],
              "type": template["type"], "subject": subject}
    log_event(SENT_LOG, record)
    return record


# ── Monitoring agenta ─────────────────────────────────────────────────────────

_agent_was_up = None  # None = unknown, True = up, False = down


async def check_agent_health() -> bool:
    try:
        import urllib.request
        urllib.request.urlopen(DASHBOARD_URL, timeout=5)
        return True
    except Exception:
        return False


async def monitor_loop(stop_event: asyncio.Event):
    global _agent_was_up
    while not stop_event.is_set():
        up = await check_agent_health()
        if _agent_was_up is None:
            _agent_was_up = up
            log_event(UPTIME_LOG, {"event": "monitor_start", "agent_up": up})
        elif up and not _agent_was_up:
            log_event(UPTIME_LOG, {"event": "recovery"})
            print(f"  ✅ [{_now()}] Agent se zotavil")
            _agent_was_up = True
        elif not up and _agent_was_up:
            log_event(UPTIME_LOG, {"event": "crash_detected"})
            print(f"  💥 [{_now()}] Agent nedostupný!")
            _agent_was_up = False
        await asyncio.sleep(60)


# ── Plánovač emailů ───────────────────────────────────────────────────────────

async def scheduler_loop(service, total_emails: int, duration_seconds: int,
                         stop_event: asyncio.Event):
    """Odešle total_emails rovnoměrně rozložených přes duration_seconds."""
    sent = 0
    # Interval mezi emaily s ±50% jitter
    base_interval = duration_seconds / total_emails

    while sent < total_emails and not stop_event.is_set():
        jitter = random.uniform(0.5, 1.5)
        wait = base_interval * jitter
        await asyncio.sleep(wait)

        if stop_event.is_set():
            break

        template = random.choice(_weighted_templates)
        try:
            record = send_email(service, template, sent + 1)
            print(f"  ✉  [{_now()}] #{sent+1:03d} {record['subject'][:60]}")
        except Exception as e:
            print(f"  ⚠  [{_now()}] Chyba při odesílání: {e}")
            log_event(SENT_LOG, {"event": "send_error", "error": str(e)})

        sent += 1

    print(f"\n  Scheduler hotov — odesláno {sent} emailů.")
    stop_event.set()


# ── Report ────────────────────────────────────────────────────────────────────

def generate_report() -> str:
    sent = read_log(SENT_LOG)
    uptime = read_log(UPTIME_LOG)
    responses = read_log(LOG_DIR / "responses.jsonl")

    total_sent = sum(1 for e in sent if e.get("event") == "sent")
    send_errors = sum(1 for e in sent if e.get("event") == "send_error")
    crashes = sum(1 for e in uptime if e.get("event") == "crash_detected")
    recoveries = sum(1 for e in uptime if e.get("event") == "recovery")

    # Uptime výpočet
    monitor_start = next((e for e in uptime if e.get("event") == "monitor_start"), None)
    last_event = uptime[-1] if uptime else None
    total_seconds = 0
    down_seconds = 0
    if monitor_start and last_event:
        t_start = datetime.fromisoformat(monitor_start["time"])
        t_end = datetime.fromisoformat(last_event["time"])
        total_seconds = (t_end - t_start).total_seconds()

        # Spočítej čas "down"
        down_start = None
        for e in uptime:
            if e.get("event") == "crash_detected":
                down_start = datetime.fromisoformat(e["time"])
            elif e.get("event") == "recovery" and down_start:
                down_seconds += (datetime.fromisoformat(e["time"]) - down_start).total_seconds()
                down_start = None
        if down_start:  # ještě pořád down
            down_seconds += (datetime.fromisoformat(last_event["time"]) - down_start).total_seconds()

    uptime_pct = ((total_seconds - down_seconds) / total_seconds * 100) if total_seconds > 0 else 0

    # Response outcomes
    outcomes: dict = {}
    for r in responses:
        k = r.get("outcome", "?")
        outcomes[k] = outcomes.get(k, 0) + 1

    # Typ rozložení odeslaných emailů
    type_counts: dict = {}
    for e in sent:
        if e.get("event") == "sent":
            k = e.get("type", "?")
            type_counts[k] = type_counts.get(k, 0) + 1

    lines = [
        "=" * 60,
        "  STABILITY REPORT — TÝDENNÍ TEST AGENTA",
        "=" * 60,
        f"  Vygenerováno: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "── STABILITA ──────────────────────────────────────────",
        f"  Uptime:          {uptime_pct:.1f}%",
        f"  Celková délka:   {total_seconds/3600:.1f} h",
        f"  Padů detekováno: {crashes}",
        f"  Zotavení:        {recoveries}",
        "",
        "── EMAILY ─────────────────────────────────────────────",
        f"  Odesláno:        {total_sent}",
        f"  Chyby odesílání: {send_errors}",
        f"  Zpracováno:      {sum(outcomes.values())}",
        "",
        "  Rozložení odeslaných typů:",
    ]
    for k, v in sorted(type_counts.items(), key=lambda x: -x[1]):
        lines.append(f"    {k:<12} {v:>4}x")
    lines += ["", "  Výsledky zpracování:"]
    outcome_labels = {
        "approved": "Schváleno a odesláno",
        "rejected": "Zamítnuto",
        "timeout": "Timeout",
        "dry_run": "Dry run",
        "escalated": "Eskalace",
        "unknown": "Neznámý typ",
    }
    for k, v in sorted(outcomes.items(), key=lambda x: -x[1]):
        label = outcome_labels.get(k, k)
        lines.append(f"    {label:<28} {v:>4}x")

    if crashes > 0:
        lines += ["", "── PÁDY ───────────────────────────────────────────────"]
        for e in uptime:
            if e.get("event") in ("crash_detected", "recovery"):
                icon = "💥" if e["event"] == "crash_detected" else "✅"
                lines.append(f"  {icon} {e['time'][:19].replace('T', ' ')}  {e['event']}")

    lines += ["", "=" * 60]
    return "\n".join(lines)


# ── Utils ─────────────────────────────────────────────────────────────────────

def _now() -> str:
    return datetime.now().strftime("%H:%M:%S")


# ── Main ──────────────────────────────────────────────────────────────────────

async def run(total_emails: int, duration_seconds: int):
    print(f"\n🚀 Stability test spuštěn")
    print(f"   Cíl:    {total_emails} emailů za {duration_seconds // 3600:.0f}h "
          f"{(duration_seconds % 3600) // 60:.0f}min")
    print(f"   Target: {TARGET}")
    print(f"   Logy:   {SENT_LOG}, {UPTIME_LOG}")
    print(f"   Ctrl+C pro předčasné ukončení + report\n")

    log_event(UPTIME_LOG, {"event": "test_start",
                           "total_emails": total_emails,
                           "duration_seconds": duration_seconds})

    service = get_gmail_service()
    stop_event = asyncio.Event()

    def _sigint(_s, _f):
        print("\n\n  Přerušeno — generuji report...")
        stop_event.set()

    signal.signal(signal.SIGINT, _sigint)

    await asyncio.gather(
        scheduler_loop(service, total_emails, duration_seconds, stop_event),
        monitor_loop(stop_event),
    )

    log_event(UPTIME_LOG, {"event": "test_end"})

    report = generate_report()
    print("\n" + report)
    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text(report, encoding="utf-8")
    print(f"\n  Report uložen: {REPORT_FILE}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fast", action="store_true",
                        help="Rychlý test: 20 emailů za 30 minut")
    parser.add_argument("--report", action="store_true",
                        help="Jen vygeneruj report z existujících logů")
    parser.add_argument("--emails", type=int, default=100,
                        help="Počet emailů (default: 100)")
    parser.add_argument("--days", type=float, default=7.0,
                        help="Délka testu ve dnech (default: 7)")
    args = parser.parse_args()

    if args.report:
        print(generate_report())
        return

    if args.fast:
        asyncio.run(run(total_emails=20, duration_seconds=30 * 60))
    else:
        asyncio.run(run(
            total_emails=args.emails,
            duration_seconds=int(args.days * 24 * 3600),
        ))


if __name__ == "__main__":
    main()
