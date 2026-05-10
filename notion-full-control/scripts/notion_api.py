#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import sys
from typing import Any, Dict, Optional
from urllib.parse import parse_qsl

import requests


NOTION_VERSION = "2022-06-28"
BASE_URL = "https://api.notion.com/v1"
KEYCHAIN_SERVICE = "codex-notion-api-key"


def get_token() -> str:
    token = os.getenv("NOTION_API_KEY")
    if token:
        return token.strip()

    result = subprocess.run(
        ["security", "find-generic-password", "-a", os.getenv("USER", ""), "-s", KEYCHAIN_SERVICE, "-w"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0 and result.stdout.strip():
        return result.stdout.strip()

    raise SystemExit(
        "No Notion token found. Set NOTION_API_KEY or add a macOS Keychain item with service 'codex-notion-api-key'."
    )


def parse_json_arg(value: Optional[str], file_path: Optional[str] = None) -> Optional[Any]:
    if value is None and file_path is None:
        return None
    if file_path:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return json.loads(value)


class NotionClient:
    def __init__(self, token: str):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Notion-Version": NOTION_VERSION,
                "Content-Type": "application/json",
            }
        )

    def request(self, method: str, path: str, body: Optional[Dict[str, Any]] = None, query: Optional[str] = None) -> Any:
        path = path if path.startswith("/") else f"/{path}"
        url = f"{BASE_URL}{path}"
        params = dict(parse_qsl(query, keep_blank_values=True)) if query else None
        resp = self.session.request(method.upper(), url, json=body, params=params, timeout=60)
        try:
            data = resp.json()
        except Exception:
            data = {"status_code": resp.status_code, "text": resp.text}
        if not resp.ok:
            print(json.dumps(data, indent=2, ensure_ascii=False), file=sys.stderr)
            raise SystemExit(resp.status_code)
        return data


def print_json(data: Any) -> None:
    print(json.dumps(data, indent=2, ensure_ascii=False))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Direct Notion API CLI with Keychain-backed auth.")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("whoami", help="Return integration info from /users/me.")

    p = sub.add_parser("search", help="Search Notion pages or databases.")
    p.add_argument("--query", default="")
    p.add_argument("--filter-object", choices=["page", "database"], default=None)
    p.add_argument("--page-size", type=int, default=25)
    p.add_argument("--start-cursor", default=None)

    p = sub.add_parser("get", help="Retrieve a page, database, or block.")
    p.add_argument("kind", choices=["page", "database", "block"])
    p.add_argument("id")

    p = sub.add_parser("query", help="Query a database.")
    p.add_argument("database_id")
    p.add_argument("--filter-json", default=None)
    p.add_argument("--filter-file", default=None)
    p.add_argument("--sorts-json", default=None)
    p.add_argument("--sorts-file", default=None)
    p.add_argument("--page-size", type=int, default=25)
    p.add_argument("--start-cursor", default=None)

    p = sub.add_parser("create-page", help="Create a page under a database or parent page.")
    parent = p.add_mutually_exclusive_group(required=True)
    parent.add_argument("--parent-database-id", default=None)
    parent.add_argument("--parent-page-id", default=None)
    p.add_argument("--properties-json", default="{}")
    p.add_argument("--properties-file", default=None)
    p.add_argument("--children-json", default=None)
    p.add_argument("--children-file", default=None)
    p.add_argument("--icon-json", default=None)
    p.add_argument("--cover-json", default=None)

    p = sub.add_parser("update-page", help="Update page properties or archive state.")
    p.add_argument("page_id")
    p.add_argument("--properties-json", default=None)
    p.add_argument("--properties-file", default=None)
    p.add_argument("--archived", choices=["true", "false"], default=None)
    p.add_argument("--icon-json", default=None)
    p.add_argument("--cover-json", default=None)

    p = sub.add_parser("append-blocks", help="Append child blocks to a block or page.")
    p.add_argument("block_id")
    p.add_argument("--children-json", default=None)
    p.add_argument("--children-file", default=None)
    p.add_argument("--after", default=None)

    p = sub.add_parser("raw", help="Send a raw Notion API request.")
    p.add_argument("method")
    p.add_argument("path")
    p.add_argument("--body-json", default=None)
    p.add_argument("--body-file", default=None)
    p.add_argument("--query", default=None)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    client = NotionClient(get_token())

    if args.command == "whoami":
        print_json(client.request("GET", "/users/me"))
        return

    if args.command == "search":
        body: Dict[str, Any] = {"query": args.query, "page_size": args.page_size}
        if args.filter_object:
            body["filter"] = {"value": args.filter_object, "property": "object"}
        if args.start_cursor:
            body["start_cursor"] = args.start_cursor
        print_json(client.request("POST", "/search", body))
        return

    if args.command == "get":
        path_map = {
            "page": f"/pages/{args.id}",
            "database": f"/databases/{args.id}",
            "block": f"/blocks/{args.id}",
        }
        print_json(client.request("GET", path_map[args.kind]))
        return

    if args.command == "query":
        body: Dict[str, Any] = {"page_size": args.page_size}
        filter_obj = parse_json_arg(args.filter_json, args.filter_file)
        sorts_obj = parse_json_arg(args.sorts_json, args.sorts_file)
        if filter_obj is not None:
            body["filter"] = filter_obj
        if sorts_obj is not None:
            body["sorts"] = sorts_obj
        if args.start_cursor:
            body["start_cursor"] = args.start_cursor
        print_json(client.request("POST", f"/databases/{args.database_id}/query", body))
        return

    if args.command == "create-page":
        properties = parse_json_arg(args.properties_json, args.properties_file) or {}
        children = parse_json_arg(args.children_json, args.children_file)
        icon = parse_json_arg(args.icon_json)
        cover = parse_json_arg(args.cover_json)
        parent: Dict[str, str]
        if args.parent_database_id:
            parent = {"database_id": args.parent_database_id}
        else:
            parent = {"page_id": args.parent_page_id}
        body: Dict[str, Any] = {"parent": parent, "properties": properties}
        if children is not None:
            body["children"] = children
        if icon is not None:
            body["icon"] = icon
        if cover is not None:
            body["cover"] = cover
        print_json(client.request("POST", "/pages", body))
        return

    if args.command == "update-page":
        body: Dict[str, Any] = {}
        properties = parse_json_arg(args.properties_json, args.properties_file)
        icon = parse_json_arg(args.icon_json)
        cover = parse_json_arg(args.cover_json)
        if properties is not None:
            body["properties"] = properties
        if args.archived is not None:
            body["archived"] = args.archived == "true"
        if icon is not None:
            body["icon"] = icon
        if cover is not None:
            body["cover"] = cover
        print_json(client.request("PATCH", f"/pages/{args.page_id}", body))
        return

    if args.command == "append-blocks":
        children = parse_json_arg(args.children_json, args.children_file)
        if children is None:
            raise SystemExit("append-blocks requires --children-json or --children-file")
        body: Dict[str, Any] = {"children": children}
        if args.after:
            body["after"] = args.after
        print_json(client.request("PATCH", f"/blocks/{args.block_id}/children", body))
        return

    if args.command == "raw":
        body = parse_json_arg(args.body_json, args.body_file)
        print_json(client.request(args.method, args.path, body, args.query))
        return


if __name__ == "__main__":
    main()
