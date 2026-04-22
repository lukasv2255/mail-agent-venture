"""
Týdenní test sorteru — posílá ~100 emailů, monitoruje dashboard, generuje report.

Spuštění:
  python3 tests/sorter/projekt_01/run_week.py           # 7 dní, ~100 emailů
  python3 tests/sorter/projekt_01/run_week.py --fast    # 30 minut, ~20 emailů
  python3 tests/sorter/projekt_01/run_week.py --report  # jen report z existujících logů

Loguje:
  logs/sorter/week_sent.jsonl    — každý odeslaný email
  logs/sorter/uptime.jsonl       — dostupnost dashboardu během testu
  logs/sorter/week_report.txt    — výsledný report

Sorter samotný zapisuje rozhodnutí do:
  logs/sorter/sorter.jsonl
"""
import argparse
import asyncio
import base64
import json
import os
import random
import signal
import sys
from collections import Counter
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.config import LOG_DIR as ROOT_LOG_DIR
from src.gmail_client import get_gmail_service

TARGET = os.getenv("TEST_TARGET_EMAIL", os.getenv("GMAIL_ADDRESS", ""))
DASHBOARD_URL = "http://localhost:8081/api/status"
SORTER_HISTORY_URL = "http://localhost:8081/api/sorter-history?per_page=200&filter=all"

LOG_DIR = ROOT_LOG_DIR / "sorter"
SENT_LOG = LOG_DIR / "week_sent.jsonl"
UPTIME_LOG = LOG_DIR / "uptime.jsonl"
REPORT_FILE = LOG_DIR / "week_report.txt"
SORTER_HISTORY_LOG = LOG_DIR / "sorter.jsonl"


# ── Šablony emailů — Projekt 01 / Sorter ─────────────────────────────────────
# Expected:
#   SPAM       -> MOVE
#   INQUIRY    -> KEEP
#   NEWSLETTER -> MOVE

