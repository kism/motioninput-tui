#!/usr/bin/env bash
# Analyse references/<game>.txt into .claude/skills/game-brief/briefs/<game>.md:
# an engineer's brief for adding the game to the trainer (roster, guide layout
# for the parser, engine/notation gotchas, ruleset rationale, test seeds).
#
# Usage: make-brief.sh [--force] [game ...]
# With no game names, every guide in references/ that lacks a brief.
set -euo pipefail

REFERENCES=${REFERENCES:-references}
MODEL=${MODEL:-sonnet}
MIN_BYTES=${MIN_BYTES:-1200}
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BRIEFS="$SKILL_DIR/briefs"
REQUIRED_HEADINGS=("## Roster" "## Guide anatomy" "## Notation & engine fit" "## Ruleset rationale" "## Test seeds")
force=0
games=()

while [[ $# -gt 0 ]]; do
    case "$1" in
    --force) force=1 ;;
    -h | --help)
        sed -n '2,7p' "$0"
        exit 0
        ;;
    -*)
        echo "Unknown option: $1" >&2
        exit 2
        ;;
    *) games+=("$1") ;;
    esac
    shift
done

# The CLI is not always on PATH; the VS Code extension bundles one.
find_claude() {
    if [[ -n ${CLAUDE_BIN:-} ]]; then
        echo "$CLAUDE_BIN"
        return
    fi
    if command -v claude >/dev/null 2>&1; then
        command -v claude
        return
    fi
    local bundled
    bundled=$(find "$HOME/.vscode/extensions" -maxdepth 4 -path '*anthropic.claude-code*/resources/native-binary/claude' 2>/dev/null | sort -V | tail -1)
    if [[ -n $bundled ]]; then
        echo "$bundled"
        return
    fi
    echo "No claude CLI found. Install it, or set CLAUDE_BIN to its path." >&2
    exit 1
}

CLAUDE=$(find_claude)

# Engine files the analysis has to reason against, pasted into the prompt.
CONTEXT_FILES=(
    src/motioninput_tui/engine/ruleset.py
    src/motioninput_tui/games/rulesets.py
    src/motioninput_tui/datagen/normalise.py
    src/motioninput_tui/engine/notation.py
    src/motioninput_tui/controls/buttons.py
    src/motioninput_tui/datagen/common.py
    src/motioninput_tui/datagen/hsf2.py
    src/motioninput_tui/datagen/sfa3.py
    src/motioninput_tui/datagen/sfiii3.py
    src/motioninput_tui/datagen/kof98.py
    tests/engine/test_motions/harness.py
)
EXAMPLE_BRIEF="$BRIEFS/kof98.md"

read -r -d '' INSTRUCTIONS <<'EOF' || true
You are writing a BRIEF for a software engineer who is about to add a fighting
game to a move-input trainer. The full GameFAQs move-list FAQ for the game
follows, after the repository files you must reason against.

The brief is analysis, not a copy of the guide. Its readers use it to write the
game's `Ruleset`, its datagen parser, and its motion tests. Be concrete and
specific to THIS guide and THIS engine: cite line numbers and exact marker text
from the guide, name the closest existing parser, and check the guide's notation
against `normalise.py` and `notation.py` yourself.

COPYRIGHT: you may name characters and quote at most a handful of individual
inputs as examples. Never reproduce a whole move list or a `| Move | Input |`
table. The roster section lists character names only.

Output GitHub-flavoured Markdown and nothing else: no preamble, no closing
remarks, no code fence around the whole reply. Start with YAML frontmatter:

---
game: <key>
panel: <street-fighter | neo-geo | mortal-kombat | tekken | eight | ... the ButtonSet key>
closest_parser: <hsf2 | sfa3 | sfiii3 | kof98>
predicted_trainable: <integer percent you expect `datagen --show-skipped` to report>
---
# <Full game name> — brief

<one sentence: what the game is and its headline input quirk>

Then these five sections, `##` headings exactly as written:

## Roster
- How many characters, and every character's name (grouped by team if the guide
  groups them). Names only -- never moves. Which guide sections to SKIP
  (alternate-style versions of listed characters, hidden-character prose,
  tables of contents) and why.
- `datagen/names.py` overrides the guide's spellings call for (ugly romaji,
  names that collide with another game), keyed by the key `character_key()`
  would produce. "none" if there are none.
- The shape of a character heading in the guide, and any variant forms.

## Guide anatomy (for the parser)
- The move-list section: start marker (with line number) to end marker. Note
  when a marker also appears in the table of contents and which one to take.
- What a character heading looks like as a rough regex or description, plus
  variants (subtitle lines, team suffixes).
- Which block under each character to parse — games often have a terse list and
  a verbose one; say which, and where it ends.
- The notation dialect (`qcf + P` shorthand, directions spelled out, an ISM/
  style column) and the closest existing parser to start from.
- Line-level quirks: continuation lines, follow-up phrasing ("P from X",
  "during Y"), condition prefixes ("When close,", "In air,").

