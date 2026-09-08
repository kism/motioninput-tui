# references

The move list guides the parsers in `src/motioninput_tui/datagen/` read, plus a
condensed Markdown version of each for reading while adding a game.

**None of these files are in the repository.** The guides are written by their
authors and explicitly may not be redistributed, so both `references/*.txt` and
the `references/*_concise.md` derived from them are gitignored, and each user
fetches or regenerates their own copy of pages they could equally read in a
browser.

```bash
uv sync --extra guides    # curl-cffi and beautifulsoup4, not needed by the trainer
uv run -m motioninput_tui_guides          # fetch anything missing
uv run -m motioninput_tui_guides --list
```

Nothing is downloaded if the file is already here; use `--force` to refresh one.
Each guide is checked against a recorded SHA-256, so a changed page or a corrupt
copy fails the fetch instead of quietly feeding the parsers.

The catalogue of guides, with the exact GameFAQs page each one comes from and
its checksum, is
[`src/motioninput_tui_guides/sources.json`](../src/motioninput_tui_guides/sources.json).

## Concise guides

`<game>_concise.md` is a full guide with everything but the roster, the move
tables, the notation key and the input-behaviour notes stripped out — roughly a
quarter of the size, as standardised Markdown. It is what you read before adding
a game; the datagen parser is still written against the full `<game>.txt`. Make
the missing ones with:

```bash
./scripts/run-concise-guides.sh           # every guide that lacks one
./scripts/run-concise-guides.sh sfa3       # just this one
```

See the
[`concise-guides` skill](../.claude/skills/concise-guides/SKILL.md) for how it
condenses and how the result is checked.

## You do not need any of this to run the trainer

The parsed rosters in `src/motioninput_tui/games/data/` are generated from the
guides and committed; the guides are only needed to regenerate that data.
