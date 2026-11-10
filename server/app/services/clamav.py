from __future__ import annotations

import socket
import struct
from pathlib import Path


class MalwareScanError(RuntimeError):
    pass


def scan_file(path: Path, host: str, port: int, timeout: int) -> None:
    try:
        with socket.create_connection((host, port), timeout=timeout) as connection:
            connection.settimeout(timeout)
            connection.sendall(b"zINSTREAM\0")
            with path.open("rb") as source:
                while block := source.read(1024 * 1024):
                    connection.sendall(struct.pack("!I", len(block)))
                    connection.sendall(block)
            connection.sendall(struct.pack("!I", 0))
            response = b""
            while not response.endswith(b"\0"):
                chunk = connection.recv(4096)
                if not chunk:
                    break
                response += chunk
    except OSError as exc:
        raise MalwareScanError("ClamAV 不可用，已禁止发布") from exc

    result = response.rstrip(b"\0").decode("utf-8", errors="replace")
    if not result.endswith("OK"):
        raise MalwareScanError(f"恶意软件扫描未通过：{result or '无响应'}")
