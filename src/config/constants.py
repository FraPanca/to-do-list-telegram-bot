import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = BASE_DIR / "todo.db"

load_dotenv(BASE_DIR / ".env")

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
USER_ID_RAW = os.getenv("TELEGRAM_USER_ID", "")

if not TOKEN or not USER_ID_RAW:
    raise RuntimeError("Configura TELEGRAM_BOT_TOKEN e TELEGRAM_USER_ID nel file .env")

try:
    ALLOWED_USER_ID = int(USER_ID_RAW)
except ValueError as exc:
    raise RuntimeError("TELEGRAM_USER_ID deve essere un numero intero") from exc