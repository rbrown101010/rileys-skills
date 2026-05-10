#!/usr/bin/env python3
"""Small QuiverAI REST helper for generating and vectorizing SVGs."""

from __future__ import annotations

import argparse
import base64
import getpass
import json
import os
import ssl
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


API_BASE = "https://api.quiver.ai"
DEFAULT_MODEL = "arrow-1.1"
KEYCHAIN_SERVICE = "codex-quiver-ai"


class QuiverError(RuntimeError):
    def __init__(self, message: str, status: int | None = None, payload: Any = None):
        super().__init__(message)
        self.status = status
        self.payload = payload


def require_key() -> str:
    key = os.environ.get("QUIVERAI_API_KEY", "").strip()
    if key:
        return key
    key = key_from_keychain()
    if not key:
        raise QuiverError(
            "Missing QuiverAI API key. Run `quiver_svg.py configure-key` "
            "or export QUIVERAI_API_KEY before running this command."
        )
    return key


def keychain_account() -> str:
    return os.environ.get("USER") or getpass.getuser()


def key_from_keychain() -> str:
    try:
        result = subprocess.run(
            [
                "security",
                "find-generic-password",
                "-s",
                KEYCHAIN_SERVICE,
                "-a",
                keychain_account(),
                "-w",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return ""
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def store_key_in_keychain(key: str) -> None:
    try:
        result = subprocess.run(
            [
                "security",
                "add-generic-password",
                "-U",
                "-s",
                KEYCHAIN_SERVICE,
                "-a",
                keychain_account(),
                "-w",
                key,
            ],
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise QuiverError("macOS `security` command was not found.") from exc
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise QuiverError(f"Could not store key in macOS Keychain: {detail}")


def request_json(method: str, path: str, body: dict[str, Any] | None = None) -> Any:
    key = require_key()
    data = None if body is None else json.dumps(body).encode("utf-8")
    request = urllib.request.Request(
        f"{API_BASE}{path}",
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=180, context=ssl_context()) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        payload = parse_json_or_text(raw)
        message = format_error(exc.code, payload)
        raise QuiverError(message, status=exc.code, payload=payload) from exc
    except urllib.error.URLError as exc:
        raise QuiverError(f"Network error calling QuiverAI: {exc.reason}") from exc
    return json.loads(raw)


def ssl_context() -> ssl.SSLContext:
    try:
        import certifi
    except ImportError:
        return ssl.create_default_context()
    return ssl.create_default_context(cafile=certifi.where())


def parse_json_or_text(raw: str) -> Any:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


def format_error(status: int, payload: Any) -> str:
    if isinstance(payload, dict):
        parts = [f"QuiverAI request failed with HTTP {status}"]
        for key in ("code", "message", "request_id"):
            value = payload.get(key)
            if value:
                parts.append(f"{key}={value}")
        return "; ".join(parts)
    return f"QuiverAI request failed with HTTP {status}: {payload}"


def add_sampling_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--temperature", type=float)
    parser.add_argument("--top-p", type=float, dest="top_p")
    parser.add_argument("--presence-penalty", type=float, dest="presence_penalty")
    parser.add_argument("--max-output-tokens", type=int, dest="max_output_tokens")


def add_common_request_fields(args: argparse.Namespace, body: dict[str, Any]) -> None:
    for key in ("temperature", "top_p", "presence_penalty", "max_output_tokens"):
        value = getattr(args, key, None)
        if value is not None:
            body[key] = value


def reference_from_file(path: str) -> dict[str, str]:
    raw = Path(path).expanduser().read_bytes()
    return {"base64": base64.b64encode(raw).decode("ascii")}


def image_from_args(args: argparse.Namespace) -> dict[str, str]:
    if args.image_url:
        return {"url": args.image_url}
    raw = Path(args.image_file).expanduser().read_bytes()
    return {"base64": base64.b64encode(raw).decode("ascii")}


def write_response_json(response: Any, path: str | None) -> None:
    if not path:
        return
    out = Path(path).expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(response, indent=2), encoding="utf-8")


def output_paths(out_arg: str, count: int) -> list[Path]:
    out = Path(out_arg).expanduser()
    if count == 1 and out.suffix.lower() == ".svg":
        out.parent.mkdir(parents=True, exist_ok=True)
        return [out]
    out.mkdir(parents=True, exist_ok=True)
    return [out / f"quiver-output-{index + 1}.svg" for index in range(count)]


def save_svgs(response: Any, out_arg: str) -> list[Path]:
    items = response.get("data", [])
    if not items:
        raise QuiverError("QuiverAI response did not include data outputs.")
    paths = output_paths(out_arg, len(items))
    for item, path in zip(items, paths, strict=True):
        svg = item.get("svg")
        if not svg:
            raise QuiverError("QuiverAI output was missing an SVG payload.")
        path.write_text(svg, encoding="utf-8")
    return paths


def cmd_models(args: argparse.Namespace) -> None:
    response = request_json("GET", "/v1/models")
    write_response_json(response, args.raw_response)
    if args.json:
        print(json.dumps(response, indent=2))
        return
    for model in response.get("data", []):
        pricing = model.get("pricing_credits", {})
        generate = pricing.get("svg_generate", "?")
        vectorize = pricing.get("svg_vectorize", "?")
        print(f"{model.get('id')}: {model.get('name', '')} generate={generate} vectorize={vectorize}")


def cmd_configure_key(args: argparse.Namespace) -> None:
    if args.from_env:
        key = os.environ.get("QUIVERAI_API_KEY", "").strip()
    elif args.stdin:
        key = sys.stdin.read().strip()
    else:
        key = getpass.getpass("QuiverAI API key: ").strip()
    if not key:
        raise QuiverError("No API key provided.")
    store_key_in_keychain(key)
    print(f"Stored QuiverAI API key in macOS Keychain service `{KEYCHAIN_SERVICE}`.")


def cmd_key_status(args: argparse.Namespace) -> None:
    if os.environ.get("QUIVERAI_API_KEY", "").strip():
        print("QuiverAI API key found in QUIVERAI_API_KEY.")
        return
    if key_from_keychain():
        print(f"QuiverAI API key found in macOS Keychain service `{KEYCHAIN_SERVICE}`.")
        return
    raise QuiverError("No QuiverAI API key found in environment or macOS Keychain.")


def cmd_generate(args: argparse.Namespace) -> None:
    body: dict[str, Any] = {
        "model": args.model,
        "prompt": args.prompt,
        "n": args.n,
        "stream": False,
    }
    if args.instructions:
        body["instructions"] = args.instructions
    references: list[Any] = []
    references.extend({"url": url} for url in args.reference_url)
    references.extend(reference_from_file(path) for path in args.reference_file)
    if references:
        body["references"] = references
    add_common_request_fields(args, body)
    response = request_json("POST", "/v1/svgs/generations", body)
    write_response_json(response, args.raw_response)
    paths = save_svgs(response, args.out)
    print_summary(response, paths)


def cmd_vectorize(args: argparse.Namespace) -> None:
    body: dict[str, Any] = {
        "model": args.model,
        "stream": False,
        "image": image_from_args(args),
    }
    if args.auto_crop:
        body["auto_crop"] = True
    if args.target_size is not None:
        body["target_size"] = args.target_size
    add_common_request_fields(args, body)
    response = request_json("POST", "/v1/svgs/vectorizations", body)
    write_response_json(response, args.raw_response)
    paths = save_svgs(response, args.out)
    print_summary(response, paths)


def print_summary(response: Any, paths: list[Path]) -> None:
    if response.get("id"):
        print(f"response_id={response['id']}")
    if "credits" in response:
        print(f"credits={response['credits']}")
    for path in paths:
        print(f"wrote={path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Use the QuiverAI SVG API.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    models = subparsers.add_parser("models", help="List available QuiverAI models.")
    models.add_argument("--json", action="store_true", help="Print the full JSON response.")
    models.add_argument("--raw-response", help="Write the full response JSON to this path.")
    models.set_defaults(func=cmd_models)

    configure_key = subparsers.add_parser("configure-key", help="Store the QuiverAI API key in macOS Keychain.")
    source = configure_key.add_mutually_exclusive_group()
    source.add_argument("--from-env", action="store_true", help="Store the current QUIVERAI_API_KEY value.")
    source.add_argument("--stdin", action="store_true", help="Read the key from stdin.")
    configure_key.set_defaults(func=cmd_configure_key)

    key_status = subparsers.add_parser("key-status", help="Check whether a QuiverAI API key is configured.")
    key_status.set_defaults(func=cmd_key_status)

    generate = subparsers.add_parser("generate", help="Generate SVGs from a text prompt.")
    generate.add_argument("--prompt", required=True)
    generate.add_argument("--instructions")
    generate.add_argument("--model", default=DEFAULT_MODEL)
    generate.add_argument("--n", type=int, default=1)
    generate.add_argument("--reference-url", action="append", default=[])
    generate.add_argument("--reference-file", action="append", default=[])
    generate.add_argument("--out", required=True)
    generate.add_argument("--raw-response")
    add_sampling_args(generate)
    generate.set_defaults(func=cmd_generate)

    vectorize = subparsers.add_parser("vectorize", help="Convert a raster image into SVG.")
    source = vectorize.add_mutually_exclusive_group(required=True)
    source.add_argument("--image-url")
    source.add_argument("--image-file")
    vectorize.add_argument("--model", default=DEFAULT_MODEL)
    vectorize.add_argument("--auto-crop", action="store_true")
    vectorize.add_argument("--target-size", type=int)
    vectorize.add_argument("--out", required=True)
    vectorize.add_argument("--raw-response")
    add_sampling_args(vectorize)
    vectorize.set_defaults(func=cmd_vectorize)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except QuiverError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
