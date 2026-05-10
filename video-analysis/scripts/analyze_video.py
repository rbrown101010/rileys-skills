#!/usr/bin/env python3
"""Analyze a local video with Gemini.

This helper intentionally uses only the Python standard library plus the local
curl binary. On this Mac, curl avoids Python certificate-store issues while
keeping the workflow portable enough for normal Codex runs.
"""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any


API_BASE = "https://generativelanguage.googleapis.com"
DEFAULT_MODEL = "gemini-2.5-flash"
INLINE_LIMIT_BYTES = 20 * 1024 * 1024
DEFAULT_PROMPT = """Analyze this video and return exactly these sections:

Transcript
Provide a clean transcript of all spoken words you can identify. Include rough timestamps every 5-10 seconds or at natural sentence breaks. If audio is unclear anywhere, mark it as [unclear].

Summary
Summarize the video's main idea in plain language. Include what the viewer is supposed to understand or feel.

Key visuals
Describe the important visuals in timestamp order. Include subjects, setting, screen recordings, UI, on-screen text, movement, camera/framing, transitions, and standout visual moments. Be detailed enough that someone could recreate the video structure from the notes.
"""


def die(message: str) -> None:
    print(f"Error: {message}", file=sys.stderr)
    raise SystemExit(1)


def run_curl(args: list[str], *, input_bytes: bytes | None = None) -> tuple[str, str]:
    proc = subprocess.run(
        ["curl", "-sS", *args],
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    stdout = proc.stdout.decode("utf-8", errors="replace")
    stderr = proc.stderr.decode("utf-8", errors="replace")
    if proc.returncode != 0:
        die(stderr.strip() or f"curl exited with code {proc.returncode}")
    return stdout, stderr


def curl_json(args: list[str], *, input_bytes: bytes | None = None) -> dict[str, Any]:
    stdout, _ = run_curl(args, input_bytes=input_bytes)
    try:
        data = json.loads(stdout)
    except json.JSONDecodeError:
        die(f"API returned non-JSON response: {stdout[:1000]}")
    if "error" in data:
        die(json.dumps(data["error"], indent=2))
    return data


def detect_mime(path: Path) -> str:
    guessed = mimetypes.guess_type(path.name)[0]
    if guessed and guessed.startswith("video/"):
        return guessed
    suffix_map = {
        ".mp4": "video/mp4",
        ".m4v": "video/mp4",
        ".mov": "video/quicktime",
        ".webm": "video/webm",
    }
    return suffix_map.get(path.suffix.lower(), "video/mp4")


def extract_file(data: dict[str, Any]) -> dict[str, Any]:
    if isinstance(data.get("file"), dict):
        return data["file"]
    return data


def generate(api_key: str, model: str, payload: dict[str, Any]) -> str:
    url = f"{API_BASE}/v1beta/models/{model}:generateContent"
    data = curl_json(
        [
            "-X",
            "POST",
            "-H",
            f"x-goog-api-key: {api_key}",
            "-H",
            "Content-Type: application/json",
            "--data-binary",
            "@-",
            url,
        ],
        input_bytes=json.dumps(payload).encode("utf-8"),
    )
    parts: list[str] = []
    for candidate in data.get("candidates", []):
        for part in candidate.get("content", {}).get("parts", []):
            text = part.get("text")
            if text:
                parts.append(text)
    if not parts:
        die("Gemini returned no text.")
    return "\n".join(parts).strip()


def inline_payload(video_path: Path, mime_type: str, prompt: str, args: argparse.Namespace) -> dict[str, Any]:
    video_b64 = base64.b64encode(video_path.read_bytes()).decode("ascii")
    return build_payload(
        [{"inline_data": {"mime_type": mime_type, "data": video_b64}}],
        prompt,
        args,
    )


def build_payload(media_parts: list[dict[str, Any]], prompt: str, args: argparse.Namespace) -> dict[str, Any]:
    final_prompt = prompt
    if args.json:
        final_prompt += "\n\nReturn valid JSON with keys: transcript, summary, key_visuals."
    parts = [*media_parts, {"text": final_prompt}]
    config: dict[str, Any] = {
        "temperature": args.temperature,
        "maxOutputTokens": args.max_output_tokens,
    }
    if args.json:
        config["responseMimeType"] = "application/json"
    return {
        "contents": [{"role": "user", "parts": parts}],
        "generationConfig": config,
    }


def upload_file(api_key: str, video_path: Path, mime_type: str) -> dict[str, Any]:
    num_bytes = video_path.stat().st_size
    metadata = json.dumps({"file": {"display_name": video_path.name}}).encode("utf-8")

    with tempfile.NamedTemporaryFile(delete=False) as header_file:
        header_path = Path(header_file.name)
    try:
        run_curl(
            [
                "-D",
                str(header_path),
                "-H",
                f"x-goog-api-key: {api_key}",
                "-H",
                "X-Goog-Upload-Protocol: resumable",
                "-H",
                "X-Goog-Upload-Command: start",
                "-H",
                f"X-Goog-Upload-Header-Content-Length: {num_bytes}",
                "-H",
                f"X-Goog-Upload-Header-Content-Type: {mime_type}",
                "-H",
                "Content-Type: application/json",
                "-d",
                metadata.decode("utf-8"),
                f"{API_BASE}/upload/v1beta/files",
            ]
        )
        upload_url = ""
        for line in header_path.read_text(errors="replace").splitlines():
            if line.lower().startswith("x-goog-upload-url:"):
                upload_url = line.split(":", 1)[1].strip()
                break
        if not upload_url:
            die("Gemini did not return an upload URL.")

        with video_path.open("rb") as video_file:
            proc = subprocess.run(
                [
                    "curl",
                    "-sS",
                    upload_url,
                    "-H",
                    f"Content-Length: {num_bytes}",
                    "-H",
                    "X-Goog-Upload-Offset: 0",
                    "-H",
                    "X-Goog-Upload-Command: upload, finalize",
                    "--data-binary",
                    "@-",
                ],
                stdin=video_file,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
        if proc.returncode != 0:
            die(proc.stderr.decode("utf-8", errors="replace").strip())
        try:
            data = json.loads(proc.stdout.decode("utf-8", errors="replace"))
        except json.JSONDecodeError:
            die(f"Upload returned non-JSON response: {proc.stdout[:1000]!r}")
        if "error" in data:
            die(json.dumps(data["error"], indent=2))
        return extract_file(data)
    finally:
        header_path.unlink(missing_ok=True)


def poll_file(api_key: str, file_name: str, timeout_seconds: int) -> dict[str, Any]:
    deadline = time.time() + timeout_seconds
    last_state = "UNKNOWN"
    while time.time() < deadline:
        data = curl_json(
            [
                "-H",
                f"x-goog-api-key: {api_key}",
                f"{API_BASE}/v1beta/{file_name}",
            ]
        )
        file_data = extract_file(data)
        last_state = file_data.get("state", "UNKNOWN")
        if last_state == "ACTIVE":
            return file_data
        if last_state == "FAILED":
            die(f"Gemini file processing failed for {file_name}.")
        time.sleep(5)
    die(f"Gemini file processing timed out. Last state: {last_state}")


def delete_file(api_key: str, file_name: str) -> None:
    run_curl(
        [
            "-X",
            "DELETE",
            "-H",
            f"x-goog-api-key: {api_key}",
            f"{API_BASE}/v1beta/{file_name}",
        ]
    )


def files_payload(file_uri: str, mime_type: str, prompt: str, args: argparse.Namespace) -> dict[str, Any]:
    return build_payload(
        [{"file_data": {"mime_type": mime_type, "file_uri": file_uri}}],
        prompt,
        args,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze a local video with Gemini.")
    parser.add_argument("video", help="Local path to a video file.")
    parser.add_argument("--prompt", default=DEFAULT_PROMPT, help="Custom analysis prompt.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Gemini model name.")
    parser.add_argument("--json", action="store_true", help="Ask Gemini for JSON output.")
    parser.add_argument("--inline-limit-mb", type=float, default=20.0, help="Inline upload threshold in MB.")
    parser.add_argument("--temperature", type=float, default=0.1)
    parser.add_argument("--max-output-tokens", type=int, default=12000)
    parser.add_argument("--processing-timeout", type=int, default=600, help="Files API processing timeout in seconds.")
    parser.add_argument("--keep-upload", action="store_true", help="Do not delete a Files API upload after analysis.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        die("Set GEMINI_API_KEY in the environment for this run.")

    video_path = Path(args.video).expanduser().resolve()
    if not video_path.exists():
        die(f"File not found: {video_path}")
    if not video_path.is_file():
        die(f"Not a file: {video_path}")

    mime_type = detect_mime(video_path)
    inline_limit = int(args.inline_limit_mb * 1024 * 1024)
    file_size = video_path.stat().st_size

    uploaded_name = ""
    try:
        if file_size <= inline_limit:
            payload = inline_payload(video_path, mime_type, args.prompt, args)
        else:
            uploaded = upload_file(api_key, video_path, mime_type)
            uploaded_name = uploaded.get("name", "")
            if not uploaded_name:
                die("Upload succeeded but no file name was returned.")
            active_file = poll_file(api_key, uploaded_name, args.processing_timeout)
            file_uri = active_file.get("uri") or uploaded.get("uri")
            if not file_uri:
                die("Gemini file did not include a file URI.")
            payload = files_payload(file_uri, mime_type, args.prompt, args)
        print(generate(api_key, args.model, payload))
    finally:
        if uploaded_name and not args.keep_upload:
            try:
                delete_file(api_key, uploaded_name)
            except Exception as exc:
                print(f"Warning: could not delete Gemini file {uploaded_name}: {exc}", file=sys.stderr)


if __name__ == "__main__":
    main()
