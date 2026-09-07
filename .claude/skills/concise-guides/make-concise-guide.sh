#!/usr/bin/env bash
# Condense references/<game>.txt into references/<game>_concise.txt with the
# claude CLI, keeping only what someone needs to add the game to the trainer.
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
You are condensing one chunk of a fighting game FAQ so that an engineer can add
the game to a move input trainer. The trainer needs the roster, every move with
its input, and anything the guide says about how the game reads inputs.

Keep, copied out exactly as they appear:
  - character names and the headings that introduce them
  - move list lines: the move name and its command notation, with the original
    spacing, column alignment and line breaks left untouched
  - the notation key or legend explaining the abbreviations the guide uses
  - any statement about input timing, buffering, motion leniency, input
    shortcuts, negative edge, charge times or how strict the game is

Drop everything else: story, credits, greetings, email addresses, ASCII art,
tables of contents, version history, legal notices, strategy, combos, matchup
advice, tier lists, unlock instructions and anything about modes or options.

Do not summarise, rewrite, reformat or translate what you keep. A parser will be
written against the exact layout of these lines, so copy them character for
character. Output only the kept text, with no preamble, commentary or code
fences. If this chunk contains nothing worth keeping, output nothing at all.
EOF

condense() {
    local game=$1
    local source="$REFERENCES/$game.txt"
    local target="$REFERENCES/${game}_concise.txt"

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
        name=$(basename "$path" .txt)
        [[ $name == *_concise ]] && continue
        games+=("$name")
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
