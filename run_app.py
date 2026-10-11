"""Source-checkout and PyInstaller launcher."""

from __future__ import annotations

import sys
from pathlib import Path

source = Path(__file__).resolve().parent / "src"
if source.is_dir():
    sys.path.insert(0, str(source))

from kdrive_link_manager.main import main


if __name__ == "__main__":
    main()

