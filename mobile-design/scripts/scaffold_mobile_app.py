#!/usr/bin/env python3
"""Scaffold a local mobile-design prototype from the bundled starter."""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path


TOKEN_NAME = "__APP_NAME__"
TOKEN_SLUG = "__APP_SLUG__"


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower())
    slug = re.sub(r"-{2,}", "-", slug).strip("-")
    return slug or "mobile-app"


def replace_tokens(root: Path, app_name: str, app_slug: str) -> None:
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".html", ".css", ".js", ".jsx", ".json", ".md", ".txt"}:
            continue
        content = path.read_text()
        content = content.replace(TOKEN_NAME, app_name)
        content = content.replace(TOKEN_SLUG, app_slug)
        path.write_text(content)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True, help="Human-readable app name")
    parser.add_argument("--slug", help="Folder slug; defaults to a slugified app name")
    parser.add_argument(
        "--out",
        default="output/mobile-design",
        help="Parent output directory. Default: output/mobile-design",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite the target directory if it already exists",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    app_name = args.name.strip()
    if not app_name:
        print("App name cannot be empty.", file=sys.stderr)
        return 1

    app_slug = slugify(args.slug or app_name)
    skill_dir = Path(__file__).resolve().parents[1]
    starter_dir = skill_dir / "assets" / "prototype-starter"
    if not starter_dir.exists():
        print(f"Starter assets not found: {starter_dir}", file=sys.stderr)
        return 1

    parent_dir = Path(args.out).expanduser().resolve()
    target_dir = parent_dir / app_slug

    if target_dir.exists():
        if not args.force:
            print(f"Target already exists: {target_dir}", file=sys.stderr)
            print("Pass --force to overwrite it.", file=sys.stderr)
            return 1
        shutil.rmtree(target_dir)

    target_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(starter_dir, target_dir)
    replace_tokens(target_dir, app_name, app_slug)

    print(f"Created mobile prototype: {target_dir}")
    print("Next steps:")
    print(
        "  python3 "
        f"{skill_dir / 'scripts' / 'start_mobile_preview.py'} "
        f"{target_dir} --open"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
