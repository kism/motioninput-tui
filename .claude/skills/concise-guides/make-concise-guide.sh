#!/usr/bin/env bash
# Condense references/<game>.txt into references/<game>_concise.md with the
# claude CLI: standardised Markdown with only what someone needs to add the
# game to the trainer (roster, move tables, notation key, input-behaviour notes).
#
# Usage: make-concise-guide.sh [--force] [--chunk-lines N] [game ...]
# With no game names, every guide in references/ that lacks a concise version.
set -euo pipefail

REFERENCES=${REFERENCES:-references}
CHUNK_LINES=${CHUNK_LINES:-900}
MODEL=${MODEL:-haiku}
MIN_BYTES=${MIN_BYTES:-500}
force=0
games=()

while [[ $# -gt 0 ]]; do
    case "$1" in
    --force) force=1 ;;
    --chunk-lines)
        CHUNK_LINES=$2
        shift
        ;;
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

read -r -d '' PROMPT <<'EOF' || true
You are condensing one chunk of a fighting game FAQ into clean Markdown so an
engineer can add the game to a move-input trainer. Keep only the roster, every
move with its input, the notation key, and anything the guide says about how the
game reads inputs. Drop everything else: story, credits, greetings, email
addresses, pictures drawn with characters, tables of contents, version history,
legal notices, strategy, combos, matchup advice, tier lists, unlock instructions
and anything about modes or options.

Output GitHub-flavoured Markdown and nothing else: no preamble, no closing
remarks, no code fence wrapping the whole reply.

Format what you keep like this:
  - Each character gets an "## Character Name" heading, spelled exactly as the
    guide spells it.
  - Put that character's moves in one Markdown table. Use the columns the guide
    provides, normally "| Move | Input |", or add a leading column when the
    guide marks moves with a code (ISM / style / stance letters, availability
    flags). One row per move. Copy the move name and the input text verbatim:
    do not translate notation, expand abbreviations or tidy the input.
  - Keep follow-up and conditional moves as ordinary rows. If the guide struck
    one through or flagged it unavailable, say so in parentheses after the name.
  - Turn the notation key or legend into a Markdown table ("| Symbol | Meaning |")
    or a bullet list.
  - Put notes on input timing, buffering, motion leniency, input shortcuts,
    negative edge, charge times or how strict the game is under an
    "## Input behaviour" heading, as prose or bullets, in the guide's own words.
  - Anything that only reads correctly as fixed-width text (a stick-motion
    diagram, a numbered direction grid) goes in a ``` fenced block, copied
    exactly.

Do not invent characters, moves or inputs. If a move list runs off the end of
this chunk, still emit the rows you can see under a table header. If this chunk
has nothing worth keeping, output nothing at all.
EOF

condense() {
    local game=$1
    local source="$REFERENCES/$game.txt"
    local target="$REFERENCES/${game}_concise.md"

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
    # shellcheck disable=SC2064 - expand the path now, while it is still set
    trap "rm -rf '$work'" RETURN

    split -l "$CHUNK_LINES" "$source" "$work/chunk."
    local chunks=("$work"/chunk.*)
    echo "  $game: $(wc -l <"$source" | tr -d ' ') lines in ${#chunks[@]} chunks"

    local index=0
    for chunk in "${chunks[@]}"; do
        index=$((index + 1))
        printf '    chunk %d/%d ... ' "$index" "${#chunks[@]}"
        if ! "$CLAUDE" -p --model "$MODEL" "$PROMPT" <"$chunk" >>"$work/out.txt"; then
            echo "failed"
            echo "  $game: the claude CLI failed, leaving $target alone" >&2
            return 1
        fi
        printf '\n' >>"$work/out.txt"
        echo "ok"
    done

    local size
    size=$(wc -c <"$work/out.txt" | tr -d ' ')
    if [[ $size -lt $MIN_BYTES ]]; then
        echo "  $game: only $size bytes came back, that is not a guide. Leaving $target alone" >&2
        return 1
    fi

    mv "$work/out.txt" "$target"
    echo "  $game: wrote $target ($size bytes, was $(wc -c <"$source" | tr -d ' '))"
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

echo "Condensing with $CLAUDE (model: $MODEL)"
failed=0
for game in "${games[@]}"; do
    condense "$game" || failed=1
done
exit "$failed"
