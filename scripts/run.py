"""Start the app only on its documented loopback interface."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
import uvicorn
from handoffready.api import create_app

if __name__ == "__main__":
    uvicorn.run(create_app(), host="127.0.0.1", port=8877, log_level="warning")
