"""Entry point for the Nuitka Windows build, which wants a script rather than ``-m``."""

import sys

from motioninput_tui.__main__ import main

sys.exit(main())
