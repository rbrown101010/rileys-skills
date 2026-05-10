# API Notes

## SerpAPI

- Google Images endpoint: `https://serpapi.com/google-images-api`
- Request base used by the script: `https://serpapi.com/search.json`
- Required parameter: `engine=google_images`
- Key env vars accepted by the script:
  - `SERP_API_KEY`
  - `SERPAPI_API_KEY`

The script reads `images_results` and prefers the `original` image URL, with `thumbnail` as a fallback.

## Firecrawl

- API intro: `https://docs.firecrawl.dev/api-reference/introduction`
- Scrape docs: `https://docs.firecrawl.dev/features/scrape`
- Map docs: `https://docs.firecrawl.dev/features/map`
- Base URL: `https://api.firecrawl.dev`
- Auth header: `Authorization: Bearer <token>`
- Key env var accepted by the script:
  - `FIRECRAWL_API_KEY`

The script uses:

- `POST /v2/scrape` with `formats=["images"]` for one-page extraction
- `POST /v2/map` to discover relevant site URLs before scraping them

## Downloader Behavior

- The script skips non-HTTP URLs.
- It removes common transform query parameters such as `w`, `h`, `q`, `fm`, `fit`, `crop`, and `dpr` by default before downloading.
- It records one `manifest.json` per output folder with all runs and file metadata.
