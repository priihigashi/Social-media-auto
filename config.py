"""Central config loaded from environment / .env file."""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


def _require(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise EnvironmentError(f"Missing required env var: {key}")
    return value


YOUTUBE_API_KEY = _require("YOUTUBE_API_KEY")
MOSAIC_API_KEY = _require("MOSAIC_API_KEY")
MOSAIC_API_BASE = os.getenv("MOSAIC_API_BASE", "https://api.usemosaic.ai")

GOOGLE_SERVICE_ACCOUNT_PATH = Path(
    os.getenv("GOOGLE_SERVICE_ACCOUNT_PATH", "credentials/service_account.json")
)
SPREADSHEET_NAME = os.getenv("SPREADSHEET_NAME", "Video Vault")

YOUTUBE_NICHE = os.getenv("YOUTUBE_NICHE", "fitness motivation")
CAPTION_COLOR = os.getenv("CAPTION_COLOR", "white")
MAX_RESULTS = int(os.getenv("MAX_RESULTS", "15"))

CLIPS_ROOT = Path(os.getenv("CLIPS_ROOT", "clips"))
CLIPS_ROOT.mkdir(parents=True, exist_ok=True)
