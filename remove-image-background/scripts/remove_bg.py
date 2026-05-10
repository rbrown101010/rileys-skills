#!/usr/bin/env python3

from __future__ import annotations

import argparse
import getpass
import json
import mimetypes
import os
import re
import shutil
import ssl
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


API_URL = "https://api.remove.bg/v1.0/removebg"
ACCOUNT_URL = "https://api.remove.bg/v1.0/account"
USER_AGENT = "Codex remove-image-background/1.0"
KEYCHAIN_SERVICE = "codex-removebg-api-key"
GLOBAL_CONFIG_DIR = Path.home() / ".config" / "remove-image-background"
GLOBAL_CONFIG_FILE = GLOBAL_CONFIG_DIR / "config.json"
DEFAULT_TIMEOUT = 120
DEFAULT_REMOVE_FORMAT = "webp"
DEFAULT_REMOVE_SIZE = "50MP"


SSL_CONTEXT = ssl.create_default_context()
try:
    import certifi  # type: ignore

    SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    pass


class CliError(Exception):
    pass


@dataclass
class SimpleResponse:
    status: int
    headers: Any
    body: bytes


def output(data: dict[str, Any]) -> None:
    print(json.dumps(data, indent=2, sort_keys=True))


def fail(message: str, *, details: dict[str, Any] | None = None, exit_code: int = 1) -> None:
    payload = {"error": message}
    if details:
        payload.update(details)
    output(payload)
    raise SystemExit(exit_code)


def read_env_key() -> tuple[str | None, str | None]:
    for name in ("REMOVE_BG_API_KEY", "REMOVEBG_API_KEY"):
        value = os.environ.get(name)
        if value:
            return value, f"environment variable {name}"
    return None, None


def keychain_supported() -> bool:
    return sys.platform == "darwin" and shutil.which("security") is not None


