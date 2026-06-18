"""UGS Classic CLI integration."""

from __future__ import annotations

import subprocess
from pathlib import Path

from makerplot_studio.com_ports import parse_ugs_port_list


class UgsCliError(RuntimeError):
    pass


def build_ugs_command(
    java: Path,
    jar: Path,
    *,
    port: str,
    baud: int,
    gcode_file: Path,
    reset_alarm: bool = True,
    print_progress: bool = True,
) -> list[str]:
    cmd = [
        str(java),
        "-Xmx256m",
        "-cp",
        str(jar),
        "com.willwinder.ugs.cli.TerminalClient",
        "--controller",
        "GRBL",
        "--port",
        port,
        "--baud",
        str(baud),
        "--driver",
        "JSERIALCOMM",
    ]
    if reset_alarm:
        cmd.append("--reset-alarm")
    if print_progress:
        cmd.append("--print-progressbar")
    cmd.extend(["--file", str(gcode_file)])
    return cmd


def list_ports_via_ugs(java: Path, jar: Path) -> list[str]:
    cmd = [
        str(java),
        "-cp",
        str(jar),
        "com.willwinder.ugs.cli.TerminalClient",
        "-l",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise UgsCliError(result.stderr or result.stdout or "Failed to list ports")
    return parse_ugs_port_list(result.stdout)


def send_gcode(
    java: Path,
    jar: Path,
    *,
    port: str,
    baud: int,
    gcode_file: Path,
    on_output=None,
) -> None:
    if not gcode_file.is_file():
        raise UgsCliError(f"G-code file not found: {gcode_file}")

    cmd = build_ugs_command(
        java,
        jar,
        port=port,
        baud=baud,
        gcode_file=gcode_file,
    )

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    assert proc.stdout is not None
    for line in proc.stdout:
        if on_output:
            on_output(line.rstrip())
    code = proc.wait()
    if code != 0:
        raise UgsCliError(f"UGS CLI exited with code {code}")
