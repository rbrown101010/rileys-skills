#!/usr/bin/env python3
"""Small Buffer GraphQL CLI for the buffer-publisher Codex skill."""

from __future__ import annotations

import argparse
import json
import os
import ssl
import subprocess
import sys
import urllib.error
import urllib.request
from typing import Any


API_URL = "https://api.buffer.com"
KEYCHAIN_SERVICE = "codex-buffer-api-key"


def ssl_context() -> ssl.SSLContext:
    try:
        import certifi  # type: ignore

        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


def key_from_keychain() -> str | None:
    user = os.environ.get("USER")
    commands = []
    if user:
        commands.append(["security", "find-generic-password", "-a", user, "-s", KEYCHAIN_SERVICE, "-w"])
    commands.append(["security", "find-generic-password", "-s", KEYCHAIN_SERVICE, "-w"])
    for command in commands:
        try:
            result = subprocess.run(command, check=False, capture_output=True, text=True)
        except FileNotFoundError:
            return None
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    return None


def get_api_key() -> str:
    key = os.environ.get("BUFFER_API_KEY") or key_from_keychain()
    if not key:
        raise SystemExit(
            "Missing Buffer API key. Set BUFFER_API_KEY or store it in macOS Keychain "
            f"as {KEYCHAIN_SERVICE}."
        )
    return key


def gql(query: str, variables: dict[str, Any] | None = None) -> tuple[dict[str, Any], dict[str, str]]:
    payload = json.dumps({"query": query, "variables": variables or {}}).encode("utf-8")
    request = urllib.request.Request(
        API_URL,
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {get_api_key()}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "codex-buffer-publisher/1.0 (+https://developers.buffer.com)",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=45, context=ssl_context()) as response:
            body = response.read().decode("utf-8")
            headers = dict(response.headers.items())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        headers = dict(exc.headers.items())
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError:
            parsed = {"http_status": exc.code, "body": body}
        raise SystemExit(json.dumps({"error": parsed, "headers": rate_headers(headers)}, indent=2))
    data = json.loads(body)
    return data, rate_headers(headers)


def rate_headers(headers: dict[str, str]) -> dict[str, str]:
    return {k: v for k, v in headers.items() if k.lower().startswith("ratelimit")}


def print_json(data: Any) -> None:
    print(json.dumps(data, indent=2, sort_keys=True))


