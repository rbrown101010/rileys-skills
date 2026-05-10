# API Notes

These are the endpoints this skill is built around.

## SerpApi

- YouTube search: `GET https://serpapi.com/search.json`
- Required params:
  - `engine=youtube`
  - `search_query=...`
  - `api_key=...`
- Useful optional params:
  - `gl`
  - `hl`
  - `sp`
  - `no_cache=true`
- Pagination:
  - read `serpapi_pagination.next_page_token`
  - pass that token back as `sp` on the next request

## Supadata

- Transcript: `GET https://api.supadata.ai/v1/transcript`
  - accepts `url`, `lang`, `text`, `mode`
  - `mode` can be `native`, `auto`, or `generate`
  - may return a `jobId` for async processing
- Transcript job status: `GET https://api.supadata.ai/v1/transcript/{jobId}`
- Channel metadata: `GET https://api.supadata.ai/v1/youtube/channel?id=...`
- Channel videos: `GET https://api.supadata.ai/v1/youtube/channel/videos?id=...&limit=...&type=...`
- Video metadata: `GET https://api.supadata.ai/v1/metadata?url=...`

## Notes

- Supadata’s older `/v1/youtube/transcript` endpoint is deprecated. Use `/v1/transcript`.
- Supadata channel video responses return IDs, so this skill fetches video metadata separately when channel inspection is requested.
- Keep transcript fetches targeted. Search is cheap; transcript enrichment should be used when the user needs actual wording or claims.
