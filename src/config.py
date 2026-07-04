"""
Central config loader. Reads .env via python-dotenv and exposes
the handful of values the rest of the app needs.
"""
import os
from dotenv import load_dotenv

load_dotenv()

B2_KEY_ID = os.environ.get("B2_KEY_ID")
B2_APP_KEY = os.environ.get("B2_APP_KEY")
B2_BUCKET_NAME = os.environ.get("B2_BUCKET_NAME", "provenance-ledger-hackathon")
B2_REGION = os.environ.get("B2_REGION", "eu-central-003")

# genblaze-nvidia reads its own key from the environment directly
# (NVIDIA_API_KEY / NVAPI_KEY — both are set in .env to be safe).
# We just check presence here so we fail fast with a clear message
# instead of a confusing SDK-level auth error later.
NVIDIA_KEY_PRESENT = bool(
    os.environ.get("NVIDIA_API_KEY") or os.environ.get("NVAPI_KEY")
)
GOOGLE_KEY_PRESENT = bool(
    os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
)

LEDGER_DB_PATH = os.environ.get("LEDGER_DB_PATH", "ledger.duckdb")


def require_credentials():
    missing = []
    if not B2_KEY_ID:
        missing.append("B2_KEY_ID")
    if not B2_APP_KEY:
        missing.append("B2_APP_KEY")
    if not GOOGLE_KEY_PRESENT:
        missing.append("GOOGLE_API_KEY (or GEMINI_API_KEY)")
    if missing:
        raise RuntimeError(
            "Missing required credentials in .env: " + ", ".join(missing)
        )
