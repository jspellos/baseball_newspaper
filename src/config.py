from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_DIR = PROJECT_ROOT / "templates"
STATIC_DIR = PROJECT_ROOT / "static"
STORAGE_DIR = PROJECT_ROOT / "storage"
CACHE_DIR = STORAGE_DIR / "cache"
OUTPUT_DIR = PROJECT_ROOT / "output"

MLB_API_BASE = "https://statsapi.mlb.com/api/v1"
MLB_SPORT_ID = 1

