"""
Mixovaný týdenní test inboxu.

Posílá 1000 emailů během 7 dnů na testovací inbox a míchá všechny emailové
scénáře, které už v repo testujeme:
  - sorter
  - responder
  - email_body

Použití:
  python3 tests/run_mixed_week.py
  python3 tests/run_mixed_week.py --fast
  python3 tests/run_mixed_week.py --report

Výchozí běh:
  - odesílatel: newagent7878@gmail.com
  - příjemce:   johnybb11@seznam.cz
  - počet:      1000 emailů
  - délka:      7 dní
"""
import argparse
import asyncio
import base64
import importlib.util
import json
import random
import signal
import sys
from collections import Counter
from datetime import datetime, timezone
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import LOG_DIR as ROOT_LOG_DIR
from src.gmail_client import get_gmail_service

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TARGET = "johnybb11@seznam.cz"
EXPECTED_SENDER = "newagent7878@gmail.com"

LOG_DIR = ROOT_LOG_DIR / "mixed_week"
SENT_LOG = LOG_DIR / "week_sent.jsonl"
REPORT_FILE = LOG_DIR / "week_report.txt"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Nepodařilo se načíst modul {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_scenarios() -> list[dict]:
    sorter_mod = _load_module("mixed_sorter_test", PROJECT_ROOT / "tests" / "sorter" / "test_sorter.py")
    responder_mod = _load_module("mixed_responder_week", PROJECT_ROOT / "tests" / "responder" / "test_responder.py")
    body_mod = _load_module("mixed_email_body", PROJECT_ROOT / "tests" / "email_body" / "send_html_body_test.py")

    scenarios: list[dict] = []

    for index, email_def in enumerate(sorter_mod.TEST_EMAILS, start=1):
        if index <= 12:
            email_type = "SPAM"
            template_id = f"S{index:02d}"
        elif index <= 20:
            email_type = "INQUIRY"
            template_id = f"P{index - 12:02d}"
        else:
            email_type = f"NEWSLETTER"
            template_id = f"N{index - 20:02d}"

        scenarios.append(
            {
                "source": "sorter",
                "frame_seq": index,
                "template_id": template_id,
                "type": email_type,
                "mode": "plain",
                "subject": email_def["subject"],
                "body": email_def["body"],
            }
        )

    for index, template in enumerate(responder_mod.TEMPLATES, start=1):
        scenarios.append(
            {
                "source": "responder",
                "frame_seq": index,
                "template_id": template["id"],
                "type": template["type"],
                "mode": "plain",
                "subject": template["subject"],
                "body": template["body"],
            }
        )

    scenarios.extend(
        [
            {
                "source": "email-body",
                "frame_seq": 1,
                "template_id": "HTML-ONLY",
                "type": "HTML_ONLY",
                "mode": "html_only",
                "subject": "HTML-only email — žádný plain text",
                "body": body_mod.HTML_BODY,
            },
            {
                "source": "email-body",
                "frame_seq": 2,
                "template_id": "MULTIPART",
                "type": "MULTIPART",
                "mode": "multipart",
                "subject": "Multipart email — plain text + HTML",
                "body": {
                    "plain": body_mod.PLAIN_BODY,
                    "html": body_mod.HTML_BODY,
                },
            },
            {
                "source": "email-body",
                "frame_seq": 3,
                "template_id": "PLAIN",
                "type": "PLAIN_TEXT",
                "mode": "plain",
                "subject": "Plain text email — referenční případ",
                "body": body_mod.PLAIN_BODY,
            },
            {
                "source": "email-body",
                "frame_seq": 4,
                "template_id": "APPLE",
                "type": "APPLE_MAIL_HTML",
                "mode": "html_only",
                "subject": "Apple Mail styl — HTML s inline CSS",
                "body": body_mod.APPLE_MAIL_HTML_BODY,
            },
        ]
    )

    return scenarios


SCENARIOS = _load_scenarios()
PERSIST_SCENARIOS = [
    {
        "source": "persist",
        "frame_seq": 1,
        "template_id": "PERSIST-SPAM-01A",
        "type": "SPAM",
        "mode": "plain",
        "subject": "Persist test — SEO audit zdarma pro vaši firmu",
        "body": (
            "Dobrý den,\n\n"
            "nabízíme bezplatný SEO audit vašeho webu a návrh konkrétních kroků "
            "pro zvýšení návštěvnosti. Pokud budete chtít, navážeme placenou "
            "spoluprací.\n\n"
            "SEO Booster Team\n"
            "info@seobooster.example"
        ),
    },
    {
        "source": "persist",
        "frame_seq": 2,
        "template_id": "PERSIST-SPAM-01B",
        "type": "SPAM",
        "mode": "plain",
        "subject": "Persist test — SEO audit zdarma pro vaši firmu",
        "body": (
            "Dobrý den,\n\n"
            "nabízíme bezplatný SEO audit vašeho webu a návrh konkrétních kroků "
            "pro zvýšení návštěvnosti. Pokud budete chtít, navážeme placenou "
            "spoluprací.\n\n"
            "SEO Booster Team\n"
            "info@seobooster.example"
        ),
    },
]
SCENARIOS.extend(PERSIST_SCENARIOS)
SCENARIO_WEIGHTS = {
    "sorter": 50,
    "responder": 35,
    "email-body": 15,
    "persist": 20,
}
WEIGHTED_SCENARIOS = []
for scenario in SCENARIOS:
    WEIGHTED_SCENARIOS.extend([scenario] * SCENARIO_WEIGHTS.get(scenario["source"], 10))


def _now() -> str:
    return datetime.now().strftime("%H:%M:%S")


def log_event(log_file: Path, record: dict):
    log_file.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(record)
    payload["time"] = datetime.now(timezone.utc).isoformat()
    with open(log_file, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def read_log(log_file: Path) -> list[dict]:
    if not log_file.exists():
        return []
    rows = []
    for line in log_file.read_text(encoding="utf-8").splitlines():
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def _build_subject(scenario: dict, seq: int) -> str:
    prefix = (
        f"[{scenario['source'].upper()}-{scenario['type']}-"
        f"{scenario['frame_seq']:02d}-{seq:04d}]"
    )
    return f"{prefix} {scenario['subject']}"


def _send_raw(service, msg):
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    service.users().messages().send(userId="me", body={"raw": raw}).execute()


def send_email(service, scenario: dict, seq: int, target: str) -> dict:
    subject = _build_subject(scenario, seq)
    mode = scenario["mode"]

    if mode == "plain":
        msg = EmailMessage()
        msg["To"] = target
        msg["Subject"] = subject
        msg.set_content(scenario["body"])
    elif mode == "html_only":
        msg = MIMEMultipart("alternative")
        msg["To"] = target
        msg["Subject"] = subject
        msg.attach(MIMEText(scenario["body"], "html", "utf-8"))
    elif mode == "multipart":
        msg = MIMEMultipart("alternative")
        msg["To"] = target
        msg["Subject"] = subject
        msg.attach(MIMEText(scenario["body"]["plain"], "plain", "utf-8"))
        msg.attach(MIMEText(scenario["body"]["html"], "html", "utf-8"))
    else:
        raise ValueError(f"Neznámý mode: {mode}")

    _send_raw(service, msg)

    record = {
        "event": "sent",
        "seq": seq,
        "source": scenario["source"],
        "type": scenario["type"],
        "template_id": scenario["template_id"],
        "mode": mode,
        "subject": subject,
        "target": target,
    }
    log_event(SENT_LOG, record)
    return record


def build_schedule(total_emails: int, scenarios: list | None = None, weighted: list | None = None) -> list[dict]:
    if scenarios is None:
        scenarios = SCENARIOS
    if weighted is None:
        weighted = WEIGHTED_SCENARIOS

    persist = [s for s in scenarios if s["source"] == "persist"]

    if total_emails < len(scenarios):
        if total_emails < len(persist):
            raise ValueError(
                f"Počet emailů ({total_emails}) je menší než minimální persist dvojice ({len(persist)})."
            )
        others = [s for s in scenarios if s["source"] != "persist"]
        remaining = total_emails - len(persist)
        schedule = persist + random.sample(others, min(remaining, len(others)))
        random.shuffle(schedule)
        return schedule

    schedule = list(scenarios)
    remaining = total_emails - len(schedule)
    pool = weighted if weighted else scenarios
    schedule.extend(random.choice(pool) for _ in range(remaining))
    random.shuffle(schedule)
    return schedule


async def scheduler_loop(service, total_emails: int, duration_seconds: int, target: str, stop_event: asyncio.Event, scenarios: list | None = None, weighted: list | None = None):
    sent = 0
    schedule = build_schedule(total_emails, scenarios, weighted)
    base_interval = (duration_seconds / total_emails) if duration_seconds > 0 else 0

    while sent < total_emails and not stop_event.is_set():
        if sent > 0 and base_interval > 0:
            await asyncio.sleep(base_interval * random.uniform(0.6, 1.4))
            if stop_event.is_set():
                break

        scenario = schedule[sent]
        try:
            record = send_email(service, scenario, sent + 1, target)
            print(
                f"  ✉  [{_now()}] #{sent + 1:04d} "
                f"{record['source']}/{record['type']} {record['subject'][:90]}"
            )
        except Exception as exc:
            print(f"  ⚠  [{_now()}] Chyba při odesílání #{sent + 1:04d}: {exc}")
            log_event(
                SENT_LOG,
                {
                    "event": "send_error",
                    "seq": sent + 1,
                    "source": scenario["source"],
                    "type": scenario["type"],
                    "template_id": scenario["template_id"],
                    "error": str(exc),
                },
            )

        sent += 1

    print(f"\nScheduler hotov — odesláno {sent} emailů.")
    stop_event.set()


def generate_report() -> str:
    events = read_log(SENT_LOG)
    sent_items = [item for item in events if item.get("event") == "sent"]
    errors = [item for item in events if item.get("event") == "send_error"]

    source_counts = Counter(item["source"] for item in sent_items)
    type_counts = Counter(item["type"] for item in sent_items)
    template_counts = Counter(item["template_id"] for item in sent_items)

    lines = [
        "=== Mixed Week Report ===",
        f"Vygenerováno: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        f"Odesláno: {len(sent_items)}",
        f"Chyby při odeslání: {len(errors)}",
        "",
        "Rozložení podle scénáře:",
    ]
    for name, count in sorted(source_counts.items()):
        lines.append(f"  - {name}: {count}")

    lines.extend(["", "Rozložení podle typu:"])
    for name, count in sorted(type_counts.items()):
        lines.append(f"  - {name}: {count}")

    lines.extend(["", "Top 15 template_id:"])
    for template_id, count in template_counts.most_common(15):
        lines.append(f"  - {template_id}: {count}")

    if errors:
        lines.extend(["", "Poslední chyby:"])
        for item in errors[-10:]:
            lines.append(
                f"  - #{item.get('seq', '?'):>4} "
                f"{item.get('source', '?')}/{item.get('template_id', '?')}: {item.get('error', '')}"
            )

    report = "\n".join(lines)
    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text(report, encoding="utf-8")
    return report


def verify_sender(service, allow_other_sender: bool):
    profile = service.users().getProfile(userId="me").execute()
    actual_sender = profile.get("emailAddress", "").strip().lower()
    if actual_sender != EXPECTED_SENDER and not allow_other_sender:
        raise RuntimeError(
            "Přihlášený Gmail účet neodpovídá očekávanému odesílateli. "
            f"Očekávám {EXPECTED_SENDER}, ale Gmail API je přihlášené jako {actual_sender or 'UNKNOWN'}. "
            "Pokud to chceš obejít záměrně, použij --allow-other-sender."
        )
    return actual_sender


async def run(args):
    if args.report:
        print(generate_report())
        return

    # Filtrování scénářů podle --sorter / --responder
    only_sources: set[str] = set()
    if args.sorter:
        only_sources.update({"sorter", "persist"})
    if args.responder:
        only_sources.add("responder")

    if only_sources:
        active_scenarios = [s for s in SCENARIOS if s["source"] in only_sources]
        active_weighted = [s for s in WEIGHTED_SCENARIOS if s["source"] in only_sources]
    else:
        active_scenarios = SCENARIOS
        active_weighted = WEIGHTED_SCENARIOS

    target = args.target
    total_emails = args.count
    duration_seconds = int(args.days * 24 * 60 * 60)
    if args.fast:
        total_emails = min(30, len(active_scenarios)) if only_sources else 30
        duration_seconds = 0

    if args.seed is not None:
        random.seed(args.seed)

    service = get_gmail_service()
    actual_sender = verify_sender(service, args.allow_other_sender)

    sources_label = ", ".join(sorted(only_sources)) if only_sources else "vše"
    print(
        "Spouštím mixovaný týdenní test:\n"
        f"  Odesílatel: {actual_sender}\n"
        f"  Příjemce:   {target}\n"
        f"  Moduly:     {sources_label}\n"
        f"  Počet:      {total_emails}\n"
        f"  Délka:      {duration_seconds // 60} minut\n"
        f"  Scénářů v poolu: {len(active_scenarios)}\n"
    )

    stop_event = asyncio.Event()

    def _handle_stop(*_args):
        stop_event.set()

    signal.signal(signal.SIGINT, _handle_stop)
    signal.signal(signal.SIGTERM, _handle_stop)

    await scheduler_loop(service, total_emails, duration_seconds, target, stop_event, active_scenarios, active_weighted)
    print("\n" + generate_report())


def main():
    parser = argparse.ArgumentParser(description="Mixovaný týdenní email test")
    parser.add_argument("--target", default=DEFAULT_TARGET, help="Cílová testovací adresa")
    parser.add_argument("--count", type=int, default=1000, help="Počet emailů")
    parser.add_argument("--days", type=float, default=7.0, help="Délka běhu ve dnech")
    parser.add_argument("--fast", action="store_true", help="Rychlý běh: 30 emailů okamžitě (nebo méně podle filtru)")
    parser.add_argument("--sorter", action="store_true", help="Jen sorter scénáře")
    parser.add_argument("--responder", action="store_true", help="Jen responder scénáře")
    parser.add_argument("--report", action="store_true", help="Pouze vygeneruje report z logu")
    parser.add_argument("--seed", type=int, help="Fixní seed pro opakovatelný mix")
    parser.add_argument(
        "--allow-other-sender",
        action="store_true",
        help="Povolí běh i když Gmail API není přihlášené jako očekávaný účet",
    )
    args = parser.parse_args()
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
