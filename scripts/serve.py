"""Run the Sous live server.

    uv run scripts/serve.py            # http://localhost:8000
    uv run scripts/serve.py --https    # https://<this Mac's LAN IP>:8443 for a phone

Phone browsers only open the camera on a secure page, so a phone needs --https.
That makes a self-signed certificate in certs/ (git-ignored) the first time; the
phone shows a warning once, which you accept ("Show details" -> "visit this
website" on iPhone).
"""

from __future__ import annotations

import argparse
import socket
import subprocess
import sys
from pathlib import Path

import uvicorn

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
CERTS = ROOT / "certs"


def lan_ip() -> str:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        try:
            s.connect(("10.255.255.255", 1))  # no packet is sent; picks the outbound interface
            return s.getsockname()[0]
        except OSError:
            return "127.0.0.1"


def self_signed(ip: str) -> tuple[Path, Path]:
    key, cert = CERTS / "key.pem", CERTS / "cert.pem"
    stamp = CERTS / "ip.txt"
    if cert.exists() and stamp.exists() and stamp.read_text() == ip:
        return key, cert
    CERTS.mkdir(exist_ok=True)
    subprocess.run(["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-days", "30",
                    "-keyout", str(key), "-out", str(cert), "-subj", "/CN=sous.local",
                    "-addext", f"subjectAltName=IP:{ip},DNS:localhost"],
                   check=True, capture_output=True)
    key.chmod(0o600)
    stamp.write_text(ip)
    return key, cert


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--https", action="store_true")
    p.add_argument("--port", type=int)
    args = p.parse_args()
    if args.https:
        ip = lan_ip()
        key, cert = self_signed(ip)
        port = args.port or 8443
        print(f"\n  On your phone (same wifi): https://{ip}:{port}\n")
        uvicorn.run("server.app:app", host="0.0.0.0", port=port,
                    ssl_keyfile=str(key), ssl_certfile=str(cert))
    else:
        port = args.port or 8000
        print(f"\n  http://localhost:{port}\n")
        uvicorn.run("server.app:app", host="127.0.0.1", port=port)


if __name__ == "__main__":
    main()
