from .base import *  # noqa: F403

DEBUG = True
SECRET_KEY = "django-insecure-dev-only-key"
ALLOWED_HOSTS = ["127.0.0.1", "localhost", ".localhost"]

# ML recommendations service (stub running locally)
# Start it with: cd src/ml && uv run uvicorn app.main:app --port 8001
ML_SERVICE_URL = "http://localhost:8001"
ML_SERVICE_TIMEOUT = 2.5
