---
name: remove-image-background
description: Remove backgrounds from images with remove.bg and save the cutout result locally. Use when Codex needs to cut out a subject from a local image file or image URL, produce a transparent PNG or WebP, export a flat JPG, or verify remove.bg account access before running image background removal.
---

# Remove Image Background

Use this skill to remove the background from a single image through the remove.bg API.

## Setup

Store the API key on this machine before the first real run:

```bash
/Users/rileybrown/.codex/skills/remove-image-background/scripts/remove_bg.py setup --key "<REMOVE_BG_API_KEY>"
```

Check configuration and account access:

```bash
/Users/rileybrown/.codex/skills/remove-image-background/scripts/remove_bg.py config:show
/Users/rileybrown/.codex/skills/remove-image-background/scripts/remove_bg.py account:get
```

Notes:

- `setup` stores the key in the macOS Keychain by default.
- `REMOVE_BG_API_KEY` or `REMOVEBG_API_KEY` overrides stored config for one-off runs.
- Use `--location global` only when a plain config file is explicitly preferred over Keychain storage.

## Quick Start

Remove the background from a local image and save a sibling output automatically:

```bash
/Users/rileybrown/.codex/skills/remove-image-background/scripts/remove_bg.py remove /absolute/path/to/image.jpg
```

Remove the background from an image URL and write to an explicit output path:

```bash
/Users/rileybrown/.codex/skills/remove-image-background/scripts/remove_bg.py remove "https://example.com/image.jpg" --output /tmp/image-no-bg.png
```

## Common Options

- `--output <path>`: choose the output path. When omitted, local files become `<name>.no-bg.<ext>` beside the input file, and URLs save into the current directory with a sanitized filename.
- `--format png|webp|jpg|zip`: choose the output format. Default is the `--output` file extension when you provide one, otherwise `webp` for higher-resolution transparent output.
- `--size <value>`: pass the remove.bg `size` parameter. Default `50MP`.
- `--type <value>`: pass a foreground hint such as `person`, `product`, `car`, `graphic`, `animal`, or `transportation`.
- `--crop`: ask remove.bg to crop empty margins.
- `--bg-color <hex>`: flatten the output onto a solid background color instead of transparency.
- `--max-retries <n>`: retry `429` responses by honoring `Retry-After`. Default `2`.

## Workflow

1. Run `config:show` if background removal has not been configured on this machine yet.
2. Run `account:get` when you want to verify the key without spending a removal call.
3. Use `remove` with a local path when the user gives you an attached image or a file on disk.
4. Use `remove` with a URL when the image already lives on the web and downloading it first adds no value.
5. The default path favors maximum quality: `size=50MP` plus `webp` when no output extension forces another format.
6. Prefer `png` only when downstream tooling specifically requires PNG. Use `jpg` only when transparency is not needed.

## Output

- Successful runs write the processed file locally and print JSON with the output path plus useful response headers such as credits charged and detected foreground type.
- Failed runs exit non-zero and include the HTTP status plus the response body excerpt.
