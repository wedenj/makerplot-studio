"""Resolve bundled tools (Java, UGS Classic, F-Engrave)."""

from __future__ import annotations

import shutil
import urllib.request
import zipfile
from pathlib import Path

from makerplot_studio.config import UGS_RELEASE_URL


PROJECT_ROOT = Path(__file__).resolve().parents[2]
VENDOR_DIR = PROJECT_ROOT / "vendor"
UGS_DIR = VENDOR_DIR / "ugs-classic" / "UniversalGcodeSender"
UGS_JAR = UGS_DIR / "UniversalGcodeSender.jar"
UGS_ZIP = VENDOR_DIR / "UniversalGcodeSender.zip"


def find_java(cfg_java: str = "", makerplot_dir: Path | None = None) -> Path | None:
    if cfg_java:
        path = Path(cfg_java)
        if path.is_file():
            return path

    candidates: list[Path] = []
    if makerplot_dir:
        candidates.extend(
            makerplot_dir.parent.glob("**/jdk/**/bin/java.exe")
        )
        candidates.extend(
            makerplot_dir.glob("win64-ugs-platform-app-*/ugsplatform-win/jdk/**/bin/java.exe")
        )

    candidates.append(
        Path(r"d:\Bambu\MakerPlot\GoogleDrive")
        / "win64-ugs-platform-app-2.1.18"
        / "ugsplatform-win"
        / "jdk"
        / "jdk-17.0.8.1+1-jre"
        / "bin"
        / "java.exe"
    )

    which = shutil.which("java")
    if which:
        candidates.append(Path(which))

    for path in candidates:
        if path.is_file():
            return path
    return None


def find_fengrave(makerplot_dir: Path) -> Path:
    return makerplot_dir / "F-Engrave-1.78_win" / "f-engrave_c.exe"


def ensure_ugs_jar(cfg_jar: str = "", on_progress=None) -> Path:
    if cfg_jar:
        path = Path(cfg_jar)
        if path.is_file():
            return path

    if UGS_JAR.is_file():
        return UGS_JAR

    UGS_DIR.mkdir(parents=True, exist_ok=True)
    VENDOR_DIR.mkdir(parents=True, exist_ok=True)

    if not UGS_ZIP.is_file():
        if on_progress:
            on_progress("Downloading UGS Classic…")
        urllib.request.urlretrieve(UGS_RELEASE_URL, UGS_ZIP)

    if on_progress:
        on_progress("Extracting UGS Classic…")

    with zipfile.ZipFile(UGS_ZIP, "r") as zf:
        for entry in zf.namelist():
            if entry.endswith("UniversalGcodeSender.jar"):
                zf.extract(entry, VENDOR_DIR / "extract-tmp")
                extracted = VENDOR_DIR / "extract-tmp" / entry
                extracted.replace(UGS_JAR)
                break

    shutil.rmtree(VENDOR_DIR / "extract-tmp", ignore_errors=True)

    if not UGS_JAR.is_file():
        raise FileNotFoundError(
            "Could not locate UniversalGcodeSender.jar after download. "
            f"Expected at {UGS_JAR}"
        )
    return UGS_JAR
