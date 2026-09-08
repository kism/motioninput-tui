"""Work out which terminal we are in and whether it will keep up.

Input latency matters here: the trainer judges motions on wall clock timing, so
a terminal that takes 30ms to paint a frame will make clean inputs look late.
GPU accelerated terminals are comfortably fast; some of the older or
web-technology based ones are not.
"""

import os
from dataclasses import dataclass
from enum import StrEnum


class Speed(StrEnum):
    """How well a terminal is expected to cope."""

    FAST = "fast"
    OK = "ok"
    SLOW = "slow"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class TerminalInfo:
    """What we managed to work out about the host terminal."""

    name: str
    speed: Speed
    detail: str = ""
    multiplexer: str = ""
    remote: bool = False

    @property
    def should_warn(self) -> bool:
        """Whether the user deserves a heads-up before training."""
        return self.speed in {Speed.SLOW, Speed.UNKNOWN} or bool(self.multiplexer) or self.remote

    def warning(self) -> str:
        """A one line explanation, empty when there is nothing to say."""
        parts = []
        if self.speed is Speed.SLOW:
            parts.append(f"{self.name} is known to have high input latency; motions may read as late.")
        elif self.speed is Speed.UNKNOWN:
            parts.append("Could not identify this terminal, so its input latency is unknown.")
        if self.multiplexer:
            parts.append(f"Running under {self.multiplexer}, which adds a frame or two of latency.")
        if self.remote:
            parts.append("Session looks remote (SSH); network latency will affect timing.")
        if parts:
            parts.append("For best results use alacritty, foot, ghostty, kitty or wezterm locally.")
        return " ".join(parts)


# Ordered checks: the first environment variable that matches wins.
_ENV_TERMINALS: tuple[tuple[str, str, Speed], ...] = (
    ("GHOSTTY_RESOURCES_DIR", "Ghostty", Speed.FAST),
    ("GHOSTTY_BIN_DIR", "Ghostty", Speed.FAST),
    ("ALACRITTY_WINDOW_ID", "Alacritty", Speed.FAST),
    ("ALACRITTY_SOCKET", "Alacritty", Speed.FAST),
    ("ALACRITTY_LOG", "Alacritty", Speed.FAST),
    ("KITTY_WINDOW_ID", "kitty", Speed.FAST),
    ("KITTY_PID", "kitty", Speed.FAST),
    ("WEZTERM_PANE", "WezTerm", Speed.FAST),
    ("WEZTERM_EXECUTABLE", "WezTerm", Speed.FAST),
    ("FOOT_PID", "foot", Speed.FAST),
    ("CONTOUR_PROFILE", "Contour", Speed.FAST),
    ("RIO_CONFIG", "Rio", Speed.FAST),
    ("KONSOLE_VERSION", "Konsole", Speed.OK),
    ("VTE_VERSION", "VTE based terminal", Speed.OK),
    ("WT_SESSION", "Windows Terminal", Speed.OK),
    ("TERMUX_VERSION", "Termux", Speed.SLOW),
)

_TERM_PROGRAMS: dict[str, tuple[str, Speed]] = {
    "ghostty": ("Ghostty", Speed.FAST),
    "wezterm": ("WezTerm", Speed.FAST),
    "alacritty": ("Alacritty", Speed.FAST),
    "kitty": ("kitty", Speed.FAST),
    "foot": ("foot", Speed.FAST),
    "rio": ("Rio", Speed.FAST),
    "iterm.app": ("iTerm2", Speed.OK),
    "apple_terminal": ("Terminal.app", Speed.SLOW),
    "vscode": ("VS Code integrated terminal", Speed.SLOW),
    "hyper": ("Hyper", Speed.SLOW),
    "tabby": ("Tabby", Speed.SLOW),
    "warpterminal": ("Warp", Speed.OK),
    "warp": ("Warp", Speed.OK),
}

_TERM_VALUES: tuple[tuple[str, str, Speed], ...] = (
    ("alacritty", "Alacritty", Speed.FAST),
    ("foot", "foot", Speed.FAST),
    ("xterm-kitty", "kitty", Speed.FAST),
    ("wezterm", "WezTerm", Speed.FAST),
    ("contour", "Contour", Speed.FAST),
    ("rio", "Rio", Speed.FAST),
    ("ghostty", "Ghostty", Speed.FAST),
    ("st-", "st", Speed.FAST),
    ("rxvt", "urxvt", Speed.OK),
    ("konsole", "Konsole", Speed.OK),
    ("xterm", "xterm", Speed.OK),
    ("linux", "Linux console", Speed.OK),
)


def detect(environ: dict[str, str] | None = None) -> TerminalInfo:
    """Identify the host terminal and rate its likely input latency."""
    env = dict(os.environ if environ is None else environ)

    multiplexer = ""
    if env.get("TMUX"):
        multiplexer = "tmux"
    elif env.get("STY"):
        multiplexer = "GNU screen"
    elif env.get("TERM", "").startswith("screen") and not env.get("TERM_PROGRAM"):
        multiplexer = "screen or tmux"

    remote = bool(env.get("SSH_CONNECTION") or env.get("SSH_TTY") or env.get("SSH_CLIENT"))

    name, speed, detail = _identify(env)
    return TerminalInfo(name=name, speed=speed, detail=detail, multiplexer=multiplexer, remote=remote)


def _identify(env: dict[str, str]) -> tuple[str, Speed, str]:
    for variable, name, speed in _ENV_TERMINALS:
        if env.get(variable):
            return name, speed, f"detected via ${variable}"

    program = env.get("TERM_PROGRAM", "").strip().lower()
    if program in _TERM_PROGRAMS:
        name, speed = _TERM_PROGRAMS[program]
        return name, speed, "detected via $TERM_PROGRAM"

    term = env.get("TERM", "").strip().lower()
    for needle, name, speed in _TERM_VALUES:
        if needle in term:
            return name, speed, "detected via $TERM"

    if program:
        return program, Speed.UNKNOWN, "unrecognised $TERM_PROGRAM"
    if term:
        return term, Speed.UNKNOWN, "unrecognised $TERM"
    return "unknown terminal", Speed.UNKNOWN, "no $TERM or $TERM_PROGRAM"
