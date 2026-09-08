---
name: game-brief
description: Write .claude/skills/game-brief/briefs/<game>.md, an analysis of one GameFAQs guide for adding that game to the trainer - roster decisions, the guide's structure for the parser, engine and notation gotchas with a predicted trainable rate, ruleset rationale, and motion-test seeds. Use before adding a game, when a brief is missing or stale, or when asked to refresh the game briefs.
---

# Game briefs

A brief is what to read before writing a game's `GameSpec` and parser. It is
*analysis*, not a smaller copy of the FAQ: where the game sits on the
strict-to-lenient axis and why, how the guide is laid out so the parser can find
the move list, which motions and buttons the engine cannot model, how many moves
will end up trainable, and which characters make good motion tests.

It does **not** replace `references/<game>.txt`. The parser is written against
the full guide, because it keys off fixed-width columns; the brief tells you
where to look and what to expect.

Briefs live in `briefs/<game>.md` and **are committed** — they are dev
documentation. They may name characters and quote a handful of inputs as
examples, but must never reproduce a whole move list: that is the guide
author's work. Keep whole `| Move | Input |` tables out.

## Making them

```bash
./scripts/run-game-briefs.sh              # every guide that lacks a brief, then verify
./scripts/run-game-briefs.sh sfa3 kof98   # just these
./scripts/run-game-briefs.sh --force sfa3 # redo one that exists
```

That fetches any missing guides, then runs the two steps below and passes its
arguments to the first:

```bash
.claude/skills/game-brief/make-brief.sh      # generate
.venv/bin/python .claude/skills/game-brief/verify-brief.py
```

`make-brief.sh` hands the whole guide to `claude -p` in one pass (no chunking —
the analysis needs a global view) along with the engine files it must reason
against: `engine/ruleset.py`, `games/rulesets.py`, `datagen/normalise.py`,
`engine/notation.py`, `controls/buttons.py`, the existing parsers, and
`briefs/kof98.md` as a worked example. `MODEL` defaults to `sonnet`. It is a
large prompt — a few minutes per game, longer for a big roster — so
`run-game-briefs.sh` is meant to run in the background.

Nothing is written unless the reply is a plausible size and has every required
`##` heading, so a failed run leaves the previous brief in place.

The `claude` CLI is found via `$CLAUDE_BIN`, then `claude` on `PATH`, then the
binary bundled with the VS Code extension. `MODEL` and `REFERENCES` are
environment overrides.

## What a brief contains

YAML frontmatter (`game`, `panel`, `closest_parser`, `predicted_trainable`)
then, in order:

* **Roster** — how many characters, which to include, which guide sections to
  skip and why (alternate-style versions, boss dupes, non-movelist prose), any
  `datagen/names.py` overrides the guide's spellings call for, and the shape of
  a character heading.
* **Guide anatomy (for the parser)** — where the move-list section starts and
  ends (and which repeated marker to take), what a character heading looks like
  and its variants, which block under each character to parse (the terse list,
  not the verbose one, usually), the notation dialect, the closest existing
  parser to copy, and line-level quirks (continuations, follow-up phrasing,
  condition prefixes).
* **Notation & engine fit** — the button vocabulary and panel; whether a
  non-Street-Fighter panel needs the parser to remap button requirements (it
  does — the recogniser matches `Button` identity, not punch/kick family — see
  `datagen/kof98.py`); direction/button token collisions; motions that are
  **not** in `normalise._MOTION_TABLE` / `_CHARGE_TABLE` and will be skipped;
  and the predicted trainable percentage with the reasons if it is below ~80%.
* **Ruleset rationale** — where the game sits relative to `HSF2`, `SFA3` and
  `SFIII3` and why, field by field for the ones that matter (`dp_double_tap`,
  `lenient_diagonals`, `charge_ms`, `negative_edge`, …), which characters are
  charge characters, the headline quirk, and a proposed `Ruleset(...)` call.
* **Test seeds** — a few characters worth covering, the shared `harness.py`
  scripts that apply to each, and the move each should produce — ideally one
  that differs from what the same script gives in another game.

## Verifying

```bash
.venv/bin/python .claude/skills/game-brief/verify-brief.py [game ...]
```

* every required `##` section is present;
* for a game with a parser, every character the parser finds in the full guide
  is named somewhere in the brief;
* for a game whose roster JSON exists, the brief's `predicted_trainable` is
  printed next to the real figure and must be within 15 points.

A game with no parser yet only gets the structural checks — read that brief
yourself before trusting it.

If you change the prompt in `make-brief.sh`, re-run `--force` on `hsf2`, `sfa3`
and `sfiii3` (all three have parsers and rosters) and check the verifier still
passes and the briefs still read well.
