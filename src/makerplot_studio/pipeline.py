"""End-to-end prepare pipeline: F-Engrave → backlash → GRBL cleanup."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from makerplot_studio.backlash import apply_backlash
from makerplot_studio.config import AppConfig
from makerplot_studio.fengrave import run_fengrave_batch
from makerplot_studio.gcode_clean import clean_for_grbl
from makerplot_studio.paths import find_fengrave


@dataclass
class PrepareResult:
    raw_path: Path
    ready_path: Path
    line_count: int
    preview: str


def _output_dir(makerplot_dir: Path) -> Path:
    out = makerplot_dir / "Backlash Compensated G-Code"
    out.mkdir(parents=True, exist_ok=True)
    return out


def _safe_slug(name: str) -> str:
    keep = []
    for ch in name:
        if ch.isalnum() or ch in "-_":
            keep.append(ch)
        elif ch.isspace():
            keep.append("_")
    slug = "".join(keep).strip("_")
    return slug or "plot"


def prepare_job(
    cfg: AppConfig,
    *,
    mode: str,
    text: str = "",
    image_path: Path | None = None,
    job_name: str = "",
) -> PrepareResult:
    makerplot = cfg.resolved_makerplot()
    fengrave = find_fengrave(makerplot)

    if mode == "text":
        settings = cfg.resolved_text_settings()
        gcode_raw = run_fengrave_batch(
            fengrave,
            settings,
            makerplot,
            text=text,
        )
        slug = _safe_slug(job_name or text[:24] or "text")
    elif mode == "image":
        settings = cfg.resolved_image_settings()
        if image_path is None:
            raise ValueError("Image path is required for image mode.")
        gcode_raw = run_fengrave_batch(
            fengrave,
            settings,
            makerplot,
            image=image_path,
        )
        slug = _safe_slug(job_name or image_path.stem)
    else:
        raise ValueError(f"Unknown mode: {mode}")

    compensated = apply_backlash(
        gcode_raw,
        backlash_x=cfg.backlash_x,
        backlash_y=cfg.backlash_y,
        backlash_z=cfg.backlash_z,
    )
    ready = clean_for_grbl(compensated)

    out_dir = _output_dir(makerplot)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    ready_path = out_dir / f"{slug}_{timestamp}_ready.ngc"

    ready_path.write_text(ready, encoding="utf-8")

    lines = [ln for ln in ready.splitlines() if ln.strip()]
    preview = "\n".join(lines[:12])
    if len(lines) > 12:
        preview += f"\n… ({len(lines) - 12} more lines)"

    raw_path = out_dir / f"{slug}_{timestamp}_raw.ngc"
    raw_path.write_text(gcode_raw, encoding="utf-8")

    return PrepareResult(
        raw_path=raw_path,
        ready_path=ready_path,
        line_count=len(lines),
        preview=preview,
    )
