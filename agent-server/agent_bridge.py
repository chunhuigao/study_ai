import sys
from pathlib import Path


PYTHON_DIR = Path(__file__).resolve().parent / "python"
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))

from agent_server.bridge import main


if __name__ == "__main__":
    main()