def result_or_exit(data: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
    if data.get("errors"):
        print_json({"errors": data["errors"], "rateLimit": headers})
        raise SystemExit(1)
    return data.get("data", {})


def command_account(_: argparse.Namespace) -> None:
    query = """
    query BufferAccount {
      account {
        id
        email
        preferences { timeFormat startOfWeek defaultScheduleOption }
        organizations {
          id
          name
          channelCount
          ownerEmail
          limits { channels members scheduledPosts ideas tags }
        }
      }
    }
    """
    data, headers = gql(query)
    print_json({"data": result_or_exit(data, headers), "rateLimit": headers})


def command_channels(args: argparse.Namespace) -> None:
    query = """
    query BufferChannels($input: ChannelsInput!) {
      channels(input: $input) {
        id
        name
        displayName
        service
        type
        descriptor
        timezone
        isLocked
        isDisconnected
        isQueuePaused
        externalLink
        allowedActions
        postingSchedule { day times paused }
      }
    }
    """
    input_data: dict[str, Any] = {"organizationId": args.organization_id}
    filter_data: dict[str, Any] = {}
    if args.locked is not None:
        filter_data["isLocked"] = args.locked
    if args.product:
        filter_data["product"] = args.product
    if filter_data:
        input_data["filter"] = filter_data
    data, headers = gql(query, {"input": input_data})
    print_json({"data": result_or_exit(data, headers), "rateLimit": headers})


def command_daily_limits(args: argparse.Namespace) -> None:
    query = """
    query DailyPostingLimits($input: DailyPostingLimitsInput!) {
      dailyPostingLimits(input: $input) {
        channelId
        sent
        scheduled
        limit
        isAtLimit
      }
    }
    """
    input_data: dict[str, Any] = {"channelIds": args.channel_id}
    if args.date:
        input_data["date"] = args.date
    data, headers = gql(query, {"input": input_data})
    print_json({"data": result_or_exit(data, headers), "rateLimit": headers})


def posts_filter(args: argparse.Namespace) -> dict[str, Any]:
    filter_data: dict[str, Any] = {}
    if args.channel_id:
        filter_data["channelIds"] = args.channel_id
    if args.status:
        filter_data["status"] = args.status
    if args.start_date:
        filter_data["startDate"] = args.start_date
    if args.end_date:
        filter_data["endDate"] = args.end_date
    if args.due_start or args.due_end:
        filter_data["dueAt"] = {k: v for k, v in {"start": args.due_start, "end": args.due_end}.items() if v}
    if args.created_start or args.created_end:
        filter_data["createdAt"] = {
            k: v for k, v in {"start": args.created_start, "end": args.created_end}.items() if v
        }
    if args.tag_id:
        filter_data["tagIds"] = args.tag_id
    return filter_data


def command_posts(args: argparse.Namespace) -> None:
    query = """
    query BufferPosts($input: PostsInput!, $first: Int, $after: String) {
      posts(input: $input, first: $first, after: $after) {
        edges {
          cursor
          node {
            id
            text
            status
            via
            channelId
            dueAt
            createdAt
            updatedAt
            tags { id name color }
            assets {
              id
              mimeType
              source
              thumbnail
              type
              ... on ImageAsset { image { altText width height isAnimated } }
            }
          }
        }
        pageInfo { startCursor endCursor hasPreviousPage hasNextPage }
      }
    }
    """
    input_data: dict[str, Any] = {"organizationId": args.organization_id}
    filter_data = posts_filter(args)
    if filter_data:
        input_data["filter"] = filter_data
    if args.sort_field:
        input_data["sort"] = [{"field": args.sort_field, "direction": args.sort_direction}]
    data, headers = gql(query, {"input": input_data, "first": args.limit, "after": args.after})
    print_json({"data": result_or_exit(data, headers), "rateLimit": headers})


def command_post(args: argparse.Namespace) -> None:
    query = """
    query BufferPost($input: PostInput!) {
      post(input: $input) {
        id
        text
        status
        via
        channelId
        dueAt
        createdAt
        updatedAt
        tags { id name color }
        assets {
          id
          mimeType
          source
          thumbnail
          type
          ... on ImageAsset { image { altText width height isAnimated } }
        }
      }
    }
    """
    data, headers = gql(query, {"input": {"id": args.id}})
    print_json({"data": result_or_exit(data, headers), "rateLimit": headers})


def asset_input(args: argparse.Namespace) -> dict[str, Any] | None:
    assets: dict[str, Any] = {}
    if args.image_url:
        assets["images"] = [{"url": url} for url in args.image_url]
    if args.video_url:
        assets["videos"] = [{"url": url} for url in args.video_url]
    if args.document_url:
        assets["documents"] = [
            {"url": url, "title": args.document_title or "Document", "thumbnailUrl": args.document_thumbnail_url or url}
            for url in args.document_url
        ]
    if args.link_url:
        assets["link"] = {"url": args.link_url}
    return assets or None


def create_post_input(args: argparse.Namespace, include_id: bool = False) -> dict[str, Any]:
    input_data: dict[str, Any] = {
        "schedulingType": args.scheduling_type,
        "mode": args.mode,
    }
    if include_id:
        input_data["id"] = args.id
    else:
        input_data["channelId"] = args.channel_id
    if args.text is not None:
        input_data["text"] = args.text
    if args.due_at:
        input_data["dueAt"] = args.due_at
    if args.draft:
        input_data["saveToDraft"] = True
    if args.ai_assisted:
        input_data["aiAssisted"] = True
    if args.tag_id:
        input_data["tagIds"] = args.tag_id
    assets = asset_input(args)
    if assets:
        input_data["assets"] = assets
    return input_data


def command_preview_post(args: argparse.Namespace) -> None:
    print_json({"operation": "createPost", "input": create_post_input(args)})


def command_create_post(args: argparse.Namespace) -> None:
    input_data = create_post_input(args)
    if args.dry_run:
        print_json({"dryRun": True, "operation": "createPost", "input": input_data})
        return
    query = """
    mutation CreateBufferPost($input: CreatePostInput!) {
      createPost(input: $input) {
        ... on PostActionSuccess {
          post { id text status channelId dueAt }
        }
        ... on MutationError { message }
      }
    }
    """
    data, headers = gql(query, {"input": input_data})
    print_json({"data": result_or_exit(data, headers), "rateLimit": headers})


def command_edit_post(args: argparse.Namespace) -> None:
    input_data = create_post_input(args, include_id=True)
    if args.dry_run:
        print_json({"dryRun": True, "operation": "editPost", "input": input_data})
        return
    if not args.yes:
        raise SystemExit("Refusing to edit without --yes after explicit user confirmation.")
    query = """
    mutation EditBufferPost($input: EditPostInput!) {
      editPost(input: $input) {
        ... on PostActionSuccess {
          post { id text status channelId dueAt }
        }
        ... on MutationError { message }
      }
    }
    """
    data, headers = gql(query, {"input": input_data})
    print_json({"data": result_or_exit(data, headers), "rateLimit": headers})


def command_delete_post(args: argparse.Namespace) -> None:
    if not args.yes:
        raise SystemExit("Refusing to delete without --yes after explicit user confirmation.")
    query = """
    mutation DeleteBufferPost($input: DeletePostInput!) {
      deletePost(input: $input) {
        ... on DeletePostSuccess { id }
        ... on MutationError { message }
      }
    }
    """
    data, headers = gql(query, {"input": {"id": args.id}})
    print_json({"data": result_or_exit(data, headers), "rateLimit": headers})


def command_create_idea(args: argparse.Namespace) -> None:
    content: dict[str, Any] = {}
    if args.title:
        content["title"] = args.title
    if args.text:
        content["text"] = args.text
    if args.ai_assisted:
        content["aiAssisted"] = True
    if args.service:
        content["services"] = args.service
    if args.date:
        content["date"] = args.date
    if args.media_url:
        content["media"] = [{"url": url, "type": args.media_type, "alt": args.media_alt} for url in args.media_url]
    input_data = {"organizationId": args.organization_id, "content": content}
    if args.dry_run:
        print_json({"dryRun": True, "operation": "createIdea", "input": input_data})
        return
    query = """
    mutation CreateBufferIdea($input: CreateIdeaInput!) {
      createIdea(input: $input) {
        ... on Idea {
          id
          organizationId
          content { title text services date aiAssisted }
        }
        ... on MutationError { message }
      }
    }
    """
    data, headers = gql(query, {"input": input_data})
    print_json({"data": result_or_exit(data, headers), "rateLimit": headers})


def command_raw(args: argparse.Namespace) -> None:
    if args.query_file:
        with open(args.query_file, "r", encoding="utf-8") as handle:
            query = handle.read()
    else:
        query = args.query
    variables = json.loads(args.variables) if args.variables else {}
    data, headers = gql(query, variables)
    print_json({"data": data, "rateLimit": headers})


def add_post_options(parser: argparse.ArgumentParser, editing: bool = False) -> None:
    if editing:
        parser.add_argument("--id", required=True, help="Post ID")
        parser.add_argument("--yes", action="store_true", help="Confirm edit after user confirmation")
    else:
        parser.add_argument("--channel-id", required=True, help="Target Buffer channel ID")
    parser.add_argument("--text", help="Post text")
    parser.add_argument("--mode", default="addToQueue", choices=["addToQueue", "shareNow", "shareNext", "customScheduled", "recommendedTime"])
    parser.add_argument("--scheduling-type", default="automatic", choices=["automatic", "notification"])
    parser.add_argument("--due-at", help="UTC ISO-8601 date for customScheduled")
    parser.add_argument("--draft", action="store_true", help="Save as draft")
    parser.add_argument("--tag-id", action="append", help="Tag ID. Repeat for multiple tags.")
    parser.add_argument("--image-url", action="append", help="Public image URL. Repeat for multiple images.")
    parser.add_argument("--video-url", action="append", help="Public video URL. Repeat for multiple videos.")
    parser.add_argument("--document-url", action="append", help="Public document URL. Repeat for multiple documents.")
    parser.add_argument("--document-title", help="Title for document assets")
    parser.add_argument("--document-thumbnail-url", help="Thumbnail URL for document assets")
    parser.add_argument("--link-url", help="Link URL asset")
    parser.add_argument("--ai-assisted", action="store_true", help="Mark content as AI-assisted")
    parser.add_argument("--dry-run", action="store_true", help="Print the mutation input without sending it")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Buffer GraphQL CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    account = sub.add_parser("account", help="Read account and organizations")
    account.set_defaults(func=command_account)

    channels = sub.add_parser("channels", help="List channels for an organization")
    channels.add_argument("--organization-id", required=True)
    channels.add_argument("--locked", choices=["true", "false"], type=lambda value: value == "true")
    channels.add_argument("--product", choices=["analyze", "engage", "publish", "buffer", "startPage", "comments"])
    channels.set_defaults(func=command_channels)

    limits = sub.add_parser("daily-limits", help="Check daily posting limits")
    limits.add_argument("--channel-id", action="append", required=True)
    limits.add_argument("--date", help="DateTime; defaults to today in Buffer if omitted")
    limits.set_defaults(func=command_daily_limits)

    posts = sub.add_parser("posts", help="List posts")
    posts.add_argument("--organization-id", required=True)
    posts.add_argument("--channel-id", action="append")
    posts.add_argument("--status", action="append", choices=["draft", "needs_approval", "scheduled", "sending", "sent", "error"])
    posts.add_argument("--start-date")
    posts.add_argument("--end-date")
    posts.add_argument("--due-start")
    posts.add_argument("--due-end")
    posts.add_argument("--created-start")
    posts.add_argument("--created-end")
    posts.add_argument("--tag-id", action="append")
    posts.add_argument("--limit", type=int, default=20)
    posts.add_argument("--after")
    posts.add_argument("--sort-field", choices=["dueAt", "createdAt"])
    posts.add_argument("--sort-direction", default="desc", choices=["asc", "desc"])
    posts.set_defaults(func=command_posts)

    post = sub.add_parser("post", help="Fetch a single post")
    post.add_argument("--id", required=True)
    post.set_defaults(func=command_post)

    preview = sub.add_parser("preview-post", help="Preview createPost input")
    add_post_options(preview)
    preview.set_defaults(func=command_preview_post)

    create_post = sub.add_parser("create-post", help="Create a post")
    add_post_options(create_post)
    create_post.set_defaults(func=command_create_post)

    edit_post = sub.add_parser("edit-post", help="Edit a post")
    add_post_options(edit_post, editing=True)
    edit_post.set_defaults(func=command_edit_post)

    delete_post = sub.add_parser("delete-post", help="Delete a post")
    delete_post.add_argument("--id", required=True)
    delete_post.add_argument("--yes", action="store_true", help="Confirm deletion after user confirmation")
    delete_post.set_defaults(func=command_delete_post)

    idea = sub.add_parser("create-idea", help="Create a Buffer idea")
    idea.add_argument("--organization-id", required=True)
    idea.add_argument("--title")
    idea.add_argument("--text")
    idea.add_argument("--service", action="append")
    idea.add_argument("--date")
    idea.add_argument("--media-url", action="append")
    idea.add_argument("--media-type", default="image", choices=["image", "gif", "video", "link", "document", "unsupported"])
    idea.add_argument("--media-alt")
    idea.add_argument("--ai-assisted", action="store_true")
    idea.add_argument("--dry-run", action="store_true")
    idea.set_defaults(func=command_create_idea)

    raw = sub.add_parser("raw", help="Run a raw GraphQL query")
    raw_group = raw.add_mutually_exclusive_group(required=True)
    raw_group.add_argument("--query")
    raw_group.add_argument("--query-file")
    raw.add_argument("--variables", help="JSON object")
    raw.set_defaults(func=command_raw)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
