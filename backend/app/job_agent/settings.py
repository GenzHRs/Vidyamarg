"""Non-secret discovery preferences in JSON; credentials only in environment."""
import json
import os
import re
from pathlib import Path
from app.core.config import settings

CONFIG_PATH = Path(__file__).with_name("config.json")

def load_config(require_telegram=False):
    config = json.loads(CONFIG_PATH.read_text()) if CONFIG_PATH.exists() else {}
    config["api_id"] = settings.TG_API_ID
    config["api_hash"] = settings.TG_API_HASH
    config["phone"] = os.getenv("TG_PHONE", "")
    config["telegram_session_string"] = os.getenv("TG_SESSION_STRING", "")
    session_file = os.getenv("TG_SESSION_FILE", "")
    if not config["telegram_session_string"] and session_file:
        config["telegram_session_string"] = Path(session_file).read_text().strip()
    if require_telegram and not all(config.get(k) for k in ["api_id", "api_hash", "telegram_session_string"]):
        raise RuntimeError("Telegram credentials and a preauthorized session are required")
    table = config.get("postgres", {}).get("table_name", "jobs")
    if not re.fullmatch(r"[a-z_][a-z0-9_]*", table):
        raise ValueError("Invalid crawler table name")
    config["postgres"] = {"table_name": table}
    return config
