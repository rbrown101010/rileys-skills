#!/usr/bin/env python3
"""Generate YouTube thumbnail options from YouTube style references."""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


YOUTUBE_RESEARCH = Path("/Users/rileybrown/.codex/skills/youtube-researcher/scripts/youtube_research.py")
IMAGE_PULLER = Path("/Users/rileybrown/.codex/skills/internet-image-puller/scripts/image_puller.py")


def run(cmd: list[str], *, env: dict[str, str] | None = None, capture: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        check=True,
        text=True,
        capture_output=capture,
        env=env,
    )


def keychain_password(service: str, account: str) -> str | None:
    try:
        result = run(["security", "find-generic-password", "-a", account, "-s", service, "-w"])
    except subprocess.CalledProcessError:
        return None
    value = result.stdout.strip()
    return value or None


def serp_env() -> dict[str, str]:
    env = os.environ.copy()
    key = env.get("SERP_API_KEY") or env.get("SERPAPI_API_KEY") or keychain_password("codex-serpapi-key", "rileybrown")
    if not key:
        raise SystemExit("Missing SerpApi key. Set SERP_API_KEY or save Keychain item codex-serpapi-key.")
    env["SERP_API_KEY"] = key
    env["SERPAPI_API_KEY"] = key
    env["SERPAPI_KEY"] = key
    return env


def slugify(value: str, fallback: str = "item") -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return slug[:80] or fallback


def download(url: str, out: Path) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    run(
        [
            "curl",
            "-L",
            "--fail",
            "--silent",
            "--show-error",
            "--max-time",
            "30",
            "-A",
            "Mozilla/5.0",
            url,
            "-o",
            str(out),
        ],
        capture=True,
    )
    return out


def load_json_from_command(cmd: list[str], env: dict[str, str]) -> Any:
    result = run(cmd, env=env)
    return json.loads(result.stdout)


def pull_style_thumbnails(args: argparse.Namespace, env: dict[str, str], out_dir: Path) -> list[dict[str, Any]]:
    if args.style_image:
        refs: list[dict[str, Any]] = []
        for index, image in enumerate(args.style_image, start=1):
            path = Path(image).expanduser().resolve()
            if not path.exists():
                raise SystemExit(f"Style image not found: {path}")
            refs.append(
                {
                    "title": f"Local style reference {index}",
                    "link": None,
                    "createdAt": None,
                    "views": None,
                    "path": str(path),
                }
            )
        return refs

    style_dir = out_dir / "style-references"
    style_dir.mkdir(parents=True, exist_ok=True)
    needed = max(args.options, args.style_count)

    if args.style_channel:
        data = load_json_from_command(
            [
                "python3",
                str(YOUTUBE_RESEARCH),
                "channel",
                args.style_channel,
                "--limit",
                str(needed),
                "--type",
                "video",
                "--json",
            ],
            env,
        )
        videos = data.get("videos", [])[:needed]
    elif args.style_query:
        data = load_json_from_command(
            [
                "python3",
                str(YOUTUBE_RESEARCH),
                "search",
                args.style_query,
                "--limit",
                str(needed),
                "--json",
                "--no-cache",
            ],
            env,
        )
        videos = data.get("results", [])[:needed]
    else:
        raise SystemExit("Provide --style-channel or --style-query.")

    refs: list[dict[str, Any]] = []
    for index, video in enumerate(videos, start=1):
        thumb = video.get("thumbnail")
        if not thumb:
            continue
        video_id = video.get("video_id") or f"style-{index}"
        title = video.get("title") or video_id
        suffix = ".jpg" if ".jpg" in thumb.split("?")[0] else ".webp"
        path = style_dir / f"{index:02d}-{slugify(title, video_id)}{suffix}"
        try:
            download(thumb, path)
        except Exception as exc:
            print(f"warn: failed to download thumbnail for {title}: {exc}", file=sys.stderr)
            continue
        refs.append(
            {
                "title": title,
                "link": video.get("link"),
                "createdAt": video.get("createdAt") or video.get("published_date"),
                "views": video.get("views"),
                "path": str(path),
            }
        )
    if not refs:
        raise SystemExit("No style thumbnails downloaded.")
    return refs


def pull_assets(args: argparse.Namespace, env: dict[str, str], out_dir: Path) -> list[Path]:
    assets: list[Path] = []
    if not args.logo_query:
        return assets
    asset_root = out_dir / "pulled-assets"
    for query in args.logo_query:
        query_dir = asset_root / slugify(query)
        run(
            [
                str(IMAGE_PULLER),
                "serp:search",
                "--query",
                query,
                "--output-dir",
                str(query_dir),
                "--limit",
                str(args.logo_limit),
            ],
            env=env,
        )
        for path in query_dir.rglob("*"):
            if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
                assets.append(path)
    return assets


