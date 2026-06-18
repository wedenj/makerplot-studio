"""Persistent user configuration."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


CONFIG_FILENAME = ".makerplot-studio.json"
DEFAULT_MAKERPLOT = Path(r"d:\Bambu\MakerPlot\GoogleDrive")
UGS_RELEASE_URL = (
    "https://github.com/winder/Universal-G-Code-Sender/releases/download/"
    "v2.1.23/UniversalGcodeSender.zip"
)


@dataclass
class AppConfig:
    makerplot_dir: str = str(DEFAULT_MAKERPLOT)
    backlash_x: float = 0.3
    backlash_y: float = 0.3
    backlash_z: float = 0.3
    baud_rate: int = 115200
    last_com_port: str = ""
    text_settings: str = ""
    image_settings: str = ""
    java_path: str = ""
    ugs_jar_path: str = ""

    def resolved_makerplot(self) -> Path:
        return Path(self.makerplot_dir)

    def resolved_text_settings(self) -> Path:
        if self.text_settings:
            return Path(self.text_settings)
        return self.resolved_makerplot() / "f-engrave settings.txt"

    def resolved_image_settings(self) -> Path:
        if self.image_settings:
            return Path(self.image_settings)
        bundled = Path(__file__).resolve().parents[2] / "settings" / "image_settings.txt"
        if bundled.is_file():
            return bundled
        return self.resolved_makerplot() / "f-engrave settings.txt"


def config_path(project_root: Path | None = None) -> Path:
    root = project_root or Path(__file__).resolve().parents[2]
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
