"""COM port discovery and selection."""

from __future__ import annotations

from dataclasses import dataclass

try:
    import serial.tools.list_ports
except ImportError:  # pragma: no cover
    serial = None  # type: ignore


PREFERRED_KEYWORDS = (
    "arduino",
    "ch340",
    "ch341",
    "usb serial",
    "usb-serial",
    "cp210",
    "ftdi",
    "wch",
    "serial",
)


@dataclass
class SerialPortInfo:
    device: str
    description: str
    hwid: str

    @property
    def label(self) -> str:
        desc = self.description.strip()
        if desc:
            return f"{self.device} — {desc}"
        return self.device


def list_serial_ports() -> list[SerialPortInfo]:
    if serial is None:
        return []
    ports = []
    for p in serial.tools.list_ports.comports():
        ports.append(SerialPortInfo(p.device, p.description or "", p.hwid or ""))
    return sorted(ports, key=lambda x: x.device)


def parse_ugs_port_list(output: str) -> list[str]:
    """Parse UGS CLI `-l` output like: Available ports: [COM3, COM4]."""
    text = output.strip()
    start = text.find("[")
    end = text.find("]")
    if start == -1 or end == -1:
        return []
    inner = text[start + 1 : end]
    return [p.strip() for p in inner.split(",") if p.strip()]


def guess_best_port(
    ports: list[SerialPortInfo],
    ugs_ports: list[str] | None = None,
    last_used: str = "",
) -> str:
    if last_used and any(p.device == last_used for p in ports):
        return last_used

    searchable = ports
    if ugs_ports:
        allowed = set(ugs_ports)
        searchable = [p for p in ports if p.device in allowed] or ports

    for keyword in PREFERRED_KEYWORDS:
        for port in searchable:
            blob = f"{port.description} {port.hwid}".lower()
            if keyword in blob:
                return port.device

    if ugs_ports:
        for device in ugs_ports:
            if any(p.device == device for p in ports):
                return device

    if searchable:
        return searchable[0].device
    if ugs_ports:
        return ugs_ports[0]
    return ""
