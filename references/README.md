# references

The move list guides the parsers in `src/motioninput_tui/datagen/` read.

**These files are not in the repository.** They are written by their authors and
explicitly may not be redistributed, so `references/*.txt` is gitignored and
each user fetches their own copy of pages they could equally read in a browser.

```bash
uv sync --extra guides    # curl-cffi and beautifulsoup4, not needed by the trainer
motioninput-tui-guides    # fetch anything missing
motioninput-tui-guides --list
```

Nothing is downloaded if the file is already here; use `--force` to refresh one.

The catalogue of guides, with the exact GameFAQs page each one comes from, is
[`src/motioninput_tui/guides/sources.json`](../src/motioninput_tui/guides/sources.json).

You do not need these files to run the trainer. The parsed rosters in
`src/motioninput_tui/games/data/` are generated from them and committed; the
guides are only needed to regenerate that data.
