#!/usr/bin/env bash
# Write .claude/skills/game-brief/briefs/<game>.md for every guide in
# references/, then verify. Guides that already have a brief are left alone;
# pass --force to redo them, or name games to do only those.

set -euo pipefail

function print_heading() {
    echo
    echo "=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-="
    echo "$1 >>>"
}

if [[ $# -eq 0 ]]; then
    cat >&2 <<'WARN'
Note: with no arguments this writes a brief for every guide that lacks one, each
a claude CLI pass over the full guide. You only need that when adding a game, or
when a guide changed. Existing briefs are left alone; to redo one, name it:
run-game-briefs.sh --force <game>.
WARN
    if [[ -t 0 ]]; then
        read -r -p "Continue? [y/N] " reply || reply=""
        [[ $reply == [yY]* ]] || exit 0
    fi
fi

source .venv/bin/activate

uv run -m motioninput_tui_guides

SKILL=".claude/skills/game-brief"

print_heading "Briefing"
"$SKILL/make-brief.sh" "$@"

print_heading "Verifying"
python "$SKILL/verify-brief.py"