TEMPLATES = [
    # Spam / nerelevantní hromadné nabídky
    {"id": "SPM-01", "type": "SPAM", "expected": "MOVE",
     "subject": "Váš web potřebuje SEO — garantujeme 1. stránku Google",
     "body": "Analyzovali jsme váš web. Nabízíme SEO balíček s garancí výsledků do 30 dní. Cena od 2 900 Kč měsíčně.\n\nSEO Expres Team"},
    {"id": "SPM-02", "type": "SPAM", "expected": "MOVE",
     "subject": "Získejte 10 000 followerů na Instagramu",
     "body": "Rychlý růst sociálních sítí bez práce. Instagram, TikTok, Facebook. Výsledky do týdne nebo vrácení peněz."},
    {"id": "SPM-03", "type": "SPAM", "expected": "MOVE",
     "subject": "Vydělávejte z domova 50 000 Kč měsíčně",
     "body": "Stačí počítač a internet. Bez zkušeností, bez rizika. Registrace zdarma jen dnes."},
    {"id": "SPM-04", "type": "SPAM", "expected": "MOVE",
     "subject": "URGENTNÍ: Váš bankovní účet byl omezen",
     "body": "Z bezpečnostních důvodů byl účet omezen. Pro obnovení přístupu klikněte na odkaz a ověřte totožnost."},
    {"id": "SPM-05", "type": "SPAM", "expected": "MOVE",
     "subject": "Pronájem databáze 50 000 B2B kontaktů",
     "body": "Nabízíme segmentované B2B kontakty podle oboru a regionu. Cena od 1,50 Kč za kontakt."},
    {"id": "SPM-06", "type": "SPAM", "expected": "MOVE",
     "subject": "Máte nevyzvednutý balíček — potvrďte doručení",
     "body": "Vaši zásilku se nepodařilo doručit. Zaplaťte manipulační poplatek 49 Kč a vyberte nový termín."},

    # Osobní B2B nabídky / poptávky — relevantní, ponechat
    {"id": "INQ-01", "type": "INQUIRY", "expected": "KEEP",
     "subject": "Poptávka: IT služby pro naši firmu",
     "body": "Dobrý den,\n\njmenuji se Petra Horáčková, jednatelka BuildTech s.r.o. Hledáme dodavatele IT služeb — správu serverů a helpdesk pro 15 zaměstnanců.\n\nMohli bychom si domluvit call příští týden?\n\nPetra Horáčková\nTel: +420 603 456 789"},
    {"id": "INQ-02", "type": "INQUIRY", "expected": "KEEP",
     "subject": "Nabídka spolupráce — účetní a daňové služby",
     "body": "Dobrý den,\n\njsem Martin Novák, certifikovaný účetní. Hledám dlouhodobou spolupráci s firmami, které potřebují účetnictví, mzdy a daňové přiznání.\n\nMůžeme probrat podmínky?\n\nMartin Novák"},
    {"id": "INQ-03", "type": "INQUIRY", "expected": "KEEP",
     "subject": "Zájem o vaše služby — doporučení od Tomáše Beneše",
     "body": "Dobrý den,\n\nna vaši firmu jsem dostal doporučení. Hledáme partnera pro vývoj interního CRM systému. Máme rozpočet i specifikaci.\n\nJste k dispozici na krátkou schůzku?\n\nJakub Procházka"},
    {"id": "INQ-04", "type": "INQUIRY", "expected": "KEEP",
     "subject": "Dodávka kancelářského nábytku — cenová nabídka",
     "body": "Dobrý den,\n\nna základě vašeho inzerátu posílám cenovou nabídku na kancelářský nábytek. Umíme dodat židle, stoly a úložné systémy včetně montáže.\n\nLucie Marková"},
    {"id": "INQ-05", "type": "INQUIRY", "expected": "KEEP",
     "subject": "Poptávka: vývoj e-shopu pro náš sortiment",
     "body": "Dobrý den,\n\nprovozujeme e-shop a plánujeme přechod na novou platformu. Hledáme dodavatele pro vývoj webu na míru.\n\nMohli bychom probrat rozsah a cenu?\n\nOndřej Šimánek"},
    {"id": "INQ-06", "type": "INQUIRY", "expected": "KEEP",
     "subject": "Spolupráce na vývoji mobilní aplikace",
     "body": "Dobrý den,\n\nnarazil jsem na vaše portfolio. Chceme vyvinout mobilní aplikaci pro správu firemních objednávek. Máme wireframy a specifikaci.\n\nTomáš Beneš"},

    # Legitimní e-shop newslettery — nejsou spam, ale pro sorter MOVE
    {"id": "NWS-01", "type": "NEWSLETTER", "expected": "MOVE",
     "subject": "Alza.cz: Velký jarní výprodej — slevy až 60 %",
     "body": "Ahoj,\n\njarní výprodej právě začal. Notebooky, sluchátka a herní periferie se slevou až 60 %.\n\nTento email dostáváš, protože jsi přihlášen k odběru novinek Alza.cz.\nOdhlásit se"},
    {"id": "NWS-02", "type": "NEWSLETTER", "expected": "MOVE",
     "subject": "Mall.cz: Akční nabídky tohoto týdne",
     "body": "Dobré ráno,\n\npřinášíme ti nejlepší nabídky tohoto týdne: spotřebiče, zahradní nábytek a hračky.\n\nMall International a.s. | Odhlásit odběr newsletteru"},
    {"id": "NWS-03", "type": "NEWSLETTER", "expected": "MOVE",
     "subject": "Sportisimo: Nová kolekce + sleva 15 %",
     "body": "Ahoj,\n\nnová jarní kolekce dorazila. Jako věrný zákazník máš kód JARO15.\n\nJsi na tomto seznamu, protože jsi u nás nakoupil. Odhlásit odběr"},
    {"id": "NWS-04", "type": "NEWSLETTER", "expected": "MOVE",
     "subject": "Notino.cz: Váš oblíbený parfém je znovu skladem",
     "body": "Dobrá zpráva!\n\nProdukt z tvého wishlistu je opět dostupný. Tuto notifikaci jsi zapnul ve svém účtu. Vypnout upozornění."},
    {"id": "NWS-05", "type": "NEWSLETTER", "expected": "MOVE",
     "subject": "Heureka.cz: Produkty na watchlistu jsou levnější",
     "body": "Dobrý den,\n\ncena produktů, které sledujete, klesla. Porovnat nabídky na Heureka.cz.\n\nNotifikaci jste nastavil ve svém profilu. Vypnout."},
    {"id": "NWS-06", "type": "NEWSLETTER", "expected": "MOVE",
     "subject": "Datart: Jarní výprodej elektroniky — poslední kusy",
     "body": "Ahoj,\n\njarní výprodej se blíží ke konci. Smart TV, sluchátka a notebooky za akční ceny.\n\nDostáváš tyto emaily jako registrovaný zákazník. Odhlásit se"},
]

