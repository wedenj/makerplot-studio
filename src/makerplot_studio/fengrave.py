"""Run F-Engrave in batch mode."""

from __future__ import annotations

import subprocess
from pathlib import Path


class FEngraveError(RuntimeError):
    pass


def run_fengrave_batch(
    fengrave_exe: Path,
    settings_file: Path,
    makerplot_dir: Path,
    *,
    text: str | None = None,
    image: Path | None = None,
) -> str:
    if not fengrave_exe.is_file():
        raise FEngraveError(f"F-Engrave not found: {fengrave_exe}")
    if not settings_file.is_file():
        raise FEngraveError(f"Settings file not found: {settings_file}")

    cmd = [
        str(fengrave_exe),
        "-b",
        "-g",
        str(settings_file),
        "-d",
        str(makerplot_dir),
    ]

    if text is not None:
        cmd.extend(["-t", text])
    elif image is not None:
        if not image.is_file():
            raise FEngraveError(f"Image not found: {image}")
        cmd.extend(["-f", str(image)])
    else:
        raise FEngraveError("Provide either text or image input.")

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(fengrave_exe.parent),
    )

    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        raise FEngraveError(f"F-Engrave failed (exit {result.returncode}): {detail}")

    gcode = result.stdout
    if not gcode.strip():
        raise FEngraveError("F-Engrave produced empty G-code output.")
    return gcode
