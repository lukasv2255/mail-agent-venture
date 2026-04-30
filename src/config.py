"""
Central project configuration.

Paths are derived from this repository location by default. Deployment-specific
overrides belong in environment variables, not in committed source files.
"""
import os
from pathlib import Path
from typing import Union


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def path_from_env(name: str, default: Union[Path, str]) -> Path:
    value = os.getenv(name)
    default_path = Path(default)
    if not value:
        return default_path if default_path.is_absolute() else PROJECT_ROOT / default_path
    path = Path(value).expanduser()
    return path if path.is_absolute() else PROJECT_ROOT / path


LOG_DIR = path_from_env("LOG_DIR", PROJECT_ROOT / "logs")
DATA_DIR = path_from_env("DATA_DIR", PROJECT_ROOT / "data")
PROMPTS_DIR = path_from_env("PROMPTS_DIR", PROJECT_ROOT / "prompts")
TEMPLATES_DIR = path_from_env("TEMPLATES_DIR", PROJECT_ROOT / "templates")

AGENT_LOG = LOG_DIR / "agent.log"
AGENT_ERR_LOG = LOG_DIR / "agent_err.log"
UPTIME_LOG = LOG_DIR / "uptime.jsonl"

RESPONDER_LOG_DIR = DATA_DIR / "logs" / "responder"
RESPONDER_HISTORY_LOG = RESPONDER_LOG_DIR / "responses.jsonl"

SORTER_LOG_DIR = DATA_DIR / "logs" / "sorter"
SORTER_HISTORY_LOG = SORTER_LOG_DIR / "sorter.jsonl"
SORTER_STATE_FILE = DATA_DIR / "sorter" / "state.json"
