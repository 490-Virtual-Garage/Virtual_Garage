#!/usr/bin/env python3
"""Tiny TCP client for the ELM327 emulator.

Start the emulator first, for example:
    python3 -m elm -s car -n 35000

Then run this script:
    python3 elm_client.py
"""

from __future__ import annotations

import argparse
import re
import socket
import time
from typing import Optional


DEFAULT_COMMANDS = [
    "ATI",   # Adapter identification
    "010C",  # Engine RPM
    "010D",  # Vehicle speed
    "0105",  # Coolant temperature
    "03",    # Stored diagnostic trouble codes (DTCs)
]


def send_command(sock: socket.socket, command: str, timeout: float) -> str:
    """Send one ELM command and read until the emulator's '>' prompt."""
    sock.sendall((command.strip() + "\r").encode("ascii"))

    reply = bytearray()
    sock.settimeout(timeout)
    while b">" not in reply:
        chunk = sock.recv(1024)
        if not chunk:
            break
        reply.extend(chunk)

    return reply.decode("ascii", errors="replace").replace("\r", "\n").strip()


def response_bytes(reply: str) -> list[int]:
    """Extract byte-looking values from a raw ELM reply."""
    return [int(value, 16) for value in re.findall(r"(?<![0-9A-Fa-f])[0-9A-Fa-f]{2}(?![0-9A-Fa-f])", reply)]


def explain(command: str, reply: str) -> Optional[str]:
    """Decode a few common Mode 01 replies so the demo is easier to understand."""
    values = response_bytes(reply)

    try:
        index = next(i for i in range(len(values) - 1) if values[i] == 0x41)
        pid = values[index + 1]
        data = values[index + 2 :]
    except (StopIteration, IndexError):
        return None

    if pid == 0x0C and len(data) >= 2:
        rpm = ((data[0] * 256) + data[1]) / 4
        return f"Decoded: engine speed = {rpm:.0f} RPM"
    if pid == 0x0D and data:
        return f"Decoded: vehicle speed = {data[0]} km/h ({data[0] * 0.621371:.1f} mph)"
    if pid == 0x05 and data:
        celsius = data[0] - 40
        return f"Decoded: coolant temperature = {celsius}°C ({celsius * 9 / 5 + 32:.1f}°F)"
    return None


def connect_with_retries(host: str, port: int, timeout: float, retries: int) -> socket.socket:
    """Wait briefly for the emulator; useful when Docker starts both containers together."""
    last_error: OSError | None = None

    for attempt in range(1, retries + 1):
        try:
            return socket.create_connection((host, port), timeout=timeout)
        except OSError as error:
            last_error = error
            if attempt < retries:
                print(f"Waiting for ELM327 emulator ({attempt}/{retries})...")
                time.sleep(1)

    raise ConnectionError(
        f"Could not connect to {host}:{port} after {retries} attempts."
    ) from last_error


def main() -> None:
    parser = argparse.ArgumentParser(description="Query an ELM327 emulator over TCP.")
    parser.add_argument("--host", default="127.0.0.1", help="Emulator host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=35000, help="Emulator TCP port (default: 35000)")
    parser.add_argument("--timeout", type=float, default=2.0, help="Seconds to wait for each reply")
    parser.add_argument("--retries", type=int, default=1, help="Connection attempts before giving up")
    parser.add_argument(
        "commands",
        nargs="*",
        help="Optional ELM/OBD commands, e.g. 010C 03. Defaults to a small live-data demo.",
    )
    args = parser.parse_args()

    commands = args.commands or DEFAULT_COMMANDS

    try:
        with connect_with_retries(args.host, args.port, args.timeout, args.retries) as sock:
            print(f"Connected to ELM327 emulator at {args.host}:{args.port}\n")

            for command in commands:
                reply = send_command(sock, command, args.timeout)
                print(f"> {command}")
                print(reply or "(no reply)")
                decoded = explain(command, reply)
                if decoded:
                    print(decoded)
                print()
    except ConnectionError:
        raise SystemExit(
            f"Could not connect to {args.host}:{args.port}. "
            "Start the emulator first with: python3 -m elm -s car -n 35000"
        )
    except TimeoutError:
        raise SystemExit("The emulator did not reply before the timeout.")


if __name__ == "__main__":
    main()
