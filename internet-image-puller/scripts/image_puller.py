#!/usr/bin/env python3

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import mimetypes
import re
import ssl
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, urlencode, urlparse, urlsplit, urlunsplit
from urllib.request import Request, urlopen


SERP_API_URL = "https://serpapi.com/search.json"
FIRECRAWL_BASE_URL = "https://api.firecrawl.dev"
USER_AGENT = "Codex internet-image-puller/1.0"
MANIFEST_NAME = "manifest.json"
DEFAULT_TIMEOUT = 60
TRANSFORM_QUERY_KEYS = {
    "w",
    "h",
    "q",
    "fm",
    "fit",
    "crop",
    "dpr",
    "auto",
    "s",
    "f",
    "blur",
    "bg",
}

SSL_CONTEXT = ssl.create_default_context()
try:
    import certifi  # type: ignore

    SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def error(message: str, *, exit_code: int = 1) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(exit_code)


def read_env(*names: str) -> str | None:
    import os

    for name in names:
        value = os.environ.get(name)
        if value:
            return value
    return None


def require_env(*names: str) -> str:
    value = read_env(*names)
    if value:
        return value
    error(f"Missing required environment variable. Expected one of: {', '.join(names)}")
    return ""


def request_json(
    url: str,
    *,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    payload: dict[str, Any] | None = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> dict[str, Any]:
    body = None
    request_headers = {"User-Agent": USER_AGENT}
    if headers:
        request_headers.update(headers)
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        request_headers.setdefault("Content-Type", "application/json")
    request = Request(url, data=body, method=method, headers=request_headers)
    try:
        with urlopen(request, timeout=timeout, context=SSL_CONTEXT) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            raw = response.read().decode(charset)
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        error(f"{method} {url} failed with HTTP {exc.code}: {detail[:400]}")
    except URLError as exc:
        error(f"{method} {url} failed: {exc.reason}")
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        error(f"{method} {url} did not return JSON. First 400 chars:\n{raw[:400]}")
    return {}


def sanitize_slug(value: str, *, fallback: str = "image") -> str:
    text = (value or "").strip().lower()
    text = re.sub(r"https?://", "", text)
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-{2,}", "-", text).strip("-")
    return text[:80] or fallback


def strip_transform_query(url: str) -> str:
    parts = urlsplit(url)
    if not parts.query:
        return url
    filtered = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if k.lower() not in TRANSFORM_QUERY_KEYS]
    new_query = urlencode(filtered, doseq=True)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, new_query, parts.fragment))


def canonical_image_url(url: str) -> str:
    stripped = strip_transform_query(url)
    parts = urlsplit(stripped)
    query_pairs = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)]
    query = urlencode(sorted(query_pairs), doseq=True)
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path, query, ""))


def guess_extension(url: str, content_type: str | None, data: bytes) -> str:
    parsed = urlparse(url)
    suffix = Path(parsed.path).suffix.lower()
    if suffix in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp", ".tif", ".tiff", ".avif"}:
        return suffix

    query = dict(parse_qsl(parsed.query))
    fm = query.get("fm", "").lower()
    if fm in {"png", "jpg", "jpeg", "gif", "webp", "svg", "bmp", "avif"}:
        return f".{fm if fm != 'jpeg' else 'jpg'}"

    if content_type:
        lowered = content_type.split(";")[0].strip().lower()
        if lowered == "image/svg+xml":
            return ".svg"
        ext = mimetypes.guess_extension(lowered)
        if ext:
            return ".jpg" if ext == ".jpe" else ext

    prefix = data[:64].lstrip()
    if prefix.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if prefix.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if prefix.startswith((b"GIF87a", b"GIF89a")):
        return ".gif"
    if prefix.startswith(b"RIFF") and b"WEBP" in prefix[:16]:
        return ".webp"
    if prefix.startswith(b"<svg") or prefix.startswith(b"<?xml") and b"<svg" in data[:512]:
        return ".svg"
    return ".img"


