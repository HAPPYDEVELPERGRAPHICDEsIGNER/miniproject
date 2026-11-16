import sys
import os
from pathlib import Path

# Ensure directory is on python path
current_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir))
os.chdir(str(current_dir))

import uvicorn

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, log_level="info")
