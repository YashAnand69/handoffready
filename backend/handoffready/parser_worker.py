import json
import sys
from pathlib import Path
from .inspect import inspect_file

if __name__ == "__main__":
    try:
        result = inspect_file(Path(sys.argv[1]), sys.argv[2])
    except Exception:
        result = {"type": "unknown", "inspection": "blocked", "metadata": {}, "text": "", "error": "File could not be inspected safely."}
    print(json.dumps(result, ensure_ascii=False))