WEIGHTS = {
    "SPAM": 35,
    "INQUIRY": 30,
    "NEWSLETTER": 35,
}
_weighted_templates = []
for t in TEMPLATES:
    _weighted_templates.extend([t] * WEIGHTS.get(t["type"], 10))


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


def send_email(service, template: dict, seq: int) -> dict:
    subject = f"[{template['id']}-{seq:03d}] {template['subject']}"

    msg = EmailMessage()
    msg["To"] = TARGET
    msg["Subject"] = subject
    msg.set_content(template["body"])
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    service.users().messages().send(userId="me", body={"raw": raw}).execute()

    record = {
        "event": "sent",
        "seq": seq,
        "id": template["id"],
        "type": template["type"],
        "expected": template["expected"],
        "subject": subject,
    }
    log_event(SENT_LOG, record)
    return record


_agent_was_up = None


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
            print(f"  OK  [{_now()}] Agent se zotavil")
            _agent_was_up = True
        elif not up and _agent_was_up:
            log_event(UPTIME_LOG, {"event": "crash_detected"})
            print(f"  !!  [{_now()}] Agent nedostupný!")
            _agent_was_up = False
        await asyncio.sleep(60)


async def scheduler_loop(service, total_emails: int, duration_seconds: int,
                         stop_event: asyncio.Event):
    sent = 0
    base_interval = duration_seconds / total_emails

    while sent < total_emails and not stop_event.is_set():
        await asyncio.sleep(base_interval * random.uniform(0.5, 1.5))
        if stop_event.is_set():
            break

        template = random.choice(_weighted_templates)
        try:
            record = send_email(service, template, sent + 1)
            print(
                f"  ->  [{_now()}] #{sent + 1:03d} "
                f"{record['type']}/{record['expected']} {record['subject'][:60]}"
            )
        except Exception as e:
            print(f"  !!  [{_now()}] Chyba při odesílání: {e}")
            log_event(SENT_LOG, {"event": "send_error", "error": str(e)})

        sent += 1

    print(f"\n  Scheduler hotov — odesláno {sent} emailů.")
    stop_event.set()


def _strip_test_prefix(subject: str) -> str:
    if subject.startswith("[") and "] " in subject:
        return subject.split("] ", 1)[1]
    return subject


def _match_sorter_record(sent_subject: str, sorter_records: list[dict]) -> Optional[dict]:
    base_subject = _strip_test_prefix(sent_subject)
    for record in reversed(sorter_records):
        subject = record.get("subject", "")
        if subject == sent_subject or subject == base_subject or base_subject in subject:
            return record
    return None


