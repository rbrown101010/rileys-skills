#!/usr/bin/env python3
"""Stop a background HTTP server started by start_mobile_preview.py."""

from __future__ import annotations

import argparse
import os
import signal
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_dir", help="Prototype directory")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    project_dir = Path(args.project_dir).expanduser().resolve()
    pid_path = project_dir / ".mobile-preview" / "server.pid"
    if not pid_path.exists():
        print(f"No running preview recorded for {project_dir}")
        return 0

    pid = int(pid_path.read_text().strip())
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    except OSError as exc:
        print(f"Failed to stop pid {pid}: {exc}", file=sys.stderr)
        return 1

    pid_path.unlink(missing_ok=True)
    print(f"Stopped preview server for {project_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
