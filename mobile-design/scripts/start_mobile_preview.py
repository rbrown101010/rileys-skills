#!/usr/bin/env python3
"""Start a background HTTP server for a mobile-design prototype."""

from __future__ import annotations

import argparse
import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_dir", help="Prototype directory to serve")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host")
    parser.add_argument("--port", type=int, default=4173, help="Preferred port")
    parser.add_argument("--open", action="store_true", help="Open the preview in the default browser")
    return parser.parse_args()


def is_pid_running(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def find_open_port(host: str, preferred_port: int, attempts: int = 30) -> int:
    for port in range(preferred_port, preferred_port + attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind((host, port))
            except OSError:
                continue
            return port
    raise RuntimeError(f"Could not find an open port starting at {preferred_port}")


def main() -> int:
    args = parse_args()
    project_dir = Path(args.project_dir).expanduser().resolve()
    index_path = project_dir / "index.html"
    if not index_path.exists():
        print(f"index.html not found in {project_dir}", file=sys.stderr)
        return 1

    runtime_dir = project_dir / ".mobile-preview"
    runtime_dir.mkdir(exist_ok=True)
    pid_path = runtime_dir / "server.pid"
    url_path = runtime_dir / "url.txt"
    log_path = runtime_dir / "server.log"

    if pid_path.exists():
        pid = int(pid_path.read_text().strip())
        if is_pid_running(pid):
            url = url_path.read_text().strip() if url_path.exists() else "unknown"
            print(f"Preview already running at {url} (pid {pid})")
            return 0
        pid_path.unlink(missing_ok=True)

    port = find_open_port(args.host, args.port)
    url = f"http://{args.host}:{port}"
    with log_path.open("ab") as log_file:
        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "http.server",
                str(port),
                "--bind",
                args.host,
                "--directory",
                str(project_dir),
            ],
            stdout=log_file,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )

    time.sleep(0.4)
    if process.poll() is not None:
        print(f"Preview server failed to start. Check {log_path}", file=sys.stderr)
        return 1

    pid_path.write_text(f"{process.pid}\n")
    url_path.write_text(f"{url}\n")

    if args.open and sys.platform == "darwin":
        subprocess.run(["open", url], check=False)

    print(f"Preview running at {url}")
    print(f"PID: {process.pid}")
    print(f"Log: {log_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
