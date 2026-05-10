---
name: paper-mcp
description: "Use when editing an open Paper board through the local Paper MCP server at http://127.0.0.1:29979/mcp. Prefer this over Computer Use for Paper canvas reads/writes, image placement, HTML writes, node inspection, screenshots, and exports."
---

# Paper MCP

Use this skill for direct Paper board work. The local Paper desktop app exposes an MCP server at:

```bash
http://127.0.0.1:29979/mcp
```

The reusable CLI wrapper is:

```bash
/Users/rileybrown/.codex/tools/paper_mcp.py
```

## Required Workflow

1. Load the Paper guide once per session:

```bash
/Users/rileybrown/.codex/tools/paper_mcp.py call get_guide '{"topic":"paper-mcp-instructions"}'
```

2. Inspect the current board:

```bash
/Users/rileybrown/.codex/tools/paper_mcp.py call get_basic_info '{}'
/Users/rileybrown/.codex/tools/paper_mcp.py call get_selection '{}'
```

3. For image placement, use `write_html` with absolute local image paths through `paper-asset://`:

```bash
/Users/rileybrown/.codex/tools/paper_mcp.py call write_html '{"targetNodeId":"root_node_1-0","mode":"insert-children","html":"<img layer-name=\"Example\" src=\"paper-asset:///absolute/path/image.jpg\" style=\"position:absolute; left:0px; top:0px; width:320px; height:180px; object-fit:cover;\" />"}'
```

4. Verify meaningful changes with `get_screenshot`.

5. Always finish:

```bash
/Users/rileybrown/.codex/tools/paper_mcp.py call finish_working_on_nodes '{}'
```

## Notes

- Do not use Computer Use for Paper board edits when this MCP server is reachable.
- Do not expose raw node IDs in final user-facing replies.
- Deleting Paper nodes changes board data; confirm with the user immediately before deletion.
