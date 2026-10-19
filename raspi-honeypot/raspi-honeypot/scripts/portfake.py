#!/usr/bin/env python3
"""
portfake.py
Taeuscht typische Active Directory Ports vor (Kerberos, RPC, LDAP, SMB, RDP).
Jede Verbindung wird als JSON Zeile protokolliert. Es laeuft kein echter Dienst,
das Skript liest nur die ersten Bytes, antwortet minimal und schliesst.
"""

import argparse
import asyncio
import json
from datetime import datetime, timezone

PORTS = {
    88: "kerberos",
    135: "msrpc",
    389: "ldap",
    445: "smb",
    3389: "rdp",
}

# Minimale Antworten, damit Scanner den Dienst erkennen
# RDP: X.224 Connection Confirm
RDP_CC = bytes.fromhex("0300000b06d00000123400")
# SMB: Antwort ohne Dialekt-Auswahl, Verbindung wird danach geschlossen
SMB_NEG = bytes.fromhex(
    "00000025ff534d4272000000008801c00000000000000000000000000000fffe00000000"
    "01ffff0000"
)

READ_LIMIT = 2048
TIMEOUT = 8


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Logger:
    def __init__(self, path: str):
        self.path = path

    def write(self, event: dict) -> None:
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")


def make_handler(port: int, log: Logger):
    service = PORTS[port]

    async def handle(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        peer = writer.get_extra_info("peername") or ("?", 0)
        event = {
            "timestamp": now(),
            "eventid": "portfake.connect",
            "src_ip": peer[0],
            "src_port": peer[1],
            "dst_port": port,
            "service": service,
        }
        try:
            data = await asyncio.wait_for(reader.read(READ_LIMIT), timeout=TIMEOUT)
            event["bytes"] = len(data)
            event["payload_hex"] = data[:256].hex()
            printable = "".join(chr(b) if 32 <= b < 127 else "." for b in data[:256])
            event["payload_ascii"] = printable
            if service == "rdp" and data[:1] == b"\x03":
                writer.write(RDP_CC)
            elif service == "smb" and b"SMB" in data[:16]:
                writer.write(SMB_NEG)
            await writer.drain()
        except asyncio.TimeoutError:
            event["bytes"] = 0
        except Exception as exc:  # noqa: BLE001
            event["error"] = type(exc).__name__
        finally:
            log.write(event)
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:  # noqa: BLE001
                pass

    return handle


async def main(args) -> None:
    log = Logger(args.log)
    servers = []
    for port in PORTS:
        srv = await asyncio.start_server(make_handler(port, log), args.bind, port)
        servers.append(srv)
        print(f"lausche auf {args.bind}:{port} ({PORTS[port]})", flush=True)
    await asyncio.gather(*(s.serve_forever() for s in servers))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Fake AD Ports")
    ap.add_argument("--log", default="/var/log/portfake/portfake.json")
    ap.add_argument("--bind", default="0.0.0.0")
    try:
        asyncio.run(main(ap.parse_args()))
    except KeyboardInterrupt:
        pass
