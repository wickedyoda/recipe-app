import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import uvicorn

from backend.app import app
from backend.config import settings

uvicorn.run(app, host="0.0.0.0", port=settings.BACKEND_PORT)
