import os
import sys
from pathlib import Path

WEB_DIR = Path(__file__).resolve().parents[1]
APPS_DIR = WEB_DIR / "apps"

for path in (WEB_DIR, APPS_DIR):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
