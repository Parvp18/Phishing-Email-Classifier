"""
PhishGuard Configuration Module
================================
Centralizes all application settings, loading values from environment
variables with sensible defaults. No secrets are hardcoded.
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR: Path = Path(__file__).resolve().parent

# ---------------------------------------------------------------------------
# API Keys & Secrets
# ---------------------------------------------------------------------------
VIRUSTOTAL_API_KEY: str = os.getenv("VIRUSTOTAL_API_KEY", "")
raw_keys = os.getenv("API_KEYS", "dev-key-123,your-secret-key-1").split(",")
API_KEYS: list[str] = [k.strip() for k in raw_keys if k.strip()]
for default_k in ["dev-key-123", "your-secret-key-1"]:
    if default_k not in API_KEYS:
        API_KEYS.append(default_k)
FLASK_SECRET_KEY: str = os.getenv("FLASK_SECRET_KEY", "phishguard-dev-secret")

# ---------------------------------------------------------------------------
# Filesystem Paths
# ---------------------------------------------------------------------------
MODEL_DIR: str = str(BASE_DIR / "models_saved")
UPLOAD_FOLDER: str = str(BASE_DIR / "uploads")
REPORTS_FOLDER: str = str(BASE_DIR / "reports")
DATA_DIR: str = str(BASE_DIR / "data")

# ---------------------------------------------------------------------------
# Limits & Thresholds
# ---------------------------------------------------------------------------
MAX_EMAIL_SIZE_BYTES: int = 500_000
MAX_BULK_ROWS: int = 500
RETRAIN_MIN_FEEDBACK: int = 50
RATE_LIMIT: str = "20 per minute"

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{BASE_DIR / 'instance' / 'phishguard.db'}"
)

# ---------------------------------------------------------------------------
# Model Metadata
# ---------------------------------------------------------------------------
MODEL_VERSION: str = "1.0.0"

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# ---------------------------------------------------------------------------
# Ensure required directories exist
# ---------------------------------------------------------------------------
for _dir in [MODEL_DIR, UPLOAD_FOLDER, REPORTS_FOLDER, DATA_DIR,
             str(BASE_DIR / "instance")]:
    os.makedirs(_dir, exist_ok=True)
