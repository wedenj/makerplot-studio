"""Remove GRBL-incompatible commands from plotter G-code."""

from __future__ import annotations

import re

# Standard GRBL on Arduino does not support these.
SKIP_COMMANDS = {
    "G90.1",
    "G90.0",
    "M3",
    "M4",
    "M5",
    "M7",
    "M8",
    "M9",
}


def _first_word(line: str) -> str:
    clean = line.strip().upper()
    if not clean or clean.startswith("("):
        return ""
    match = re.match(r"^([GMT]\d+(?:\.\d+)?)", clean.replace(" ", ""))
    return match.group(1) if match else ""


def clean_for_grbl(content: str, keep_comments: bool = False) -> str:
    out: list[str] = []
    for raw in content.splitlines():
        line = raw.rstrip()
        if not line.strip():
            continue
        if line.strip().startswith("(") and not keep_comments:
            continue
        cmd = _first_word(line)
        if cmd in SKIP_COMMANDS:
            continue
        out.append(line)
    return "\n".join(out) + "\n"