def prompt_for(args: argparse.Namespace, option_index: int, style_ref: dict[str, Any], asset_paths: list[Path]) -> str:
    text = pick_variant(args.text_variant, option_index) or args.text or infer_text(args.topic, option_index)
    graphic = pick_variant(args.graphic_variant, option_index) or args.graphic or infer_graphic(args.topic, asset_paths)
    asset_names = ", ".join(sorted({p.parent.name.replace("-", " ") for p in asset_paths})) if asset_paths else "relevant simple icons or UI cards for the topic"
    return (
        "16x9 dimensions. Our goal is to copy the style of a YouTube thumbnail that did well, with our own face. "
        "Attached assets: A is the high quality thumbnail style reference. B, C, and D are images of the target person. "
        f"The target video topic is: {args.topic}. "
        "Please make a new thumbnail in the style of A, but with the face and identity of the person in B-D. "
        "Do not make the target person look like the person in A. Keep the bold layout, large readable text, high contrast, "
        "simple composition, and clear YouTube click-through design logic. "
        f"Change the text to: {text}. "
        f"Change the graphic next to him to: {graphic}. "
        f"Use or evoke these relevant logos/assets where appropriate: {asset_names}. "
        "Make it polished, modern, and professional."
    )


def form_image_arg(path: Path | str) -> str:
    path = Path(path)
    suffix = path.suffix.lower()
    mime = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }.get(suffix)
    if mime:
        return f"image[]=@{path};type={mime}"
    return f"image[]=@{path}"


def infer_text(topic: str, option_index: int) -> str:
    lower = topic.lower()
    if "remotion" in lower or "motion graphic" in lower or "make videos" in lower:
        variants = [
            "CODEX MAKES VIDEOS",
            "PROMPT TO VIDEO",
            "REMOTION + CODEX",
            "AI VIDEO WORKFLOW",
            "MAKE LAUNCH VIDEOS",
        ]
        return variants[(option_index - 1) % len(variants)]
    variants = [
        "MY AI SETUP",
        "BEST AI TOOLS",
        "MY AI WORKFLOW",
        "START HERE",
        "TOOLS I USE",
    ]
    if len(topic) <= 26:
        variants[0] = topic.upper()
    return variants[(option_index - 1) % len(variants)]


def infer_graphic(topic: str, asset_paths: list[Path]) -> str:
    lower = topic.lower()
    if "remotion" in lower or "motion graphic" in lower or "make videos" in lower:
        return "Remotion and Codex logos, a timeline/video editor preview, social media icons, and an export arrow"
    if asset_paths:
        return "a clean cluster of the relevant app logos and tool cards"
    if "ai" in topic.lower():
        return "a clean grid of AI tool cards, app icons, and a bold arrow"
    return "a simple visual diagram that explains the video's main idea"


def pick_variant(values: list[str], option_index: int) -> str | None:
    if not values:
        return None
    return values[(option_index - 1) % len(values)]


def generate_option(args: argparse.Namespace, option_index: int, style_ref: dict[str, Any], asset_paths: list[Path], out_dir: Path) -> Path:
    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("Missing OPENAI_API_KEY.")
    person_images = [Path(p) for p in args.person_image][:3]
    if len(person_images) < 1:
        raise SystemExit("Provide at least one --person-image.")

    out_path = out_dir / "generated" / f"thumbnail-{option_index:02d}.png"
    out_json = out_path.with_suffix(".json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists() and not args.force:
        return out_path

    cmd = [
        "curl",
        "-sS",
        "-X",
        "POST",
        "https://api.openai.com/v1/images/edits",
        "-H",
        f"Authorization: Bearer {os.environ['OPENAI_API_KEY']}",
        "-F",
        f"model={args.model}",
        "-F",
        form_image_arg(style_ref["path"]),
    ]
    for image in person_images:
        cmd.extend(["-F", form_image_arg(image)])
    cmd.extend(
        [
            "-F",
            f"prompt={prompt_for(args, option_index, style_ref, asset_paths)}",
            "-F",
            f"size={args.size}",
            "-F",
            f"quality={args.quality}",
            "-F",
            "output_format=png",
            "-o",
            str(out_json),
        ]
    )
    run(cmd, capture=False)
    payload = json.loads(out_json.read_text())
    if payload.get("error"):
        raise SystemExit(payload["error"].get("message", payload["error"]))
    b64 = payload["data"][0]["b64_json"]
    out_path.write_bytes(base64.b64decode(b64))
    out_json.unlink(missing_ok=True)
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate YouTube thumbnail options.")
    parser.add_argument("--topic", required=True)
    parser.add_argument("--style-channel")
    parser.add_argument("--style-query")
    parser.add_argument("--style-image", action="append", default=[])
    parser.add_argument("--style-count", type=int, default=5)
    parser.add_argument("--options", type=int, default=5)
    parser.add_argument("--person-image", action="append", default=[])
    parser.add_argument("--logo-query", action="append", default=[])
    parser.add_argument("--logo-limit", type=int, default=6)
    parser.add_argument("--text")
    parser.add_argument("--text-variant", action="append", default=[])
    parser.add_argument("--graphic")
    parser.add_argument("--graphic-variant", action="append", default=[])
    parser.add_argument("--model", default="gpt-image-2")
    parser.add_argument("--size", default="1536x864")
    parser.add_argument("--quality", default="high")
    parser.add_argument("--force", action="store_true", help="Regenerate existing thumbnails instead of resuming.")
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    out_dir = Path(args.output_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    env = serp_env()

    style_refs = pull_style_thumbnails(args, env, out_dir)
    asset_paths = pull_assets(args, env, out_dir)
    generated = []
    for index in range(1, args.options + 1):
        style_ref = style_refs[(index - 1) % len(style_refs)]
        generated.append(generate_option(args, index, style_ref, asset_paths, out_dir))

    summary = {
        "topic": args.topic,
        "options": args.options,
        "style_references": style_refs,
        "asset_count": len(asset_paths),
        "generated": [str(path) for path in generated],
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
