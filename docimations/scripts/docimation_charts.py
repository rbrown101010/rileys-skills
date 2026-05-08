#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import math
import shutil
import subprocess
from pathlib import Path
from typing import Any

from PIL import Image


W, H = 1280, 720
BG = "#ffffff"
TEXT = "#050505"
MUTED = "#4f5459"
ARROW = "#70716d"
FONT_STACK = "-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', Arial, sans-serif"

TONES = {
    "gray": ("#f3f1eb", "#696862", "#1f1f1f"),
    "green": ("#e3f5ef", "#127967", "#003d39"),
    "purple": ("#eeeeff", "#554fc2", "#28245f"),
    "orange": ("#fff2dc", "#ba7724", "#5a3310"),
    "blue": ("#eef4ff", "#3863b8", "#19335e"),
}


SAMPLE_CHARTS: list[dict[str, Any]] = [
    {
        "id": "model_handoff",
        "type": "linear",
        "title": "Model handoff",
        "subtitle": "A placeholder flow for turning one prompt into a useful output.",
        "nodes": [
            {"label": "Prompt", "note": "what you want", "tone": "gray"},
            {"label": "Plan", "note": "small path", "tone": "green"},
            {"label": "Tools", "note": "do the work", "tone": "purple"},
            {"label": "Result", "note": "ready to use", "tone": "orange"},
        ],
    },
    {
        "id": "research_pipeline",
        "type": "linear",
        "title": "Research pipeline",
        "subtitle": "A placeholder chart for moving from scattered inputs to a sharp takeaway.",
        "nodes": [
            {"label": "Find", "note": "sources", "tone": "gray"},
            {"label": "Verify", "note": "check dates", "tone": "green"},
            {"label": "Synthesize", "note": "make useful", "tone": "purple"},
        ],
        "below": ["raw notes", "trusted facts", "clear answer"],
    },
    {
        "id": "context_lookup",
        "type": "hub",
        "title": "Context lookup",
        "subtitle": "A placeholder map for choosing the right context before answering.",
        "center": {"label": "Question", "note": "new request", "tone": "gray"},
        "nodes": [
            {"label": "Local files", "note": "current truth", "tone": "green", "position": "left"},
            {"label": "Memory", "note": "prior work", "tone": "purple", "position": "bottom-left"},
            {"label": "Web", "note": "fresh facts", "tone": "orange", "position": "right"},
            {"label": "Answer", "note": "short and useful", "tone": "blue", "position": "bottom-right"},
        ],
    },
    {
        "id": "automation_timeline",
        "type": "timeline",
        "title": "Automation timeline",
        "subtitle": "A placeholder timeline for showing scheduled work without extra UI.",
        "nodes": [
            {"label": "Trigger", "note": "time or event", "tone": "gray"},
            {"label": "Run", "note": "agent wakes up", "tone": "green"},
            {"label": "Check", "note": "inspect result", "tone": "purple"},
            {"label": "Report", "note": "send update", "tone": "orange"},
        ],
    },
    {
        "id": "human_in_the_loop",
        "type": "linear",
        "title": "Human in the loop",
        "subtitle": "A placeholder chart for keeping taste and approval in the workflow.",
        "nodes": [
            {"label": "User", "note": "sets taste", "tone": "gray"},
            {"label": "Agent", "note": "makes draft", "tone": "green"},
            {"label": "Ship", "note": "final output", "tone": "purple"},
        ],
        "review_label": "tighten, approve, redirect",
    },
]


def rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


def mix(a: str, b: str, t: float) -> str:
    ar, ag, ab = rgb(a)
    br, bg, bb = rgb(b)
    return "#{:02x}{:02x}{:02x}".format(
        int(ar + (br - ar) * t),
        int(ag + (bg - ag) * t),
        int(ab + (bb - ab) * t),
    )


def esc(value: str) -> str:
    return html.escape(str(value), quote=True)


def ease(t: float) -> float:
    if t <= 0:
        return 0.0
    if t >= 1:
        return 1.0
    return 1 - (1 - t) * (1 - t)


def progress(frame: int, start: int, length: int) -> float:
    return ease((frame - start) / max(1, length))


def tone_colors(node: dict[str, Any]) -> tuple[str, str, str]:
    tone = node.get("tone", "gray")
    return TONES.get(tone, TONES["gray"])


def svg_shell(title: str, subtitle: str, body: str) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <rect width="{W}" height="{H}" fill="{BG}"/>
  <text x="170" y="145" fill="{TEXT}" font-family="{FONT_STACK}" font-size="44" font-weight="700">{esc(title)}</text>
  <text x="170" y="220" fill="{TEXT}" font-family="{FONT_STACK}" font-size="28" font-weight="400">{esc(subtitle)}</text>
  {body}
