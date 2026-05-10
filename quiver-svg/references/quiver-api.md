# QuiverAI API Reference Notes

Source docs checked on 2026-04-22:

- Quickstart: https://docs.quiver.ai/getting-started/quickstart
- Text to SVG: https://docs.quiver.ai/models/text-to-svg
- Image to SVG: https://docs.quiver.ai/models/image-to-svg
- List models: https://docs.quiver.ai/api-reference/models/list-models

## Authentication

Use bearer auth with the API key from `QUIVERAI_API_KEY` or macOS Keychain service `codex-quiver-ai`.

```http
Authorization: Bearer <QUIVERAI_API_KEY>
```

Do not commit keys. The docs recommend storing the key in the environment; this skill also supports Keychain for durable local use.

## Endpoints

`GET /v1/models`

Returns models available to the authenticated organization. Use before relying on a specific model when availability is uncertain.

`POST /v1/svgs/generations`

Generates one or more SVGs from a text prompt and optional references.

Required body:

```json
{
  "model": "arrow-1.1",
  "prompt": "Generate an icon of a unicorn",
  "stream": false
}
```

Optional fields include `instructions`, `references`, `n`, `temperature`, `top_p`, `presence_penalty`, and `max_output_tokens`.

`POST /v1/svgs/vectorizations`

Converts PNG, JPEG, or WebP input into SVG.

Required body:

```json
{
  "model": "arrow-1.1",
  "stream": false,
  "image": {
    "url": "https://example.com/logo.png"
  }
}
```

The `image` object can use `url` or `base64`. Optional fields include `auto_crop`, `target_size`, `temperature`, `top_p`, `presence_penalty`, and `max_output_tokens`.

## Models

Default to `arrow-1.1` for most generation and vectorization requests.

Use `arrow-1.1-max` when the output needs higher fidelity: dense illustrations, technical diagrams, precise logos, alignment-sensitive graphics, or detailed raster image vectorization.

The list-models response in the docs shows:

- `arrow-1`: older model
- `arrow-1.1`: general-purpose current model
- `arrow-1.1-max`: higher-fidelity variant

## Parameter Ranges

Generation:

- `n`: 1 to 16, defaults to 1
- `temperature`: 0 to 2, defaults to 1
- `top_p`: 0 to 1, defaults to 1
- `presence_penalty`: -2 to 2, defaults to 0
- `max_output_tokens`: 1 to 131072
- `references`: model-specific limit, 4 for Arrow 1.1 and 16 for Arrow 1.1 Max

Vectorization:

- `target_size`: 128 to 4096
- `auto_crop`: boolean, useful when the input was not tightly cropped
- Sampling fields match generation.

## Responses

Non-streaming successful responses include:

- `id`
- `created`
- `data`: array of outputs where each item contains `svg` and `mime_type`
- `credits`: billing debit for the request

Deprecated `usage` token fields may appear but should not be used for billing behavior.

## Errors and Rate Limits

Failures return JSON error payloads with fields such as `status`, `code`, `message`, and `request_id`.

Common statuses:

- `401`: missing or invalid API key, or organization billing resolution failed
- `402`: insufficient credits
- `403`: account frozen
- `429`: rate limited

The quickstart states the default generation/vectorization limit is 20 requests per 60 seconds per organization. Respect `Retry-After` and `X-RateLimit-*` headers when present.
