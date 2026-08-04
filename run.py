#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from backend.config import settings
from backend.app import app
import uvicorn

uvicorn.run(app, host="0.0.0.0", port=settings.BACKEND_PORT)
