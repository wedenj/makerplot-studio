"""Directional backlash compensation for G0/G1 toolpaths."""

from __future__ import annotations

import re
from dataclasses import dataclass


WORD_RE = re.compile(r"([A-Z])([-+]?(?:\d+(?:\.\d*)?|\.\d+))")


@dataclass
class Position:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0


def _strip_comments(line: str) -> str:
    result = []
    depth = 0
    for ch in line:
        if ch == "(":
            depth += 1
            continue
        if ch == ")":
            depth = max(0, depth - 1)
            continue
        if depth == 0:
            result.append(ch)
    code = "".join(result)
    if ";" in code:
        code = code.split(";", 1)[0]
    return code.strip()


def _parse_words(line: str) -> dict[str, float]:
    clean = _strip_comments(line).upper().replace(" ", "")
    return {m.group(1): float(m.group(2)) for m in WORD_RE.finditer(clean)}


def _backlash_offset(delta: float, amount: float) -> float:
    if delta > 0:
        return -amount
    if delta < 0:
        return amount
    return 0.0


def apply_backlash(
    content: str,
    backlash_x: float = 0.3,
    backlash_y: float = 0.3,
    backlash_z: float = 0.3,
) -> str:
    """Apply MakerPlot-style backlash compensation, preserving mm units."""
    pos = Position()
    out: list[str] = []

    for raw in content.splitlines():
        line = raw.rstrip()
        if not line.strip():
            continue

        code = _strip_comments(line)
        if not code:
            continue

        words = _parse_words(line)
        if "G" not in words:
            out.append(code)
            continue

        gcode = int(words["G"])
        if gcode in (20, 21, 90, 91, 17):
            out.append(code)
            continue

        if gcode not in (0, 1):
            out.append(code)
            continue

        target = Position(
            words.get("X", pos.x),
            words.get("Y", pos.y),
            words.get("Z", pos.z),
        )
        dx = target.x - pos.x
        dy = target.y - pos.y
        dz = target.z - pos.z

        ax = target.x + _backlash_offset(dx, backlash_x)
        ay = target.y + _backlash_offset(dy, backlash_y)
        az = target.z + _backlash_offset(dz, backlash_z)

        parts = [f"G{gcode}"]
        if "X" in words:
            parts.append(f"X{ax:.4f}")
        if "Y" in words:
            parts.append(f"Y{ay:.4f}")
        if "Z" in words:
            parts.append(f"Z{az:.4f}")
        if "F" in words:
            feed = words["F"]
            parts.append(f"F{feed:.1f}" if feed != int(feed) else f"F{int(feed)}")

        out.append(" ".join(parts))
        pos = Position(ax, ay, az)

    return "\n".join(out) + "\n"
