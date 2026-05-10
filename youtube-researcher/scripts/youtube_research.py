#!/usr/bin/env python3
"""Fast YouTube niche research via SerpApi + Supadata.

This script is intentionally dependency-light and uses only the Python standard
library so it can run in fresh Codex environments without extra setup.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import ssl
import sys
import time
import textwrap
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, urlopen

DEFAULT_SUPADATA_API_KEY = "sd_b12c8dcb7970a1e00bb1838d31b26b00"
DEFAULT_SERPAPI_KEY = "7f79f132002c4ccce713e14f6f3cf0f288ac02bcd6d6a6fa5f6ce1618656ffd5"

SERPAPI_SEARCH_URL = "https://serpapi.com/search.json"
SUPADATA_TRANSCRIPT_URL = "https://api.supadata.ai/v1/transcript"
SUPADATA_CHANNEL_URL = "https://api.supadata.ai/v1/youtube/channel"
SUPADATA_CHANNEL_VIDEOS_URL = "https://api.supadata.ai/v1/youtube/channel/videos"
SUPADATA_METADATA_URL = "https://api.supadata.ai/v1/metadata"
DEFAULT_HTTP_HEADERS = {
    "Accept": "application/json",
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/135.0.0.0 Safari/537.36"
    ),
}

VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")
VIDEO_RESULT_KEYS = ("video_results", "shorts_results", "live_results", "movie_results")


class ApiError(RuntimeError):
    """Raised when an API call fails."""


def get_supadata_key() -> str:
    return os.environ.get("SUPADATA_API_KEY") or DEFAULT_SUPADATA_API_KEY


def get_serpapi_key() -> str:
    return os.environ.get("SERPAPI_KEY") or DEFAULT_SERPAPI_KEY


def to_bool_string(value: bool) -> str:
    return "true" if value else "false"


def build_ssl_context() -> ssl.SSLContext:
    context = ssl.create_default_context()
    try:
        import certifi  # type: ignore

        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return context


def api_get_json(url: str, params: dict[str, Any], headers: dict[str, str] | None = None) -> tuple[dict[str, Any], dict[str, str]]:
    query = urlencode({k: v for k, v in params.items() if v is not None})
    for attempt in range(4):
        request = Request(
            f"{url}?{query}",
            headers={**DEFAULT_HTTP_HEADERS, **(headers or {})},
            method="GET",
        )
        try:
            with urlopen(request, timeout=30, context=build_ssl_context()) as response:
                payload = response.read().decode("utf-8")
                return json.loads(payload), dict(response.headers.items())
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            if exc.code == 429 and attempt < 3:
                retry_after = exc.headers.get("Retry-After")
                sleep_seconds = float(retry_after) if retry_after else float(2 ** attempt)
                time.sleep(sleep_seconds)
                continue
            raise ApiError(f"{exc.code} {exc.reason}: {body.strip()}") from exc
        except URLError as exc:
            raise ApiError(f"Network error: {exc.reason}") from exc
    raise ApiError("Request failed after retries.")


def extract_video_id(value: str | None) -> str | None:
    if not value:
        return None
    candidate = value.strip()
    if VIDEO_ID_RE.fullmatch(candidate):
        return candidate

    parsed = urlparse(candidate)
    if parsed.netloc == "youtu.be":
        maybe_id = parsed.path.lstrip("/").split("/")[0]
        return maybe_id if VIDEO_ID_RE.fullmatch(maybe_id) else None

    if "youtube.com" in parsed.netloc:
        if parsed.path == "/watch":
            maybe_id = parse_qs(parsed.query).get("v", [None])[0]
            return maybe_id if maybe_id and VIDEO_ID_RE.fullmatch(maybe_id) else None
        path_bits = [bit for bit in parsed.path.split("/") if bit]
        if len(path_bits) >= 2 and path_bits[0] in {"shorts", "live", "embed"}:
            maybe_id = path_bits[1]
            return maybe_id if VIDEO_ID_RE.fullmatch(maybe_id) else None
    return None


def as_video_url(value: str) -> str:
    video_id = extract_video_id(value)
    return f"https://www.youtube.com/watch?v={video_id}" if video_id else value


def truncate_text(value: str | None, max_chars: int) -> str | None:
    if value is None:
        return None
    collapsed = " ".join(value.split())
    if len(collapsed) <= max_chars:
        return collapsed
    return collapsed[: max_chars - 1].rstrip() + "…"


def normalize_search_item(source_key: str, item: dict[str, Any]) -> dict[str, Any] | None:
    link = item.get("link")
    video_id = item.get("video_id") or extract_video_id(link)
    if not video_id:
        return None

    channel = item.get("channel") or {}
    thumbnail = item.get("thumbnail")
    if isinstance(thumbnail, dict):
        thumbnail = thumbnail.get("rich") or thumbnail.get("static")

    return {
        "result_type": source_key.replace("_results", ""),
        "position_on_page": item.get("position_on_page"),
        "video_id": video_id,
        "title": item.get("title"),
        "link": link or f"https://www.youtube.com/watch?v={video_id}",
        "channel_name": channel.get("name"),
        "channel_link": channel.get("link"),
        "published_date": item.get("published_date"),
        "views": item.get("views"),
        "length": item.get("length"),
        "description": item.get("description"),
        "extensions": item.get("extensions") or [],
        "thumbnail": thumbnail,
    }


def search_youtube(query: str, limit: int, gl: str, hl: str, sp: str | None, no_cache: bool) -> dict[str, Any]:
    params = {
        "engine": "youtube",
        "search_query": query,
        "api_key": get_serpapi_key(),
        "gl": gl,
        "hl": hl,
        "output": "json",
        "sp": sp,
        "no_cache": to_bool_string(no_cache),
    }

    results: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    next_sp = sp
    page = 1

    while len(results) < limit:
        params["sp"] = next_sp
        payload, _headers = api_get_json(SERPAPI_SEARCH_URL, params)

        if payload.get("error"):
            raise ApiError(str(payload["error"]))

        page_had_results = False
        for key in VIDEO_RESULT_KEYS:
            items = payload.get(key)
            if not isinstance(items, list):
                continue
            for item in items:
                if not isinstance(item, dict):
                    continue
                normalized = normalize_search_item(key, item)
                if not normalized:
                    continue
                page_had_results = True
                if normalized["video_id"] in seen_ids:
                    continue
                seen_ids.add(normalized["video_id"])
                normalized["page"] = page
                results.append(normalized)
                if len(results) >= limit:
                    break
            if len(results) >= limit:
                break

        pagination = payload.get("serpapi_pagination") or payload.get("pagination") or {}
        next_page_token = pagination.get("next_page_token")
        if len(results) >= limit or not next_page_token or not page_had_results:
            return {
                "query": query,
                "gl": gl,
                "hl": hl,
                "sp": sp,
                "results": results[:limit],
                "next_page_token": next_page_token,
            }

        next_sp = next_page_token
        page += 1

    return {
        "query": query,
        "gl": gl,
        "hl": hl,
        "sp": sp,
        "results": results[:limit],
        "next_page_token": None,
    }


def fetch_transcript(target: str, lang: str | None, mode: str, wait_seconds: int, excerpt_chars: int | None = None) -> tuple[dict[str, Any], dict[str, str]]:
    payload, headers = api_get_json(
        SUPADATA_TRANSCRIPT_URL,
        {
            "url": as_video_url(target),
            "lang": lang,
            "text": "true",
            "mode": mode,
        },
        headers={"x-api-key": get_supadata_key()},
    )

    job_id = payload.get("jobId")
    if job_id:
        deadline = time.time() + wait_seconds
        while time.time() < deadline:
            time.sleep(1)
            status_payload, job_headers = api_get_json(
                f"{SUPADATA_TRANSCRIPT_URL}/{job_id}",
                {},
                headers={"x-api-key": get_supadata_key()},
            )
            headers.update(job_headers)
            status = status_payload.get("status")
            if status == "completed":
                payload = status_payload
                break
            if status == "failed":
                raise ApiError(f"Transcript job failed for {target}: {status_payload}")
        else:
            return {
                "job_id": job_id,
                "status": "timeout",
                "message": f"Transcript job still running after {wait_seconds} seconds.",
            }, headers

    content = payload.get("content")
    if isinstance(content, str) and excerpt_chars is not None:
        payload["excerpt"] = truncate_text(content, excerpt_chars)
    return payload, headers


def fetch_channel(channel_id: str) -> dict[str, Any]:
    payload, _headers = api_get_json(
        SUPADATA_CHANNEL_URL,
        {"id": channel_id},
        headers={"x-api-key": get_supadata_key()},
    )
    return payload


def fetch_channel_videos(channel_id: str, limit: int, video_type: str) -> dict[str, Any]:
    payload, _headers = api_get_json(
        SUPADATA_CHANNEL_VIDEOS_URL,
        {"id": channel_id, "limit": limit, "type": video_type},
        headers={"x-api-key": get_supadata_key()},
    )
    return payload


def fetch_video_metadata(target: str) -> dict[str, Any]:
    payload, _headers = api_get_json(
        SUPADATA_METADATA_URL,
        {"url": as_video_url(target)},
        headers={"x-api-key": get_supadata_key()},
    )
    return payload


def flatten_channel_video_ids(payload: dict[str, Any], limit: int) -> list[dict[str, str]]:
    ordered: list[dict[str, str]] = []
    seen: set[str] = set()
    mapping = (
        ("video", payload.get("videoIds") or []),
        ("short", payload.get("shortIds") or []),
        ("live", payload.get("liveIds") or []),
    )
    for kind, values in mapping:
        for video_id in values:
            if not isinstance(video_id, str) or video_id in seen:
                continue
            seen.add(video_id)
            ordered.append({"video_id": video_id, "kind": kind})
            if len(ordered) >= limit:
                return ordered
    return ordered


def format_item_block(item: dict[str, Any], excerpt_chars: int) -> str:
    lines = [f"- {item.get('title') or item.get('video_id')}"]
    lines.append(f"  URL: {item.get('link') or as_video_url(item['video_id'])}")
    channel_name = item.get("channel_name")
    if channel_name:
        lines.append(f"  Channel: {channel_name}")
    views = item.get("views")
    if views is not None:
        lines.append(f"  Views: {views}")
    published = item.get("published_date") or item.get("createdAt")
    if published:
        lines.append(f"  Published: {published}")
    length = item.get("length")
    if length:
        lines.append(f"  Length: {length}")
    description = truncate_text(item.get("description"), excerpt_chars)
    if description:
        lines.append(f"  Description: {description}")
    excerpt = item.get("transcript_excerpt") or item.get("excerpt")
    if excerpt:
        wrapped = textwrap.fill(excerpt, width=96, subsequent_indent="  ")
        lines.append(f"  Transcript excerpt: {wrapped}")
    return "\n".join(lines)


def print_json(data: dict[str, Any]) -> None:
    json.dump(data, sys.stdout, indent=2, ensure_ascii=True)
    sys.stdout.write("\n")


def run_search(args: argparse.Namespace) -> int:
    data = search_youtube(args.query, args.limit, args.gl, args.hl, args.sp, args.no_cache)
    results = data["results"]
    if args.channel:
        needle = args.channel.lower()
        results = [item for item in results if needle in (item.get("channel_name") or "").lower()]
        data["results"] = results

    transcript_targets = min(args.transcripts, len(results))
    for item in results[:transcript_targets]:
        transcript, headers = fetch_transcript(
            item["link"],
            args.lang,
            args.mode,
            args.wait_seconds,
            args.excerpt_chars,
        )
        item["transcript"] = transcript
        item["supadata_billable_requests"] = headers.get("x-billable-requests")
        if isinstance(transcript.get("content"), str):
            item["transcript_excerpt"] = truncate_text(transcript["content"], args.excerpt_chars)

    if args.json:
        print_json(data)
        return 0

    print(f"# Search: {args.query}")
    print(f"Returned {len(results)} results")
    for item in results:
        print(format_item_block(item, args.excerpt_chars))
    return 0


def run_transcript(args: argparse.Namespace) -> int:
    data, headers = fetch_transcript(args.target, args.lang, args.mode, args.wait_seconds, args.excerpt_chars)
    data["supadata_billable_requests"] = headers.get("x-billable-requests")

    if args.json:
        print_json(data)
        return 0

    print(f"# Transcript: {as_video_url(args.target)}")
    if "job_id" in data:
        print(json.dumps(data, indent=2, ensure_ascii=True))
        return 0
    content = data.get("content")
    if isinstance(content, str):
        print(content)
        return 0
    print(json.dumps(data, indent=2, ensure_ascii=True))
    return 0


def run_channel(args: argparse.Namespace) -> int:
    channel = fetch_channel(args.channel_id)
    video_ids_payload = fetch_channel_videos(args.channel_id, args.limit, args.type)
    ordered_ids = flatten_channel_video_ids(video_ids_payload, args.limit)

    videos: list[dict[str, Any]] = []
    for item in ordered_ids:
        metadata = fetch_video_metadata(item["video_id"])
        author = metadata.get("author") or {}
        stats = metadata.get("stats") or {}
        media = metadata.get("media") or {}
        normalized = {
            "video_id": metadata.get("id") or item["video_id"],
            "kind": item["kind"],
            "title": metadata.get("title"),
            "link": metadata.get("url") or as_video_url(item["video_id"]),
            "channel_name": author.get("displayName") or author.get("username") or channel.get("name"),
            "views": stats.get("views"),
            "description": metadata.get("description"),
            "createdAt": metadata.get("createdAt"),
            "thumbnail": media.get("thumbnailUrl"),
        }
        videos.append(normalized)

    transcript_targets = min(args.with_transcripts, len(videos))
    for item in videos[:transcript_targets]:
        transcript, headers = fetch_transcript(
            item["link"],
            args.lang,
            args.mode,
            args.wait_seconds,
            args.excerpt_chars,
        )
        item["transcript"] = transcript
        item["supadata_billable_requests"] = headers.get("x-billable-requests")
        if isinstance(transcript.get("content"), str):
            item["transcript_excerpt"] = truncate_text(transcript["content"], args.excerpt_chars)

    response = {
        "channel": channel,
        "videos": videos,
        "video_ids": video_ids_payload,
    }

    if args.json:
        print_json(response)
        return 0

    print(f"# Channel: {channel.get('name') or args.channel_id}")
    if channel.get("description"):
        print(truncate_text(channel["description"], args.excerpt_chars))
    print(f"Subscribers: {channel.get('subscriberCount')}")
    print(f"Videos returned: {len(videos)}")
    for item in videos:
        print(format_item_block(item, args.excerpt_chars))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fast YouTube search, channel inspection, and transcript collection.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    search_parser = subparsers.add_parser("search", help="Search YouTube via SerpApi.")
    search_parser.add_argument("query", help="YouTube search query.")
    search_parser.add_argument("--limit", type=int, default=10, help="Maximum results to return.")
    search_parser.add_argument("--gl", default="us", help="Country code for localization.")
    search_parser.add_argument("--hl", default="en", help="Language code for localization.")
    search_parser.add_argument("--sp", default=None, help="YouTube filter/pagination token.")
    search_parser.add_argument("--channel", default=None, help="Channel name substring filter.")
    search_parser.add_argument("--transcripts", type=int, default=0, help="Fetch transcripts for the top N results.")
    search_parser.add_argument("--lang", default=None, help="Preferred transcript language.")
    search_parser.add_argument("--mode", choices=("native", "auto", "generate"), default="auto", help="Supadata transcript mode.")
    search_parser.add_argument("--wait-seconds", type=int, default=20, help="How long to poll Supadata transcript jobs.")
    search_parser.add_argument("--excerpt-chars", type=int, default=700, help="Max chars for descriptions and transcript excerpts.")
    search_parser.add_argument("--no-cache", action="store_true", help="Force SerpApi to skip cached search results.")
    search_parser.add_argument("--json", action="store_true", help="Emit JSON instead of plain text.")
    search_parser.set_defaults(func=run_search)

    transcript_parser = subparsers.add_parser("transcript", help="Fetch a transcript for one video.")
    transcript_parser.add_argument("target", help="YouTube URL or video ID.")
    transcript_parser.add_argument("--lang", default=None, help="Preferred transcript language.")
    transcript_parser.add_argument("--mode", choices=("native", "auto", "generate"), default="auto", help="Supadata transcript mode.")
    transcript_parser.add_argument("--wait-seconds", type=int, default=30, help="How long to poll Supadata transcript jobs.")
    transcript_parser.add_argument("--excerpt-chars", type=int, default=1200, help="Excerpt size if the API returns async status first.")
    transcript_parser.add_argument("--json", action="store_true", help="Emit JSON instead of plain text.")
    transcript_parser.set_defaults(func=run_transcript)

    channel_parser = subparsers.add_parser("channel", help="Inspect a YouTube channel with Supadata.")
    channel_parser.add_argument("channel_id", help="Channel URL, handle, or ID.")
    channel_parser.add_argument("--limit", type=int, default=10, help="How many videos to inspect.")
    channel_parser.add_argument("--type", choices=("all", "video", "short", "live"), default="all", help="Which channel tab to inspect.")
    channel_parser.add_argument("--with-transcripts", type=int, default=0, help="Fetch transcripts for the first N channel videos.")
    channel_parser.add_argument("--lang", default=None, help="Preferred transcript language.")
    channel_parser.add_argument("--mode", choices=("native", "auto", "generate"), default="auto", help="Supadata transcript mode.")
    channel_parser.add_argument("--wait-seconds", type=int, default=20, help="How long to poll Supadata transcript jobs.")
    channel_parser.add_argument("--excerpt-chars", type=int, default=700, help="Max chars for descriptions and transcript excerpts.")
    channel_parser.add_argument("--json", action="store_true", help="Emit JSON instead of plain text.")
    channel_parser.set_defaults(func=run_channel)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.func(args)
    except ApiError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
