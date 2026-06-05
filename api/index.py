import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1] / "kiraya_haa"
sys.path.insert(0, str(APP_DIR))

from app import create_app  # noqa: E402

app = create_app()
