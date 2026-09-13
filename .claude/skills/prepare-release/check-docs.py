"""Mechanical checks on the documentation and the app's own text.

Everything here is something a machine can be sure about: a path that does not
exist, an identifier that was renamed, a flag that was removed, a percentage
that no longer matches the data. Judgement calls - whether a section still
earns its place, whether the app says it better - are in SKILL.md and are for a
person.

Two severities. ``FAIL`` is wrong and blocks; ``LOOK`` is a smell that is
usually fine, printed so it gets a glance. Only failures set the exit code.

Run from the repository root: ``.venv/bin/python .claude/skills/prepare-release/check-docs.py``
"""

import json
import re
import subprocess  # ruff: ignore[suspicious-subprocess-import] - only to read our own --help
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DOCS = ["README.md", "CLAUDE.md", *sorted(str(p.relative_to(ROOT)) for p in (ROOT / "docs").glob("*.md"))]
SOURCE_DIRS = ["src", "tests", "scripts"]

IGNORED_PATHS = {"config.json", "glyphnames.json"}
"""Named on purpose but gitignored or generated, so never on disk."""

NOT_OUR_CODE = {"repeat_delay"}
"""Backticked names that belong to somebody else - a compositor setting here."""

MODULES = ("motioninput_tui", "motioninput_tui_datagen", "motioninput_tui_guides")
"""The three entry points, each checked against its own ``--help``."""

THIRD_PARTY_FLAGS = {"--python", "--force", "--all-groups", "--group", "--fix"}
"""Flags of tools the docs tell you to run: uv, pipx, ruff."""

failures: list[str] = []
looks: list[str] = []


def fail(where: str, message: str) -> None:
    failures.append(f"{where}: {message}")


def look(where: str, message: str) -> None:
    looks.append(f"{where}: {message}")


def _source_words() -> set[str]:
    """Every bare word in the source, for spotting a renamed identifier."""
    words: set[str] = set()
    for directory in SOURCE_DIRS:
        for path in (ROOT / directory).rglob("*"):
            if path.suffix in {".py", ".sh"} and path.is_file():
                words.update(re.findall(r"\w+", path.read_text(encoding="utf-8", errors="replace")))
    return words


def _help_text(module: str) -> str:
    result = subprocess.run(  # ruff: ignore[subprocess-without-shell-equals-true] - fixed arguments, no shell
        [sys.executable, "-m", module, "--help"], capture_output=True, text=True, cwd=ROOT, check=False
    )
    return result.stdout


def check_paths() -> None:
    """Every repository path a doc names should exist."""
    pattern = re.compile(
        r"[`(]((?:src|tests|docs|scripts|references|\.claude)/[\w./-]+|[\w-]+\.(?:py|sh|json|toml))[`)]"
    )
    for doc in DOCS:
        for name in sorted(set(pattern.findall((ROOT / doc).read_text()))):
            if (ROOT / name).exists():
                continue
            # A bare filename is shorthand; accept it if the repo has one.
            if "/" not in name and any(ROOT.glob(f"**/{name}")):
                continue
            # Gitignored or generated files are named on purpose.
            if name in IGNORED_PATHS or name.startswith(("docs/_build", "src/anniversary")):
                continue
            fail(doc, f"names {name}, which does not exist")


def check_identifiers(words: set[str]) -> None:
    """Every code name a doc puts in backticks should still be in the source."""
    pattern = re.compile(r"`([A-Za-z_][\w.]*)`")
    for doc in DOCS:
        if doc == "docs/sfiii3-from-the-decomp.md":
            continue  # Mostly C identifiers from another repository.
        for name in sorted(set(pattern.findall((ROOT / doc).read_text()))):
            if name.endswith((".md", ".py", ".json", ".txt", ".sh", ".toml", ".c")):
                continue
            looks_like_code = "_" in name or "." in name or re.match(r"^[A-Z][a-z]+[A-Z]", name)
            if not looks_like_code:
                continue
            if name in NOT_OUR_CODE:
                continue
            unknown = [part for part in name.split(".") if part and part not in words]
            if unknown:
                fail(doc, f"`{name}` is not in the source ({', '.join(unknown)})")


def check_cli() -> None:
    """Documented flags must exist *on the entry point being invoked*.

    Per entry point matters: the guide fetcher has a ``--game`` and the trainer
    no longer does, so checking against the union would let a stale trainer
    command through. Only commands count - prose is free to name a flag that
    was removed, which is how CLAUDE.md explains why it was.
    """
    helps = {module: _help_text(module) for module in MODULES}

    documented: set[str] = set()
    for doc in DOCS:
        for line in _command_lines((ROOT / doc).read_text()):
            module = _invoked_module(line)
            if module is None:
                continue
            for flag in re.findall(r"(?<![\w-])--[a-z][a-z0-9-]*", line):
                if module == "motioninput_tui":
                    documented.add(flag)
                if flag not in helps[module] and flag not in THIRD_PARTY_FLAGS:
                    fail(doc, f"a command runs `{line.strip()}` but {module} has no {flag}")

    real = set(re.findall(r"(?<![\w-])--[a-z][a-z0-9-]*", helps["motioninput_tui"]))
    for flag in sorted(real - documented - {"--help"}):
        look("docs", f"the trainer has {flag} but no documented command uses it")


def _invoked_module(line: str) -> str | None:
    """Which entry point a command line runs, or None if it is somebody else's."""
    for module in ("motioninput_tui_datagen", "motioninput_tui_guides"):
        if module in line:
            return module
    if re.search(r"(^|\s)(motioninput-tui|python -m motioninput_tui|-m motioninput_tui)(\s|$)", line):
        return "motioninput_tui"
    return None


