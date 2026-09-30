#!/usr/bin/env python3
"""Tiny TCP client for the ELM327 emulator.

Start the emulator first, for example:
    python3 -m elm -s car -n 35000

Then open the interactive menu:
    python3 elm_client.py

Or send specific commands and exit:
    python3 elm_client.py 010C 03

The emulator address comes from ELM_HOST and ELM_PORT, or from --host and --port.
"""

from __future__ import annotations

import argparse
import os
import re
import socket
import time
from typing import Optional


MENU = {
    "1": ("Engine RPM", "010C"),
    "2": ("Vehicle speed", "010D"),
    "3": ("Coolant temperature", "0105"),
    "4": ("Stored trouble codes (DTCs)", "03"),
}


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

    return reply.decode("ascii", errors="replace").replace("\r", "\n").replace(">", "").strip()


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


def run_command(sock: socket.socket, command: str, timeout: float) -> None:
    reply = send_command(sock, command, timeout)
    print(f"> {command}")
    print(reply or "(no reply)")
    decoded = explain(command, reply)
    if decoded:
        print(decoded)
    print()


def run_menu(sock: socket.socket, timeout: float) -> None:
    while True:
        for key, (label, command) in MENU.items():
            print(f"  {key}) {label} [{command}]")
        print("  q) Quit")

        try:
            choice = input("Choose: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return

        if choice == "q":
            return
        if choice not in MENU:
            print(f"Unknown choice: {choice!r}\n")
            continue

        print()
        run_command(sock, MENU[choice][1], timeout)


def main() -> None:
    parser = argparse.ArgumentParser(description="Query an ELM327 emulator over TCP.")
    parser.add_argument(
        "--host",
        default=os.environ.get("ELM_HOST", "127.0.0.1"),
        help="Emulator host (default: $ELM_HOST or 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("ELM_PORT", "35000")),
        help="Emulator TCP port (default: $ELM_PORT or 35000)",
    )
    parser.add_argument("--timeout", type=float, default=2.0, help="Seconds to wait for each reply")
    parser.add_argument("--retries", type=int, default=1, help="Connection attempts before giving up")
    parser.add_argument(
        "commands",
        nargs="*",
        help="Optional ELM/OBD commands, e.g. 010C 03. Without commands, opens the interactive menu.",
    )
    args = parser.parse_args()

    try:
        with connect_with_retries(args.host, args.port, args.timeout, args.retries) as sock:
            print(f"Connected to ELM327 emulator at {args.host}:{args.port}\n")
            send_command(sock, "ATE0", args.timeout)

            if args.commands:
                for command in args.commands:
                    run_command(sock, command, args.timeout)
            else:
                run_menu(sock, args.timeout)
    except ConnectionError:
        raise SystemExit(
            f"Could not connect to {args.host}:{args.port}. "
            "Start the emulator first with: python3 -m elm -s car -n 35000"
        )
    except TimeoutError:
        raise SystemExit("The emulator did not reply before the timeout.")


if __name__ == "__main__":
    main()