def load_manifest(output_dir: Path) -> dict[str, Any]:
    manifest_path = output_dir / MANIFEST_NAME
    if manifest_path.exists():
        with manifest_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    return {
        "created_at": utc_now(),
        "output_dir": str(output_dir),
        "runs": [],
        "entries": [],
    }


def save_manifest(output_dir: Path, manifest: dict[str, Any]) -> Path:
    manifest_path = output_dir / MANIFEST_NAME
    with manifest_path.open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2, sort_keys=True)
        handle.write("\n")
    return manifest_path


def existing_keys(manifest: dict[str, Any]) -> tuple[set[str], set[str]]:
    hashes = set()
    canonical_urls = set()
    for entry in manifest.get("entries", []):
        if entry.get("sha256"):
            hashes.add(entry["sha256"])
        if entry.get("canonical_url"):
            canonical_urls.add(entry["canonical_url"])
    return hashes, canonical_urls


def domain_allowed(candidate: dict[str, Any], required_domains: list[str]) -> bool:
    if not required_domains:
        return True
    hosts = []
    for field in ("image_url", "page_url", "source_page"):
        value = candidate.get(field)
        if not value:
            continue
        host = urlparse(value).netloc.lower()
        if host:
            hosts.append(host)
    for required in required_domains:
        required = required.lower()
        for host in hosts:
            if host == required or host.endswith(f".{required}"):
                return True
    return False


def fetch_binary(url: str, *, referer: str | None = None, timeout: int = DEFAULT_TIMEOUT) -> tuple[bytes, str | None, str]:
    headers = {"User-Agent": USER_AGENT}
    if referer:
        headers["Referer"] = referer
    request = Request(url, headers=headers)
    try:
        with urlopen(request, timeout=timeout, context=SSL_CONTEXT) as response:
            content_type = response.headers.get("Content-Type")
            final_url = response.geturl()
            data = response.read()
            return data, content_type, final_url
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {detail[:240]}") from exc
    except URLError as exc:
        raise RuntimeError(str(exc.reason)) from exc


def serp_search(query: str, *, limit: int, safe: str | None) -> list[dict[str, Any]]:
    api_key = require_env("SERP_API_KEY", "SERPAPI_API_KEY")
    results: list[dict[str, Any]] = []
    page = 0
    seen_originals: set[str] = set()

    while len(results) < limit:
        params = {
            "engine": "google_images",
            "q": query,
            "api_key": api_key,
            "ijn": str(page),
            "no_cache": "true",
        }
        if safe:
            params["safe"] = safe
        payload = request_json(f"{SERP_API_URL}?{urlencode(params)}")
        image_results = payload.get("images_results") or []
        if not image_results:
            break
        page_added = 0
        for item in image_results:
            image_url = item.get("original") or item.get("thumbnail")
            if not image_url or image_url in seen_originals:
                continue
            seen_originals.add(image_url)
            results.append(
                {
                    "provider": "serpapi",
                    "query": query,
                    "title": item.get("title") or query,
                    "page_url": item.get("link"),
                    "source_label": item.get("source"),
                    "image_url": image_url,
                    "thumbnail_url": item.get("thumbnail"),
                }
            )
            page_added += 1
            if len(results) >= limit:
                break
        if page_added == 0:
            break
        page += 1

    return results[:limit]


def firecrawl_headers() -> dict[str, str]:
    api_key = require_env("FIRECRAWL_API_KEY")
    return {"Authorization": f"Bearer {api_key}"}


def firecrawl_scrape_images(url: str) -> list[str]:
    payload = {"url": url, "formats": ["images"]}
    response = request_json(
        f"{FIRECRAWL_BASE_URL}/v2/scrape",
        method="POST",
        headers=firecrawl_headers(),
        payload=payload,
    )
    data = response.get("data") or {}
    images = data.get("images") or []
    return [image for image in images if isinstance(image, str)]


