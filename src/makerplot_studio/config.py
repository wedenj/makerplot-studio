"""Persistent user configuration."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from makerplot_studio.paths import PROJECT_ROOT, SETTINGS_DIR, SAMPLES_DIR


CONFIG_FILENAME = ".makerplot-studio.json"


@dataclass
class AppConfig:
    # Optional MakerPlot kit folder (fallback tools + extra sample files)
    makerplot_dir: str = ""
    backlash_x: float = 0.3
    backlash_y: float = 0.3
    backlash_z: float = 0.3
    baud_rate: int = 115200
    last_com_port: str = ""
    text_settings: str = ""
    image_settings: str = ""
    java_path: str = ""
    ugs_jar_path: str = ""

    def resolved_makerplot(self) -> Path | None:
        if self.makerplot_dir:
            path = Path(self.makerplot_dir)
            if path.is_dir():
                return path
        return None

    def resolved_text_settings(self) -> Path:
        if self.text_settings:
            return Path(self.text_settings)
        bundled = SETTINGS_DIR / "text_settings.txt"
        if bundled.is_file():
            return bundled
        kit = self.resolved_makerplot()
        if kit:
            kit_settings = kit / "f-engrave settings.txt"
            if kit_settings.is_file():
                return kit_settings
        return bundled

    def resolved_image_settings(self) -> Path:
        if self.image_settings:
            return Path(self.image_settings)
        bundled = SETTINGS_DIR / "image_settings.txt"
        if bundled.is_file():
            return bundled
        kit = self.resolved_makerplot()
        if kit:
            return kit / "f-engrave settings.txt"
        return bundled

    def default_sample_image(self) -> Path | None:
        sample = SAMPLES_DIR / "monkey.png"
        if sample.is_file():
            return sample
        kit = self.resolved_makerplot()
        if kit:
            kit_sample = kit / "monkey.png"
            if kit_sample.is_file():
                return kit_sample
        return None


def config_path(project_root: Path | None = None) -> Path:
    root = project_root or PROJECT_ROOT
    return root / CONFIG_FILENAME


def load_config(project_root: Path | None = None) -> AppConfig:
    path = config_path(project_root)
    if not path.is_file():
        return AppConfig()
    data = json.loads(path.read_text(encoding="utf-8"))
    return AppConfig(**{k: v for k, v in data.items() if k in AppConfig.__dataclass_fields__})


def save_config(cfg: AppConfig, project_root: Path | None = None) -> None:
    path = config_path(project_root)
    path.write_text(json.dumps(asdict(cfg), indent=2), encoding="utf-8")
