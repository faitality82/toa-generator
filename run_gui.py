"""Entry point for the TOA Generator desktop GUI."""

import os
import sys
from pathlib import Path

# PyInstaller: set CWD to exe directory so relative paths (.env) resolve correctly
if getattr(sys, "frozen", False):
    os.chdir(Path(sys.executable).parent)
else:
    # Ensure packages are importable when running from source
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from gui.app import TOAGeneratorApp


def main():
    app = TOAGeneratorApp()
    app.mainloop()


if __name__ == "__main__":
    main()
