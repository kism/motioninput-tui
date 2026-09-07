#!/usr/bin/env bash
# Condense every guide in references/ into references/<game>_concise.txt, then
# check the result. Guides that already have a concise version are left alone;
# pass --force to redo them, or name games to do only those.

set -euo pipefail

function print_heading() {
    echo
    echo "=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-="
    echo "$1 >>>"
}

uv run -m motioninput_tui_guides

SKILL=".claude/skills/concise-guides"

source .venv/bin/activate

print_heading "Condensing"
"$SKILL/make-concise-guide.sh" "$@"

print_heading "Verifying"
python "$SKILL/verify-concise-guide.py"