def _command_lines(text: str) -> list[str]:
    """Lines that actually run something, from fenced blocks and inline spans."""
    lines: list[str] = []
    for block in re.findall(r"```(?:bash|console|shell)\n(.*?)```", text, re.DOTALL):
        lines += [line for line in block.splitlines() if line.strip() and not line.lstrip().startswith("#")]
    runs = re.compile(r"(motioninput-tui|python -m |uv |pipx )")
    lines += [span for span in re.findall(r"`([^`]+)`", text) if runs.match(span)]
    return lines


def check_statistics() -> None:
    """A percentage in the docs should be one the rosters actually produce.

    A range (``78-89%``) only has to bracket some real rate; a bare figure has
    to be one, since that is a claim about a specific roster.
    """
    rates = {}
    for path in sorted((ROOT / "src/motioninput_tui/games/data").glob("*.json")):
        characters = json.loads(path.read_text())["characters"]
        moves = sum(len(c["moves"]) for c in characters)
        trainable = sum(1 for c in characters for m in c["moves"] if m.get("motion"))
        rates[path.stem] = round(100 * trainable / moves) if moves else 0
    real = set(rates.values())

    for doc in DOCS:
        text = (ROOT / doc).read_text()
        ranges = [(int(low), int(high)) for low, high in re.findall(r"\b(\d{2})-(\d{2})%", text)]
        for low, high in ranges:
            if not any(low <= rate <= high for rate in real):
                look(doc, f"quotes {low}-{high}%, which brackets no roster ({sorted(real)})")
        spanned = {n for low, high in ranges for n in (low, high)}
        for quoted in {int(n) for n in re.findall(r"\b(\d{2})%", text)} - spanned:
            if quoted not in real:
                look(doc, f"quotes {quoted}%, which is not a current trainable rate ({sorted(real)})")


def check_in_app_text() -> None:
    """The app is the documentation now, so its own strings have to be right."""
    sys.path.insert(0, str(ROOT / "src"))
    from motioninput_tui.games.rulesets import GAME_SPECS  # ruff: ignore[import-outside-top-level] - importing the app is the check
    from motioninput_tui.settings import SETTINGS  # ruff: ignore[import-outside-top-level] - importing the app is the check

    playable = [spec for spec in GAME_SPECS.values() if spec.reference]
    # Counting words go stale every time a game is added; the picker shows note 0.
    stale = re.compile(r"\bof the (?:two|three|four|five|six)\b|\bboth games\b|\bthe other two\b", re.IGNORECASE)
    for spec in playable:
        if not spec.notes:
            fail("rulesets.py", f"{spec.key} has no notes, so the picker shows nothing about it")
            continue
        for note in spec.notes:
            if not note.strip():
                fail("rulesets.py", f"{spec.key} has an empty note")
            if stale.search(note):
                fail("rulesets.py", f"{spec.key} note counts the roster, which goes stale: {note!r}")

    for setting in SETTINGS:
        if not setting.name.strip() or not setting.detail.strip():
            fail("settings.py", f"{setting.attribute} needs both a name and a detail; the panes print them")

    _check_bindings()


def _check_bindings() -> None:
    """A binding with no description is invisible in the Footer."""
    for path in sorted((ROOT / "src/motioninput_tui/tui").rglob("*.py")):
        for match in re.finditer(r'Binding\(\s*"([^"]+)"\s*,\s*"([^"]+)"\s*(.*?)\)', path.read_text(), re.DOTALL):
            key, _action, rest = match.groups()
            described = re.match(r'\s*,\s*"[^"]+"', rest)
            if not described and "show=False" not in rest:
                fail(str(path.relative_to(ROOT)), f'binding "{key}" has no description and is not hidden')


def check_duplication() -> None:
    """Docs that re-list what a menu already draws."""
    from motioninput_tui.notation_styles import STYLES  # ruff: ignore[import-outside-top-level] - importing the app is the check
    from motioninput_tui.settings import SETTINGS  # ruff: ignore[import-outside-top-level] - importing the app is the check

    names = [setting.name for setting in SETTINGS]
    style_names = [style.name for family in STYLES.values() for style in family]
    for doc in DOCS:
        if doc == "CLAUDE.md":
            continue  # It explains the rule, so it names the things.
        text = (ROOT / doc).read_text()
        tables = [line for line in text.splitlines() if line.startswith("|")]
        joined = "\n".join(tables)
        if sum(name in joined for name in names) >= 2:  # ruff: ignore[magic-value-comparison] - two rows is enough to be a table
            look(doc, "a table lists the settings; the setup pane and ctrl+b already describe each one")
        if sum(name in joined for name in style_names) >= 2:  # ruff: ignore[magic-value-comparison] - two rows is enough to be a table
            look(doc, "a table lists notation styles; the ctrl+b menu previews every one of them")
        if len(set(re.findall(r"`ctrl\+[a-z]`", text))) >= 4:  # ruff: ignore[magic-value-comparison] - two rows is enough to be a table
            look(doc, "several ctrl+ bindings are listed; every screen has a Footer showing them")


def main() -> int:
    """Run every check and report."""
    words = _source_words()
    check_paths()
    check_identifiers(words)
    check_cli()
    check_statistics()
    check_in_app_text()
    check_duplication()

    for line in failures:
        print(f"FAIL  {line}")
    for line in looks:
        print(f"LOOK  {line}")
    if not failures and not looks:
        print("Documentation and in-app text check out.")
    elif not failures:
        print(f"\nNothing wrong; {len(looks)} to glance at.")
    else:
        print(f"\n{len(failures)} to fix, {len(looks)} to glance at.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