def firecrawl_map(
    url: str,
    *,
    search: str | None,
    limit: int,
    include_subdomains: bool,
) -> list[dict[str, str]]:
    payload = {
        "url": url,
        "limit": limit,
        "includeSubdomains": include_subdomains,
        "ignoreQueryParameters": True,
    }
    if search:
        payload["search"] = search
    response = request_json(
        f"{FIRECRAWL_BASE_URL}/v2/map",
        method="POST",
        headers=firecrawl_headers(),
        payload=payload,
    )
    links = response.get("links") or []
    normalized = []
    for item in links:
        if isinstance(item, str):
            normalized.append({"url": item, "title": "", "description": ""})
        elif isinstance(item, dict) and item.get("url"):
            normalized.append(
                {
                    "url": item["url"],
                    "title": item.get("title", ""),
                    "description": item.get("description", ""),
                }
            )
    return normalized


def build_download_items_from_firecrawl(url: str, images: list[str], *, provider: str) -> list[dict[str, Any]]:
    items = []
    for image_url in images:
        items.append(
            {
                "provider": provider,
                "source_page": url,
                "page_url": url,
                "title": Path(urlparse(image_url).path).stem or Path(urlparse(url).path).stem or "image",
                "image_url": image_url,
            }
        )
    return items


def filter_pages(
    pages: list[dict[str, str]],
    *,
    include_terms: list[str],
    exclude_terms: list[str],
    base_url: str,
    page_limit: int,
) -> list[dict[str, str]]:
    include_terms = [term.lower() for term in include_terms]
    exclude_terms = [term.lower() for term in exclude_terms]

    by_url: dict[str, dict[str, str]] = {base_url: {"url": base_url, "title": "", "description": ""}}
    for page in pages:
        by_url[page["url"]] = page

    filtered: list[dict[str, str]] = []
    for page in by_url.values():
        haystack = " ".join([page.get("url", ""), page.get("title", ""), page.get("description", "")]).lower()
        if include_terms and not all(term in haystack for term in include_terms):
            continue
        if any(term in haystack for term in exclude_terms):
            continue
        filtered.append(page)

    return filtered[:page_limit]


