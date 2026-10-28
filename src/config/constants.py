import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Env
load_dotenv(BASE_DIR / ".env")

# Paths
DB_PATH = Path(os.getenv("TODO_DB_PATH", BASE_DIR / "todo.db"))

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
ADMIN_USER_ID_RAW = os.getenv("TELEGRAM_USER_ID_ADMIN", "")

if not TOKEN or not ADMIN_USER_ID_RAW:
    raise RuntimeError("Configura TELEGRAM_BOT_TOKEN e TELEGRAM_USER_ID_ADMIN nel file .env")

# Admin ID
try:
    ADMIN_USER_ID = int(ADMIN_USER_ID_RAW)
except ValueError as exc:
    raise RuntimeError("TELEGRAM_USER_ID_ADMIN deve essere un numero intero") from exc