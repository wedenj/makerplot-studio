"""Resolve bundled tools (Java, UGS Classic, F-Engrave)."""

from __future__ import annotations

import shutil
import urllib.request
import zipfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
VENDOR_DIR = PROJECT_ROOT / "vendor"
FENGRAVE_DIR = VENDOR_DIR / "f-engrave"
FENGRAVE_EXE = FENGRAVE_DIR / "f-engrave_c.exe"
JRE_JAVA = VENDOR_DIR / "jre" / "bin" / "java.exe"
UGS_DIR = VENDOR_DIR / "ugs-classic" / "UniversalGcodeSender"
UGS_JAR = UGS_DIR / "UniversalGcodeSender.jar"
UGS_ZIP = VENDOR_DIR / "UniversalGcodeSender.zip"
UGS_RELEASE_URL = (
    "https://github.com/winder/Universal-G-Code-Sender/releases/download/"
    "v2.1.23/UniversalGcodeSender.zip"
)
OUTPUT_DIR = PROJECT_ROOT / "output"
SETTINGS_DIR = PROJECT_ROOT / "settings"
SAMPLES_DIR = PROJECT_ROOT / "samples"


def bundled_apps_present() -> bool:
    return FENGRAVE_EXE.is_file() and JRE_JAVA.is_file() and UGS_JAR.is_file()


def find_java(cfg_java: str = "", makerplot_dir: Path | None = None) -> Path | None:
    if cfg_java:
        path = Path(cfg_java)
        if path.is_file():
            return path

    candidates: list[Path] = [JRE_JAVA]

    if makerplot_dir:
        candidates.extend(makerplot_dir.glob("win64-ugs-platform-app-*/ugsplatform-win/jdk/**/bin/java.exe"))
        candidates.extend(makerplot_dir.parent.glob("**/jdk/**/bin/java.exe"))

    which = shutil.which("java")
    if which:
        candidates.append(Path(which))

    for path in candidates:
        if path.is_file():
            return path
    return None


def find_fengrave(makerplot_dir: Path | None = None) -> Path:
    if FENGRAVE_EXE.is_file():
        return FENGRAVE_EXE
    if makerplot_dir:
        kit = makerplot_dir / "F-Engrave-1.78_win" / "f-engrave_c.exe"
        if kit.is_file():
            return kit
    raise FileNotFoundError(
        "F-Engrave not found. Run scripts\\bundle-apps.ps1 to copy it from your MakerPlot kit."
    )


def fengrave_work_dir(makerplot_dir: Path | None = None) -> Path:
    """Directory passed to F-Engrave -d (default paths for relative settings)."""
    if FENGRAVE_EXE.is_file():
        return PROJECT_ROOT
    if makerplot_dir:
        return makerplot_dir
    return PROJECT_ROOT


def ensure_output_dir() -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUT_DIR


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
            "Could not locate UniversalGcodeSender.jar. "
            "Run scripts\\bundle-apps.ps1 or scripts\\setup.ps1."
        )
    return UGS_JAR