def download_candidates(
    candidates: list[dict[str, Any]],
    *,
    output_dir: Path,
    strip_transform: bool,
    workers: int,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest(output_dir)
    known_hashes, known_urls = existing_keys(manifest)
    new_entries: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []

    prepared: list[dict[str, Any]] = []
    seen_in_run: set[str] = set()
    save_lock = threading.Lock()

    for index, candidate in enumerate(candidates, start=1):
        image_url = candidate.get("image_url")
        if not image_url or not image_url.startswith(("http://", "https://")):
            skipped.append({"reason": "unsupported_url", "image_url": image_url, "source_page": candidate.get("source_page")})
            continue
        requested_url = strip_transform_query(image_url) if strip_transform else image_url
        canonical_url = canonical_image_url(requested_url)
        if canonical_url in known_urls or canonical_url in seen_in_run:
            skipped.append({"reason": "duplicate_url", "image_url": requested_url, "source_page": candidate.get("source_page")})
            continue
        seen_in_run.add(canonical_url)
        prepared.append(
            {
                **candidate,
                "sequence": index,
                "requested_url": requested_url,
                "canonical_url": canonical_url,
            }
        )

    def worker(candidate: dict[str, Any]) -> dict[str, Any]:
        data, content_type, final_url = fetch_binary(
            candidate["requested_url"],
            referer=candidate.get("page_url") or candidate.get("source_page"),
        )
        sha256 = hashlib.sha256(data).hexdigest()
        slug = sanitize_slug(candidate.get("title") or Path(urlparse(candidate["requested_url"]).path).stem)
        ext = guess_extension(final_url, content_type, data)
        filename = f"{candidate['sequence']:03d}-{slug}-{sha256[:10]}{ext}"
        file_path = output_dir / filename
        with save_lock:
            if sha256 in known_hashes:
                return {
                    "status": "skipped",
                    "reason": "duplicate_sha256",
                    "candidate": candidate,
                    "sha256": sha256,
                }
            with file_path.open("wb") as handle:
                handle.write(data)
            known_hashes.add(sha256)
        return {
            "status": "saved",
            "candidate": candidate,
            "entry": {
                "saved_at": utc_now(),
                "provider": candidate.get("provider"),
                "query": candidate.get("query"),
                "title": candidate.get("title"),
                "page_url": candidate.get("page_url"),
                "source_page": candidate.get("source_page"),
                "source_label": candidate.get("source_label"),
                "image_url": candidate.get("image_url"),
                "requested_url": candidate.get("requested_url"),
                "canonical_url": candidate.get("canonical_url"),
                "resolved_url": final_url,
                "content_type": content_type,
                "sha256": sha256,
                "bytes": len(data),
                "file_path": str(file_path),
            },
        }

    with concurrent.futures.ThreadPoolExecutor(max_workers=max(workers, 1)) as executor:
        futures = [executor.submit(worker, candidate) for candidate in prepared]
        for future in concurrent.futures.as_completed(futures):
            try:
                result = future.result()
            except Exception as exc:  # noqa: BLE001
                skipped.append({"reason": "download_error", "error": str(exc)})
                continue
            if result["status"] == "saved":
                entry = result["entry"]
                new_entries.append(entry)
                known_urls.add(entry["canonical_url"])
            else:
                skipped.append(
                    {
                        "reason": result["reason"],
                        "image_url": result["candidate"].get("requested_url"),
                        "source_page": result["candidate"].get("source_page"),
                    }
                )

    manifest["entries"].extend(sorted(new_entries, key=lambda item: item["file_path"]))
    run_summary = {
        "ran_at": utc_now(),
        "attempted": len(prepared),
        "saved": len(new_entries),
        "skipped": len(skipped),
    }
    manifest["runs"].append(run_summary)
    manifest_path = save_manifest(output_dir, manifest)

    return {
        "output_dir": str(output_dir),
        "manifest_path": str(manifest_path),
        "saved_count": len(new_entries),
        "skipped_count": len(skipped),
        "saved_files": [entry["file_path"] for entry in sorted(new_entries, key=lambda item: item["file_path"])],
        "skipped": skipped,
    }


def command_config_show(_: argparse.Namespace) -> dict[str, Any]:
    return {
        "serp_api_key_present": bool(read_env("SERP_API_KEY", "SERPAPI_API_KEY")),
        "firecrawl_api_key_present": bool(read_env("FIRECRAWL_API_KEY")),
    }


def command_serp_search(args: argparse.Namespace) -> dict[str, Any]:
    candidates = serp_search(args.query, limit=args.limit, safe=args.safe)
    if args.require_domain:
        candidates = [candidate for candidate in candidates if domain_allowed(candidate, args.require_domain)]
    summary = download_candidates(
        candidates,
        output_dir=Path(args.output_dir).expanduser(),
        strip_transform=not args.keep_transform_query,
        workers=args.download_workers,
    )
    summary.update(
        {
            "command": "serp:search",
            "query": args.query,
            "candidate_count": len(candidates),
        }
    )
    return summary


def command_firecrawl_scrape(args: argparse.Namespace) -> dict[str, Any]:
    images = firecrawl_scrape_images(args.url)
    items = build_download_items_from_firecrawl(args.url, images[: args.limit], provider="firecrawl-scrape")
    summary = download_candidates(
        items,
        output_dir=Path(args.output_dir).expanduser(),
        strip_transform=not args.keep_transform_query,
        workers=args.download_workers,
    )
    summary.update(
        {
            "command": "firecrawl:scrape",
            "url": args.url,
            "image_urls_found": len(images),
            "candidate_count": len(items),
        }
    )
    return summary


def command_firecrawl_site(args: argparse.Namespace) -> dict[str, Any]:
    pages = firecrawl_map(
        args.url,
        search=args.map_search,
        limit=args.map_limit,
        include_subdomains=args.include_subdomains,
    )
    selected_pages = filter_pages(
        pages,
        include_terms=args.include,
        exclude_terms=args.exclude,
        base_url=args.url,
        page_limit=args.page_limit,
    )
    candidates: list[dict[str, Any]] = []
    page_summaries: list[dict[str, Any]] = []
    for page in selected_pages:
        images = firecrawl_scrape_images(page["url"])
        limited_images = images[: args.images_per_page]
        page_summaries.append({"url": page["url"], "image_urls_found": len(images), "used": len(limited_images)})
        candidates.extend(build_download_items_from_firecrawl(page["url"], limited_images, provider="firecrawl-site"))

    summary = download_candidates(
        candidates,
        output_dir=Path(args.output_dir).expanduser(),
        strip_transform=not args.keep_transform_query,
        workers=args.download_workers,
    )
    summary.update(
        {
            "command": "firecrawl:site",
            "url": args.url,
            "mapped_pages": len(pages),
            "selected_pages": len(selected_pages),
            "page_summaries": page_summaries,
            "candidate_count": len(candidates),
        }
    )
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Search or scrape internet images and download them into a local folder.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    config_show = subparsers.add_parser("config:show", help="Show whether required API keys are present.")
    config_show.set_defaults(func=command_config_show)

    serp_search_parser = subparsers.add_parser("serp:search", help="Search Google Images with SerpAPI and download results.")
    serp_search_parser.add_argument("--query", required=True)
    serp_search_parser.add_argument("--output-dir", required=True)
    serp_search_parser.add_argument("--limit", type=int, default=20)
    serp_search_parser.add_argument("--safe", choices=["active", "off"], default=None)
    serp_search_parser.add_argument("--require-domain", action="append", default=[])
    serp_search_parser.add_argument("--download-workers", type=int, default=8)
    serp_search_parser.add_argument("--keep-transform-query", action="store_true")
    serp_search_parser.set_defaults(func=command_serp_search)

    firecrawl_scrape_parser = subparsers.add_parser("firecrawl:scrape", help="Scrape one page with Firecrawl and download its images.")
    firecrawl_scrape_parser.add_argument("--url", required=True)
    firecrawl_scrape_parser.add_argument("--output-dir", required=True)
    firecrawl_scrape_parser.add_argument("--limit", type=int, default=100)
    firecrawl_scrape_parser.add_argument("--download-workers", type=int, default=8)
    firecrawl_scrape_parser.add_argument("--keep-transform-query", action="store_true")
    firecrawl_scrape_parser.set_defaults(func=command_firecrawl_scrape)

    firecrawl_site_parser = subparsers.add_parser("firecrawl:site", help="Map a site with Firecrawl, scrape selected pages, and download their images.")
    firecrawl_site_parser.add_argument("--url", required=True)
    firecrawl_site_parser.add_argument("--output-dir", required=True)
    firecrawl_site_parser.add_argument("--map-search")
    firecrawl_site_parser.add_argument("--map-limit", type=int, default=25)
    firecrawl_site_parser.add_argument("--page-limit", type=int, default=10)
    firecrawl_site_parser.add_argument("--images-per-page", type=int, default=100)
    firecrawl_site_parser.add_argument("--include", action="append", default=[])
    firecrawl_site_parser.add_argument("--exclude", action="append", default=[])
    firecrawl_site_parser.add_argument("--include-subdomains", action="store_true")
    firecrawl_site_parser.add_argument("--download-workers", type=int, default=8)
    firecrawl_site_parser.add_argument("--keep-transform-query", action="store_true")
    firecrawl_site_parser.set_defaults(func=command_firecrawl_site)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    result = args.func(args)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
