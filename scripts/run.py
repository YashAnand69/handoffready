"""Start the app only on its documented loopback interface."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
import os
import uvicorn
from handoffready.api import create_app

if __name__ == "__main__":
    port = int(os.environ.get("HANDOFFREADY_PORT", "8877"))
    if not 1024 <= port <= 65535:
        raise SystemExit("App port must be between 1024 and 65535")
    uvicorn.run(create_app(port=port), host="127.0.0.1", port=port, log_level="warning")
