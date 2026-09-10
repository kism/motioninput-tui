# references

The move list guides the parsers in `src/motioninput_tui/datagen/` read.

**None of these files are in the repository.** The guides are written by their
authors and explicitly may not be redistributed, so `references/*.txt` is
gitignored and each user fetches their own copy of a page they could equally
read in a browser. The per-game *briefs* that analyse each guide against the
engine live in `.claude/skills/game-brief/briefs/` and are committed — they are
our notes, not the guide text.

```bash
uv sync --group guides    # curl-cffi and beautifulsoup4, not needed by the trainer
uv run -m motioninput_tui_guides          # fetch anything missing
uv run -m motioninput_tui_guides --list
```

Nothing is downloaded if the file is already here; use `--force` to refresh one.
Each guide is checked against a recorded SHA-256, so a changed page or a corrupt
copy fails the fetch instead of quietly feeding the parsers.

The catalogue of guides, with the exact GameFAQs page each one comes from and
its checksum, is
[`src/motioninput_tui_guides/sources.json`](../src/motioninput_tui_guides/sources.json).

## Game briefs

`.claude/skills/game-brief/briefs/<game>.md` analyses one guide for adding the
game: the roster, the guide's layout for the parser, the button and motion
gotchas with a predicted trainable rate, a proposed `Ruleset`, and motion-test
seeds. It is what you read before adding a game; the datagen parser is still
written against the full `<game>.txt`. Make the missing ones with:

```bash
./scripts/2-game-briefs.sh           # every guide that lacks one
./scripts/2-game-briefs.sh sfa3      # just this one
```

See the
[`game-brief` skill](../.claude/skills/game-brief/SKILL.md) for the brief's
structure and how it is checked.

## You do not need any of this to run the trainer

The parsed rosters in `src/motioninput_tui/games/data/` are generated from the
guides and committed; the guides are only needed to regenerate that data.