def read_keychain_key() -> tuple[str | None, str | None]:
    if not keychain_supported():
        return None, None
    command = [
        "security",
        "find-generic-password",
        "-a",
        getpass.getuser(),
        "-s",
        KEYCHAIN_SERVICE,
        "-w",
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        return None, None
    return result.stdout.strip(), f"macOS Keychain ({KEYCHAIN_SERVICE})"


def write_keychain_key(api_key: str) -> None:
    if not keychain_supported():
        raise CliError("macOS Keychain storage is unavailable on this machine")
    command = [
        "security",
        "add-generic-password",
        "-a",
        getpass.getuser(),
        "-s",
        KEYCHAIN_SERVICE,
        "-w",
        api_key,
        "-U",
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise CliError(result.stderr.strip() or "Failed to write API key to macOS Keychain")


def read_global_config() -> dict[str, Any]:
    if not GLOBAL_CONFIG_FILE.exists():
        return {}
    try:
        return json.loads(GLOBAL_CONFIG_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CliError(f"Invalid JSON in {GLOBAL_CONFIG_FILE}: {exc}") from exc


def write_global_config(api_key: str) -> None:
    GLOBAL_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    GLOBAL_CONFIG_FILE.write_text(json.dumps({"apiKey": api_key}, indent=2) + "\n", encoding="utf-8")
    os.chmod(GLOBAL_CONFIG_FILE, 0o600)


def resolve_api_key() -> tuple[str | None, str | None]:
    env_key, env_source = read_env_key()
    if env_key:
        return env_key, env_source

    keychain_key, keychain_source = read_keychain_key()
    if keychain_key:
        return keychain_key, keychain_source

    config = read_global_config()
    api_key = config.get("apiKey")
    if api_key:
        return str(api_key), str(GLOBAL_CONFIG_FILE)

    return None, None


def require_api_key() -> tuple[str, str]:
    api_key, source = resolve_api_key()
    if not api_key or not source:
        raise CliError(
            "API key not configured. Run 'remove_bg.py setup --key <REMOVE_BG_API_KEY>' or set REMOVE_BG_API_KEY."
        )
    return api_key, source


def is_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def slugify(value: str, *, fallback: str = "image") -> str:
    text = value.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-{2,}", "-", text).strip("-")
    return text[:80] or fallback


def infer_output_path(input_value: str, *, output: str | None, output_format: str) -> Path:
    if output:
        return Path(output).expanduser().resolve()

    extension = ".jpg" if output_format == "jpg" else f".{output_format}"
    if is_url(input_value):
        parsed = urlparse(input_value)
        stem = Path(parsed.path).stem or "image"
        filename = f"{slugify(stem)}.no-bg{extension}"
        return (Path.cwd() / filename).resolve()

    input_path = Path(input_value).expanduser().resolve()
    return input_path.with_name(f"{input_path.stem}.no-bg{extension}")


def infer_output_format(*, requested_format: str | None, output: str | None) -> str:
    if requested_format:
        return requested_format

    if output:
        suffix = Path(output).suffix.lower()
        if suffix == ".jpeg":
            suffix = ".jpg"
        if suffix in {".png", ".webp", ".jpg", ".zip"}:
            return suffix[1:]

    return DEFAULT_REMOVE_FORMAT


def build_multipart_body(
    fields: dict[str, str],
    *,
    file_field_name: str | None = None,
    file_path: Path | None = None,
) -> tuple[bytes, str]:
    boundary = f"----CodexRemoveBg{uuid.uuid4().hex}"
    chunks: list[bytes] = []

    for name, value in fields.items():
        chunks.append(f"--{boundary}\r\n".encode("utf-8"))
        chunks.append(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8"))
        chunks.append(value.encode("utf-8"))
        chunks.append(b"\r\n")

    if file_field_name and file_path:
        mime_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
        chunks.append(f"--{boundary}\r\n".encode("utf-8"))
        chunks.append(
            (
                f'Content-Disposition: form-data; name="{file_field_name}"; '
                f'filename="{file_path.name}"\r\n'
            ).encode("utf-8")
        )
        chunks.append(f"Content-Type: {mime_type}\r\n\r\n".encode("utf-8"))
        chunks.append(file_path.read_bytes())
        chunks.append(b"\r\n")

    chunks.append(f"--{boundary}--\r\n".encode("utf-8"))
    body = b"".join(chunks)
    content_type = f"multipart/form-data; boundary={boundary}"
    return body, content_type


def make_request(
    url: str,
    *,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    body: bytes | None = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> SimpleResponse:
    request_headers = {"User-Agent": USER_AGENT}
    if headers:
        request_headers.update(headers)
    request = Request(url, method=method, headers=request_headers, data=body)
    try:
        with urlopen(request, timeout=timeout, context=SSL_CONTEXT) as response:
            return SimpleResponse(status=response.status, headers=response.headers, body=response.read())
    except HTTPError as exc:
        return SimpleResponse(status=exc.code, headers=exc.headers, body=exc.read())
    except URLError as exc:
        raise CliError(f"{method} {url} failed: {exc.reason}") from exc


def decode_json(data: bytes) -> dict[str, Any]:
    if not data:
        return {}
    return json.loads(data.decode("utf-8", errors="replace"))


def error_excerpt(data: bytes, *, limit: int = 400) -> str:
    text = data.decode("utf-8", errors="replace").strip()
    return text[:limit]


def header_value(headers: Any, name: str) -> str | None:
    return headers.get(name) if headers else None


def remove_headers_summary(headers: Any) -> dict[str, Any]:
    foreground = {
        "top": header_value(headers, "X-Foreground-Top"),
        "left": header_value(headers, "X-Foreground-Left"),
        "width": header_value(headers, "X-Foreground-Width"),
        "height": header_value(headers, "X-Foreground-Height"),
    }
    return {
        "credits_charged": header_value(headers, "X-Credits-Charged"),
        "foreground": {key: value for key, value in foreground.items() if value is not None},
        "rate_limit": {
            "limit": header_value(headers, "X-RateLimit-Limit"),
            "remaining": header_value(headers, "X-RateLimit-Remaining"),
            "reset": header_value(headers, "X-RateLimit-Reset"),
            "retry_after": header_value(headers, "Retry-After"),
        },
        "response_content_type": header_value(headers, "Content-Type"),
        "result_type": header_value(headers, "X-Type"),
    }


def command_setup(args: argparse.Namespace) -> None:
    api_key = args.key or read_env_key()[0]
    if not api_key:
        fail("Missing API key. Provide --key or set REMOVE_BG_API_KEY.")

    location = args.location
    if location == "auto":
        location = "keychain" if keychain_supported() else "global"

    try:
        if location == "keychain":
            write_keychain_key(api_key)
            source = f"macOS Keychain ({KEYCHAIN_SERVICE})"
        elif location == "global":
            write_global_config(api_key)
            source = str(GLOBAL_CONFIG_FILE)
        else:
            raise CliError(f"Unsupported location: {location}")
    except CliError as exc:
        fail(str(exc))

    output(
        {
            "configured": True,
            "key_last4": api_key[-4:],
            "stored_in": source,
        }
    )


def command_config_show(_: argparse.Namespace) -> None:
    try:
        api_key, source = resolve_api_key()
    except CliError as exc:
        fail(str(exc))
        return
    output(
        {
            "configured": bool(api_key),
            "global_config_file": str(GLOBAL_CONFIG_FILE),
            "key_last4": api_key[-4:] if api_key else None,
            "key_source": source,
            "keychain_service": KEYCHAIN_SERVICE,
        }
    )


def command_account_get(_: argparse.Namespace) -> None:
    try:
        api_key, source = require_api_key()
        response = make_request(ACCOUNT_URL, headers={"X-Api-Key": api_key})
    except CliError as exc:
        fail(str(exc))
        return

    if response.status != 200:
        fail(
            f"GET /account failed with HTTP {response.status}",
            details={"response": error_excerpt(response.body)},
        )

    try:
        data = decode_json(response.body)
    except json.JSONDecodeError:
        fail("GET /account returned non-JSON data", details={"response": error_excerpt(response.body)})
        return

    output(
        {
            "account": data,
            "key_source": source,
            "rate_limit": remove_headers_summary(response.headers)["rate_limit"],
        }
    )


def command_remove(args: argparse.Namespace) -> None:
    try:
        api_key, source = require_api_key()
    except CliError as exc:
        fail(str(exc))
        return

    input_value = args.input
    output_format = infer_output_format(requested_format=args.format, output=args.output)
    output_size = args.size or DEFAULT_REMOVE_SIZE
    fields: dict[str, str] = {
        "format": output_format,
        "size": output_size,
    }
    if args.type:
        fields["type"] = args.type
    if args.crop:
        fields["crop"] = "true"
    if args.bg_color:
        fields["bg_color"] = args.bg_color

    file_path: Path | None = None
    if is_url(input_value):
        fields["image_url"] = input_value
    else:
        file_path = Path(input_value).expanduser().resolve()
        if not file_path.exists() or not file_path.is_file():
            fail("Input image file not found", details={"input": str(file_path)})
        body, content_type = build_multipart_body(fields, file_field_name="image_file", file_path=file_path)

    if is_url(input_value):
        body, content_type = build_multipart_body(fields)

    assert body is not None
    output_path = infer_output_path(input_value, output=args.output, output_format=output_format)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    attempt = 0
    while True:
        try:
            response = make_request(
                API_URL,
                method="POST",
                headers={
                    "X-Api-Key": api_key,
                    "Content-Type": content_type,
                },
                body=body,
            )
        except CliError as exc:
            fail(str(exc))
            return

        if response.status == 429 and attempt < args.max_retries:
            retry_after_raw = header_value(response.headers, "Retry-After")
            try:
                retry_after = max(1, int(retry_after_raw or "1"))
            except ValueError:
                retry_after = 1
            time.sleep(retry_after)
            attempt += 1
            continue

        if response.status != 200:
            detail = error_excerpt(response.body)
            try:
                detail = json.dumps(decode_json(response.body), sort_keys=True)
            except json.JSONDecodeError:
                pass
            fail(
                f"remove.bg request failed with HTTP {response.status}",
                details={
                    "input": input_value,
                    "response": detail[:500],
                },
            )

        output_path.write_bytes(response.body)
        summary = remove_headers_summary(response.headers)
        output(
            {
                "bytes_written": len(response.body),
                "credits_charged": summary["credits_charged"],
                "foreground": summary["foreground"],
                "input": input_value,
                "key_source": source,
                "output_format": output_format,
                "output_path": str(output_path),
                "output_size": output_size,
                "rate_limit": summary["rate_limit"],
                "response_content_type": summary["response_content_type"],
                "result_type": summary["result_type"],
                "source_type": "url" if is_url(input_value) else "file",
            }
        )
        return


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Configure and use remove.bg from Codex without extra dependencies."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    setup_parser = subparsers.add_parser("setup", help="Store the remove.bg API key locally")
    setup_parser.add_argument("--key", help="remove.bg API key")
    setup_parser.add_argument(
        "--location",
        default="auto",
        choices=["auto", "keychain", "global"],
        help="Where to store the API key. Default: auto",
    )
    setup_parser.set_defaults(func=command_setup)

    config_show_parser = subparsers.add_parser("config:show", help="Show where the API key resolves from")
    config_show_parser.set_defaults(func=command_config_show)

    account_parser = subparsers.add_parser("account:get", help="Fetch account metadata without removing a background")
    account_parser.set_defaults(func=command_account_get)

    remove_parser = subparsers.add_parser("remove", help="Remove an image background from a file path or URL")
    remove_parser.add_argument("input", help="Local image path or image URL")
    remove_parser.add_argument("--output", help="Output file path")
    remove_parser.add_argument(
        "--format",
        choices=["png", "webp", "jpg", "zip"],
        help="Output format. Default: infer from --output extension, otherwise webp",
    )
    remove_parser.add_argument(
        "--size",
        help="remove.bg size parameter. Default: 50MP",
    )
    remove_parser.add_argument("--type", help="remove.bg foreground hint, for example person or product")
    remove_parser.add_argument("--crop", action="store_true", help="Crop empty margins from the result")
    remove_parser.add_argument("--bg-color", help="Optional solid background color in hex")
    remove_parser.add_argument(
        "--max-retries",
        type=int,
        default=2,
        help="Retries on HTTP 429 using Retry-After. Default: 2",
    )
    remove_parser.set_defaults(func=command_remove)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
