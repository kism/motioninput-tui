"""Repo-wide invariants: versioning, where a game is named, and which way imports point."""

import ast
import tomllib
from pathlib import Path

from motioninput_tui import PROGRAM_NAME, PROGRAM_REPO_URL, PROGRAM_VERSION, constants
from motioninput_tui.games.rulesets import GAME_SPECS
from motioninput_tui_datagen.__main__ import PARSERS
from motioninput_tui_datagen.names import OVERRIDES
from motioninput_tui_guides.catalog import load_guides


def test_version_pyproject() -> None:
    """Verify version in pyproject.toml matches package version."""
    with Path("pyproject.toml").open("rb") as f:
        pyproject_toml = tomllib.load(f)
    assert pyproject_toml.get("project", {}).get("version", None) == PROGRAM_VERSION


def test_version_lock() -> None:
    """Verify version in uv.lock matches package version."""
    with Path("uv.lock").open("rb") as f:
        uv_lock = tomllib.load(f)

    found_version = False
    for package in uv_lock.get("package", []):
        if package.get("name") == PROGRAM_NAME:
            assert package.get("version") == PROGRAM_VERSION
            found_version = True
            break

    assert found_version, f"{PROGRAM_NAME} not found in uv.lock"


def test_repo_url() -> None:
    """Verify repo URL is correct."""
    with Path("pyproject.toml").open("rb") as f:
        pyproject_toml = tomllib.load(f)
    assert pyproject_toml.get("project", {}).get("urls", {}).get("Repository", None) == PROGRAM_REPO_URL


def test_get_version_str_with_git(tmp_path, monkeypatch) -> None:
    """Verify branch and commit are read from a git dir next to the package."""
    git_dir = tmp_path / ".git"
    (git_dir / "logs").mkdir(parents=True)
    (git_dir / "logs" / "HEAD").write_text("0000000 abcdef1234567 Someone <a@b.c> 0 +0000\tcommit: hello\n")
    (git_dir / "HEAD").write_text("ref: refs/heads/my-branch\n")
    monkeypatch.setattr(constants, "__file__", str(tmp_path / "pkg" / "constants.py"))

    assert constants._get_version_str() == f"{PROGRAM_NAME} v{PROGRAM_VERSION}-my-branch/abcdef1"


def test_get_version_str_no_git(tmp_path, monkeypatch) -> None:
    """Verify version string without a git dir."""
    monkeypatch.setattr(constants, "__file__", str(tmp_path / "pkg" / "constants.py"))

    assert constants._get_version_str() == f"{PROGRAM_NAME} v{PROGRAM_VERSION}"


def test_game_keys_agree() -> None:
    """A game with a roster is named in the same way everywhere it appears.

    The key is spelled out in a handful of tables that nothing else joins up, so
    a game added to one and missed in another is caught here rather than at the
    next datagen run. The guide catalogue is allowed to run ahead: a guide can be
    fetched before the game is added to the trainer.
    """
    generated = {key for key, spec in GAME_SPECS.items() if spec.reference}

    assert generated == set(PARSERS), "every game with a reference guide needs a parser, and vice versa"
    assert generated <= {guide.key for guide in load_guides()}, "a game whose guide is not in the catalogue"
    assert set(OVERRIDES) <= generated, "a name override for a game that is not generated"


# `engine` is what the matchers live in, and it has to stay answerable to every
# game rather than to any one of them. CLAUDE.md puts it as: the recogniser
# takes moves through a Protocol rather than importing `games`. Nothing stops
# that quietly rotting except checking.
#
# A `TYPE_CHECKING` import is allowed and `session.py` uses one: it is the layer
# that binds a Game to a session, so it needs the names, and an annotation
# cannot change what the matchers do. A runtime import could.
ENGINE = Path("src/motioninput_tui/engine")
GAME_KEYS = ("sfiii3", "hsf2", "sfa3", "kof98", "kof2001", "usfiv", "ssii", "ssvsp", "lb2")


def type_checking_only(tree: ast.AST) -> set[int]:
    """Nodes sitting under ``if TYPE_CHECKING:``, which never run."""
    guarded: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.If) and "TYPE_CHECKING" in ast.dump(node.test):
            guarded.update(id(child) for child in ast.walk(node))
    return guarded


def runtime_imports(source: Path) -> set[str]:
    """Every module a file imports for real, annotations aside."""
    tree = ast.parse(source.read_text(encoding="utf-8"))
    guarded = type_checking_only(tree)
    found: set[str] = set()
    for node in ast.walk(tree):
        if id(node) in guarded:
            continue
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            found.add(node.module)
    return found


def test_the_engine_does_not_import_games_or_the_interface() -> None:
    """A game's rules have to reach the matchers as a Ruleset value, never as an
    import: that is what stops one game's findings quietly becoming the engine's
    behaviour for all of them."""
    offenders = {
        f"{source.name} imports {module}"
        for source in ENGINE.glob("*.py")
        for module in runtime_imports(source)
        if module.startswith(("motioninput_tui.games", "motioninput_tui.tui"))
    }
    assert not offenders


def test_no_game_is_named_in_engine_code() -> None:
    """Game names belong in docstrings, where they say which game a Ruleset
    field is describing, and in `games/rulesets.py`, where the per-game figures
    and their provenance live. A game key in engine code would mean the matchers
    had started branching on one."""
    offenders = []
    for source in ENGINE.glob("*.py"):
        tree = ast.parse(source.read_text(encoding="utf-8"))
        docstrings = {
            ast.get_docstring(node, clean=False)
            for node in ast.walk(tree)
            if isinstance(node, ast.Module | ast.ClassDef | ast.FunctionDef)
        }
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value not in docstrings:
                offenders += [f"{source.name}:{node.lineno} names {key}" for key in GAME_KEYS if key in node.value]
    assert not offenders