def generate_report() -> str:
    sent = read_log(SENT_LOG)
    uptime = read_log(UPTIME_LOG)
    sorter_records = read_log(SORTER_HISTORY_LOG)

    sent_items = [e for e in sent if e.get("event") == "sent"]
    total_sent = len(sent_items)
    send_errors = sum(1 for e in sent if e.get("event") == "send_error")
    crashes = sum(1 for e in uptime if e.get("event") == "crash_detected")
    recoveries = sum(1 for e in uptime if e.get("event") == "recovery")

    monitor_start = next((e for e in uptime if e.get("event") == "monitor_start"), None)
    last_event = uptime[-1] if uptime else None
    total_seconds = 0
    down_seconds = 0
    if monitor_start and last_event:
        t_start = datetime.fromisoformat(monitor_start["time"])
        t_end = datetime.fromisoformat(last_event["time"])
        total_seconds = (t_end - t_start).total_seconds()
        down_start = None
        for e in uptime:
            if e.get("event") == "crash_detected":
                down_start = datetime.fromisoformat(e["time"])
            elif e.get("event") == "recovery" and down_start:
                down_seconds += (datetime.fromisoformat(e["time"]) - down_start).total_seconds()
                down_start = None
        if down_start:
            down_seconds += (datetime.fromisoformat(last_event["time"]) - down_start).total_seconds()

    uptime_pct = ((total_seconds - down_seconds) / total_seconds * 100) if total_seconds > 0 else 0

    type_counts = Counter(e.get("type", "?") for e in sent_items)
    expected_counts = Counter(e.get("expected", "?") for e in sent_items)
    sorter_outcomes = Counter(r.get("decision", "?") for r in sorter_records)

    matched = 0
    correct = 0
    mismatches = []
    for item in sent_items:
        record = _match_sorter_record(item.get("subject", ""), sorter_records)
        if not record:
            mismatches.append((item.get("subject", ""), item.get("expected"), "MISSING"))
            continue
        matched += 1
        actual = record.get("decision")
        if actual == item.get("expected"):
            correct += 1
        else:
            mismatches.append((item.get("subject", ""), item.get("expected"), actual))

    accuracy = (correct / matched * 100) if matched else 0

    lines = [
        "=" * 60,
        "  SORTER REPORT — TÝDENNÍ TEST",
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
        f"  Zalogováno:      {matched}",
        f"  Správně:         {correct}",
        f"  Přesnost:        {accuracy:.1f}%",
        "",
        "  Rozložení odeslaných typů:",
    ]
    for k, v in sorted(type_counts.items(), key=lambda x: -x[1]):
        lines.append(f"    {k:<12} {v:>4}x")

    lines += ["", "  Očekávaná rozhodnutí:"]
    for k, v in sorted(expected_counts.items()):
        lines.append(f"    {k:<12} {v:>4}x")

    lines += ["", "  Rozhodnutí sorteru v historii:"]
    for k, v in sorted(sorter_outcomes.items()):
        lines.append(f"    {k:<12} {v:>4}x")

    if mismatches:
        lines += ["", "── NESHODY / CHYBĚJÍCÍ ───────────────────────────────"]
        for subject, expected, actual in mismatches[:30]:
            lines.append(f"  {expected:>4} -> {actual:<7} {subject[:80]}")
        if len(mismatches) > 30:
            lines.append(f"  ... a dalších {len(mismatches) - 30}")

    lines += ["", "=" * 60]
    return "\n".join(lines)


def _now() -> str:
    return datetime.now().strftime("%H:%M:%S")


async def run(total_emails: int, duration_seconds: int):
    print("\nSorter týdenní test spuštěn")
    print(f"   Cíl:    {total_emails} emailů za {duration_seconds // 3600:.0f}h "
          f"{(duration_seconds % 3600) // 60:.0f}min")
    print(f"   Target: {TARGET}")
    print(f"   Logy:   {SENT_LOG}, {UPTIME_LOG}")
    print("   Ctrl+C pro předčasné ukončení + report\n")

    log_event(UPTIME_LOG, {
        "event": "test_start",
        "total_emails": total_emails,
        "duration_seconds": duration_seconds,
    })

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