## Notation & engine fit
- The button vocabulary (A/B/C/D, LP..HK, ...) and the panel `ButtonSet`.
- If the panel is not Street Fighter's six: the parser must translate commands
  to SF notation for `normalise`, then map the resulting `ButtonRequirement`
  back onto the real panel buttons, because the recogniser matches `Button`
  identity, not punch/kick family. Point at `datagen/kof98.py`'s `_neo_buttons`.
- Token collisions (button letters that clash with direction tokens) and what
  disambiguates them.
- Motions in this guide that are NOT keys in `normalise._MOTION_TABLE` or
  `_CHARGE_TABLE` and will therefore be skipped — list the token sequences and
  roughly how many moves each costs.
- The predicted trainable percentage, and if it is below ~80%, exactly why
  (command throws the engine has no model for, compound super motions,
  follow-ups and stances).

## Ruleset rationale
- Where the game sits relative to `HSF2` (strict), `SFA3` (mid) and `SFIII3`
  (lenient), and why, using real knowledge of the game: buffer leniency,
  whether a dragon punch has a shortcut, charge duration in frames, negative
  edge.
- The fields that matter, each with a value and a one-line reason:
  `dp_double_tap`, `dp_skip_down`, `lenient_diagonals`, `charge_ms`,
  `charge_release_ms`, `negative_edge`, and the motion/activation windows if
  they should differ from the interpolated default.
- Which characters are charge characters.
- The single headline quirk this game teaches that the others do not.
- A complete proposed `Ruleset(...)` call.

## Test seeds
- Three or four characters worth covering. For each: the shared `harness.py`
  script(s) that apply (`QUARTER_CIRCLE_FORWARD_HP`, `DOWN_DOUBLE_TAP_FORWARD_HP`,
  the half-circle ones) or a short custom script description, and the move name
  it should produce. Prefer cases where the same script gives a different answer
  here than in the Street Fighter games.

Do not invent characters, moves, inputs or rules. If you are unsure of a real
game-feel fact, say so rather than guessing a number with false confidence.
EOF

brief_for() {
    local game=$1
    local source="$REFERENCES/$game.txt"
    local target="$BRIEFS/$game.md"

    if [[ ! -f $source ]]; then
        echo "  $game: no $source, fetch it first with: uv run python -m motioninput_tui_guides" >&2
        return 1
    fi
    if [[ -s $target && $force -eq 0 ]]; then
        echo "  $game: already have $(basename "$target"), skipping"
        return 0
    fi

    local work
    work=$(mktemp -d)
    # shellcheck disable=SC2064  # $work is expanded now, on purpose
    trap "rm -rf '$work'" RETURN

    # Instructions go as the prompt argument; the bulk (repo files + guide) is
    # piped on stdin, the same split make-concise-guide.sh used.
    {
        echo "=== REPOSITORY FILES (reason against these) ==="
        for file in "${CONTEXT_FILES[@]}"; do
            [[ -f $file ]] || continue
            echo
            echo "--- $file ---"
            cat "$file"
        done
        if [[ -f $EXAMPLE_BRIEF ]]; then
            echo
            echo "--- WORKED EXAMPLE: $(basename "$EXAMPLE_BRIEF") ---"
            cat "$EXAMPLE_BRIEF"
        fi
        echo
        echo "=== FULL GUIDE: $game ($(wc -l <"$source" | tr -d ' ') lines) ==="
        cat "$source"
    } >"$work/data.txt"

    echo "  $game: analysing $(wc -c <"$work/data.txt" | tr -d ' ') bytes with $MODEL ..."
    if ! "$CLAUDE" -p --model "$MODEL" "$INSTRUCTIONS" <"$work/data.txt" >"$work/out.md"; then
        echo "  $game: the claude CLI failed, leaving $target alone" >&2
        return 1
    fi

    local size
    size=$(wc -c <"$work/out.md" | tr -d ' ')
    if [[ $size -lt $MIN_BYTES ]]; then
        echo "  $game: only $size bytes came back, not a brief. Leaving $target alone" >&2
        return 1
    fi
    local heading
    for heading in "${REQUIRED_HEADINGS[@]}"; do
        if ! grep -qF "$heading" "$work/out.md"; then
            echo "  $game: reply is missing the '$heading' section. Leaving $target alone" >&2
            return 1
        fi
    done

    mkdir -p "$BRIEFS"
    mv "$work/out.md" "$target"
    echo "  $game: wrote $target ($size bytes)"
}

if [[ ${#games[@]} -eq 0 ]]; then
    for path in "$REFERENCES"/*.txt; do
        [[ -f $path ]] || continue
        games+=("$(basename "$path" .txt)")
    done
fi

if [[ ${#games[@]} -eq 0 ]]; then
    echo "No guides in $REFERENCES. Fetch them with: uv run python -m motioninput_tui_guides" >&2
    exit 1
fi

echo "Briefing with $CLAUDE (model: $MODEL)"
failed=0
for game in "${games[@]}"; do
    brief_for "$game" || failed=1
done
exit "$failed"
