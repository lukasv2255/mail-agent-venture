"""
Generate and install the macOS LaunchAgent plist for this project instance.

The committed launchd file is a template. This script resolves paths from the
current checkout and writes the machine-specific plist to ~/Library/LaunchAgents.
"""
import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

TEMPLATE_FILE = PROJECT_ROOT / "launchd" / "com.mailagent.plist.template"
LABEL = os.getenv("LAUNCHD_LABEL", "com.mailagent.agent")
PYTHON_BIN = os.getenv("PYTHON_BIN") or sys.executable
LOG_DIR = Path(os.getenv("LOG_DIR") or PROJECT_ROOT / "logs").expanduser()
if not LOG_DIR.is_absolute():
    LOG_DIR = PROJECT_ROOT / LOG_DIR

INSTALL_DIR = Path.home() / "Library" / "LaunchAgents"
INSTALL_FILE = INSTALL_DIR / f"{LABEL}.plist"


def render_template() -> str:
    text = TEMPLATE_FILE.read_text(encoding="utf-8")
    replacements = {
        "{{LAUNCHD_LABEL}}": LABEL,
        "{{PYTHON_BIN}}": PYTHON_BIN,
        "{{PROJECT_ROOT}}": str(PROJECT_ROOT),
        "{{LOG_DIR}}": str(LOG_DIR),
    }
    for placeholder, value in replacements.items():
        text = text.replace(placeholder, value)
    return text


def run(command: list[str], check: bool = True):
    print("+ " + " ".join(command))
    return subprocess.run(command, check=check)


def main():
    INSTALL_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    INSTALL_FILE.write_text(render_template(), encoding="utf-8")
    print(f"Installed: {INSTALL_FILE}")

    run(["launchctl", "bootout", f"gui/{os.getuid()}", str(INSTALL_FILE)], check=False)
    run(["launchctl", "bootstrap", f"gui/{os.getuid()}", str(INSTALL_FILE)])
    run(["launchctl", "kickstart", "-k", f"gui/{os.getuid()}/{LABEL}"])
    run(["launchctl", "print", f"gui/{os.getuid()}/{LABEL}"], check=False)


if __name__ == "__main__":
    main()