</svg>
"""


def text_line(x: float, y: float, value: str, size: int, color: str, p: float = 1.0, weight: int = 400) -> str:
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="middle" fill="{mix(BG, color, p)}" '
        f'font-family="{FONT_STACK}" font-size="{size}" font-weight="{weight}" opacity="{p:.3f}">{esc(value)}</text>'
    )


def box(x: int, y: int, w: int, h: int, node: dict[str, Any], p: float) -> str:
    fill, outline, text_fill = tone_colors(node)
    cx = x + w / 2
    cy = y + h / 2
    scale = 0.86 + 0.14 * p
    note_color = text_fill if text_fill != "#1f1f1f" else MUTED
    return f"""
  <g opacity="{p:.3f}" transform="translate({cx:.1f} {cy:.1f}) scale({scale:.3f}) translate({-cx:.1f} {-cy:.1f})">
    <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16" fill="{mix(BG, fill, p)}" stroke="{mix(BG, outline, p)}" stroke-width="3"/>
    <text x="{cx:.1f}" y="{cy - 8:.1f}" text-anchor="middle" fill="{mix(BG, text_fill, p)}" font-family="{FONT_STACK}" font-size="25" font-weight="500">{esc(node.get("label", ""))}</text>
    <text x="{cx:.1f}" y="{cy + 28:.1f}" text-anchor="middle" fill="{mix(BG, note_color, p)}" font-family="{FONT_STACK}" font-size="17" font-weight="400">{esc(node.get("note", ""))}</text>
  </g>"""


def arrowhead(x: float, y: float, angle: float, color: str, opacity: float) -> str:
    size = 15
    left = angle + math.pi * 0.78
    right = angle - math.pi * 0.78
    points = [
        (x, y),
        (x + math.cos(left) * size, y + math.sin(left) * size),
        (x + math.cos(right) * size, y + math.sin(right) * size),
    ]
    pts = " ".join(f"{px:.1f},{py:.1f}" for px, py in points)
    return f'<polygon points="{pts}" fill="{color}" opacity="{opacity:.3f}"/>'


def arrow(x1: int, y1: int, x2: int, y2: int, p: float, color: str = ARROW) -> str:
    tx = x1 + (x2 - x1) * p
    ty = y1 + (y2 - y1) * p
    line_color = mix(BG, color, p)
    angle = math.atan2(y2 - y1, x2 - x1)
    head = ""
    if p > 0.72:
        head = arrowhead(x2, y2, angle, line_color, min(1.0, (p - 0.72) / 0.28))
    return (
        f'<line x1="{x1}" y1="{y1}" x2="{tx:.1f}" y2="{ty:.1f}" '
        f'stroke="{line_color}" stroke-width="3" stroke-linecap="round"/>{head}'
    )


def dot(x: int, y: int, node: dict[str, Any], p: float, r: int = 18) -> str:
    fill, outline, _ = tone_colors(node)
    return (
        f'<circle cx="{x}" cy="{y}" r="{r * p:.1f}" fill="{mix(BG, fill, p)}" '
        f'stroke="{mix(BG, outline, p)}" stroke-width="3" opacity="{p:.3f}"/>'
    )


def linear_frame(chart: dict[str, Any], frame: int, frames: int) -> str:
    nodes = chart["nodes"]
    count = len(nodes)
    box_w = 215 if count >= 4 else 230
    box_h = 110
    gap = 40
    total_w = count * box_w + (count - 1) * gap
    x0 = int((W - total_w) / 2)
    y = 420
    parts: list[str] = []

    review = chart.get("review_label")
    if review:
        p = progress(frame, int(frames * 0.38), 7)
        parts.append(
            f'<rect x="475" y="300" width="330" height="95" rx="18" fill="{mix(BG, "#fafafa", p)}" stroke="{mix(BG, "#d6d6d2", p)}" stroke-width="2" opacity="{p:.3f}"/>'
        )
        parts.append(text_line(640, 360, review, 17, MUTED, p))

    for idx, node in enumerate(nodes):
        start = 2 + idx * 7
        x = x0 + idx * (box_w + gap)
        p = progress(frame, start, 6)
        parts.append(box(x, y, box_w, box_h, node, p))
        if idx < count - 1:
            parts.append(arrow(x + box_w + 12, y + box_h // 2, x + box_w + gap - 12, y + box_h // 2, progress(frame, start + 4, 5)))
        if chart.get("below"):
            labels = chart["below"]
            if idx < len(labels):
                parts.append(arrow(x + box_w // 2, y + box_h + 10, x + box_w // 2, y + box_h + 70, progress(frame, start + 3, 5)))
                parts.append(text_line(x + box_w // 2, y + box_h + 98, labels[idx], 17, MUTED, progress(frame, start + 6, 5)))

    return svg_shell(chart["title"], chart["subtitle"], "\n".join(parts))


def loop_frame(chart: dict[str, Any], frame: int, frames: int) -> str:
    nodes = chart["nodes"][:4]
    coords = [(360, 320), (720, 320), (720, 500), (360, 500)]
    arrows = [((570, 375), (710, 375)), ((820, 440), (820, 490)), ((710, 555), (570, 555)), ((460, 490), (460, 440))]
    parts: list[str] = []
    for idx, node in enumerate(nodes):
        start = 2 + idx * 7
        x, y = coords[idx]
        parts.append(box(x, y, 200, 110, node, progress(frame, start, 6)))
        (x1, y1), (x2, y2) = arrows[idx]
        parts.append(arrow(x1, y1, x2, y2, progress(frame, start + 4, 5)))
    return svg_shell(chart["title"], chart["subtitle"], "\n".join(parts))


def branch_frame(chart: dict[str, Any], frame: int, frames: int) -> str:
    source = chart.get("source") or chart["nodes"][0]
    branches = chart.get("branches") or chart["nodes"][1:]
    parts = [box(210, 420, 230, 125, source, progress(frame, 2, 7))]
    trunk_p = progress(frame, 8, 7)
    trunk_color = mix(BG, ARROW, trunk_p)
    parts.append(f'<line x1="455" y1="482" x2="565" y2="482" stroke="{trunk_color}" stroke-width="3" stroke-linecap="round"/>')
    y_positions = [350, 482, 615] if len(branches) == 3 else [385, 550]
    parts.append(f'<line x1="565" y1="{min(y_positions)}" x2="565" y2="{max(y_positions)}" stroke="{trunk_color}" stroke-width="3" stroke-linecap="round"/>')
    for idx, node in enumerate(branches):
        y = y_positions[idx]
        start = 13 + idx * 7
        parts.append(arrow(565, y, 700, y, trunk_p))
        parts.append(box(715, y - 62, 270, 124, node, progress(frame, start, 6)))
    return svg_shell(chart["title"], chart["subtitle"], "\n".join(parts))


def stack_frame(chart: dict[str, Any], frame: int, frames: int) -> str:
    nodes = chart["nodes"]
    widths = [560, 420, 280, 210]
    parts: list[str] = []
    for idx, node in enumerate(nodes):
        w = widths[min(idx, len(widths) - 1)]
        x = int((W - w) / 2)
        y = 500 - idx * 85
        parts.append(box(x, y, w, 95, node, progress(frame, 4 + idx * 8, 7)))
    return svg_shell(chart["title"], chart["subtitle"], "\n".join(parts))


def timeline_frame(chart: dict[str, Any], frame: int, frames: int) -> str:
    nodes = chart["nodes"]
    x0, x1 = 265, 970
    y = 480
    count = len(nodes)
    xs = [int(x0 + (x1 - x0) * idx / max(1, count - 1)) for idx in range(count)]
    rail_p = progress(frame, 3, 9)
    parts = [
        f'<line x1="{x0}" y1="{y}" x2="{x0 + (x1 - x0) * rail_p:.1f}" y2="{y}" stroke="{mix(BG, ARROW, rail_p)}" stroke-width="3" stroke-linecap="round"/>'
    ]
    for idx, node in enumerate(nodes):
        start = 7 + idx * 6
        p = progress(frame, start, 6)
        x = xs[idx]
        parts.append(dot(x, y, node, p))
        parts.append(arrow(x, y - 18, x, y - 32, p))
        parts.append(box(x - 95, 340, 190, 105, node, p))
    return svg_shell(chart["title"], chart["subtitle"], "\n".join(parts))


def hub_frame(chart: dict[str, Any], frame: int, frames: int) -> str:
    center = chart.get("center") or {"label": "Question", "note": "new request", "tone": "gray"}
    positions = {
        "left": (185, 315),
        "right": (885, 315),
        "top": (535, 285),
        "bottom": (535, 535),
        "bottom-left": (435, 520),
        "bottom-right": (635, 520),
    }
    center_xy = (525, 400, 230, 120)
    cx = center_xy[0] + center_xy[2] // 2
    cy = center_xy[1] + center_xy[3] // 2
    parts = [box(*center_xy, center, progress(frame, 2, 7))]
    for idx, node in enumerate(chart["nodes"]):
        x, y = positions.get(node.get("position", "right"), positions["right"])
        nx, ny = x + 105, y + 52
        start = 9 + idx * 6
        parts.append(arrow(cx, cy, nx, ny, progress(frame, start - 2, 5)))
        parts.append(box(x, y, 210, 105, node, progress(frame, start, 6)))
    return svg_shell(chart["title"], chart["subtitle"], "\n".join(parts))


BUILDERS = {
    "linear": linear_frame,
    "loop": loop_frame,
    "branch": branch_frame,
    "stack": stack_frame,
    "timeline": timeline_frame,
    "hub": hub_frame,
}


def write_svg(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def convert_svg(svg_path: Path, png_path: Path) -> None:
    png_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["sips", "-s", "format", "png", str(svg_path), "--out", str(png_path)],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def gif_from_pngs(gif_path: Path, frame_paths: list[Path], duration: int) -> None:
    frames = [Image.open(path).convert("RGB") for path in frame_paths]
    frames[0].save(
        gif_path,
        save_all=True,
        append_images=frames[1:],
        duration=duration,
        loop=0,
        optimize=True,
        disposal=2,
    )


def render_chart(chart: dict[str, Any], out_dir: Path, frames: int, duration: int) -> Path:
    chart_id = chart["id"]
    builder = BUILDERS.get(chart.get("type"))
    if builder is None:
        raise ValueError(f"Unsupported chart type for {chart_id}: {chart.get('type')}")

    pngs: list[Path] = []
    for frame in range(frames):
        svg_path = out_dir / "svg_frames" / chart_id / f"frame_{frame:03d}.svg"
        png_path = out_dir / "png_frames" / chart_id / f"frame_{frame:03d}.png"
        write_svg(svg_path, builder(chart, frame, frames))
        convert_svg(svg_path, png_path)
        pngs.append(png_path)

    gif_path = out_dir / f"{chart_id}.gif"
    gif_from_pngs(gif_path, pngs, duration)
    return gif_path


def preview_sheet(gifs: list[Path], out_dir: Path) -> Path:
    thumb_w, thumb_h = 384, 216
    sheet = Image.new("RGB", (thumb_w * 2, (thumb_h + 36) * len(gifs)), "white")
    for row, path in enumerate(gifs):
        gif = Image.open(path)
        first = gif.copy().convert("RGB").resize((thumb_w, thumb_h))
        gif.seek(gif.n_frames - 1)
        last = gif.copy().convert("RGB").resize((thumb_w, thumb_h))
        y = row * (thumb_h + 36) + 18
        sheet.paste(first, (0, y))
        sheet.paste(last, (thumb_w, y))
    out = out_dir / "preview_sheet.png"
    sheet.save(out)
    return out


def load_charts(args: argparse.Namespace) -> list[dict[str, Any]]:
    if args.spec:
        data = json.loads(Path(args.spec).read_text(encoding="utf-8"))
        charts = data["charts"] if isinstance(data, dict) else data
    else:
        charts = SAMPLE_CHARTS

    if args.only:
        wanted = {item.strip() for item in args.only.split(",") if item.strip()}
        charts = [chart for chart in charts if chart.get("id") in wanted]

    if not charts:
        raise SystemExit("No charts selected.")
    return charts


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate doc-ready animated GIF charts from editable SVG frames.")
    parser.add_argument("--out", required=True, help="Output directory for GIFs, frames, and preview sheet.")
    parser.add_argument("--spec", help="JSON chart spec. If omitted, uses the built-in sample preset.")
    parser.add_argument("--preset", default="sample", choices=["sample"], help="Built-in preset to render.")
    parser.add_argument("--only", help="Comma-separated chart ids to render.")
    parser.add_argument("--frames", type=int, default=32, help="Frame count per chart. Lower is faster.")
    parser.add_argument("--duration", type=int, default=95, help="GIF frame duration in milliseconds.")
    parser.add_argument("--clean", action="store_true", help="Remove existing output directory before rendering.")
    args = parser.parse_args()

    if not shutil.which("sips"):
        raise SystemExit("Missing sips. This script expects macOS /usr/bin/sips for SVG to PNG conversion.")
    if args.frames < 28:
        raise SystemExit("--frames must be at least 28 so every chart reaches its final state.")

    out_dir = Path(args.out).expanduser().resolve()
    if args.clean and out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    charts = load_charts(args)
    gifs = [render_chart(chart, out_dir, args.frames, args.duration) for chart in charts]
    preview = preview_sheet(gifs, out_dir)
    for path in gifs + [preview]:
        print(path)


if __name__ == "__main__":
    main()
