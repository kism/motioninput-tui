#!/usr/bin/env bash
# Rebuild the packaged rosters (src/motioninput_tui/games/data/*.json) from the
# guides in references/. Fetch those first with scripts/run-download-guides.sh.
set -euo pipefail
source .venv/bin/activate
python -m motioninput_tui_datagen "$@"
