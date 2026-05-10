# Buffer API Reference Notes

Sources checked on 2026-04-22:

- Quick Start: https://developers.buffer.com/guides/getting-started.html
- Authentication: https://developers.buffer.com/guides/authentication.html
- Posts & Scheduling: https://developers.buffer.com/guides/posts-and-scheduling.html
- Ideas: https://developers.buffer.com/guides/ideas.html
- Pagination: https://developers.buffer.com/guides/pagination.html
- Rate Limits: https://developers.buffer.com/guides/api-limits.html
- GraphQL Reference: https://developers.buffer.com/reference.html

## Endpoint and Auth

- GraphQL endpoint: `https://api.buffer.com`
- Send requests as `POST` with `Content-Type: application/json`.
- Send `Authorization: Bearer <token>`.
- API keys act on the user's Buffer account and can access all organizations/channels in that account. There is no per-org API-key scoping in the docs.

## Core Model

```text
Account
  Organizations
    Channels
      Posts
    Ideas
```

Typical flow:

1. Query `account { organizations { id name } }`.
2. Query `channels(input: { organizationId })`.
3. Create or list posts against a channel, or create ideas against an organization.

## Queries

- `account`: account ID/email/preferences/organizations.
- `channel(input: { id })`: one channel.
- `channels(input: { organizationId, filter })`: all channels for an organization.
- `dailyPostingLimits(input: { channelIds, date })`: sent/scheduled/limit status.
- `post(input: { id })`: one post.
- `posts(input: PostsInput!, first: Int, after: String)`: paginated posts.

`PostsFiltersInput` fields:

- `channelIds: [ChannelId!]`
- `startDate: DateTime`
- `endDate: DateTime`
- `status: [PostStatus!]`
- `tags: TagComparator`
- `tagIds: [TagId!]`
- `dueAt: DateTimeComparator`
- `createdAt: DateTimeComparator`

`PostsInput` fields:

- `organizationId: OrganizationId!`
- `filter: PostsFiltersInput`
- `sort: [PostSortInput!]`

## Mutations

- `createPost(input: CreatePostInput!)`
- `editPost(input: EditPostInput!)`
- `deletePost(input: DeletePostInput!)`
- `createIdea(input: CreateIdeaInput!)`

Always include success and error fragments where the schema allows them.

## CreatePostInput

Useful fields:

- `channelId: ChannelId!`
- `text: String`
- `schedulingType: SchedulingType!`
- `mode: ShareMode!`
- `dueAt: DateTime`
- `assets: AssetsInput`
- `metadata: PostInputMetaData`
- `tagIds: [TagId!]`
- `source: String`
- `aiAssisted: Boolean`
- `saveToDraft: Boolean`
- `ideaId: IdeaId`
- `draftId: DraftId`

`AssetsInput` supports:

- `images: [ImageAssetInput!]`
- `videos: [VideoAssetInput!]`
- `documents: [DocumentAssetInput!]`
- `link: LinkAssetInput`

Media assets are URL-based. Do not assume direct local file upload.

## Ideas

`CreateIdeaInput` fields:

- `organizationId: ID!`
- `content: IdeaContentInput!`
- `cta: String`
- `group: IdeaGroupInput`
- `templateId: String`

`IdeaContentInput` supports:

- `title`
- `text`
- `media`
- `tags`
- `aiAssisted`
- `services`
- `date`

## Enums

`PostStatus`:

- `draft`
- `needs_approval`
- `scheduled`
- `sending`
- `sent`
- `error`

`ShareMode`:

- `addToQueue`
- `shareNow`
- `shareNext`
- `customScheduled`
- `recommendedTime`

`SchedulingType`:

- `automatic`
- `notification`

`Service` values documented in the reference:

- `instagram`
- `facebook`
- `twitter`
- `linkedin`
- `pinterest`
- `tiktok`
- `googlebusiness`
- `startPage`
- `mastodon`
- `youtube`
- `threads`
- `bluesky`

The posts guide says the public post creation API supports Instagram, Threads, LinkedIn, X/Twitter, Facebook, Google Business Profiles, Mastodon, YouTube, Pinterest, and Bluesky.

## Rate and Query Limits

- Third-party clients: 100 requests per 15 minutes.
- Unknown/unauthenticated: 50 requests per 15 minutes.
- Account overall: 2000 requests per 15 minutes.
- Respect `RateLimit-Limit`, `RateLimit-Remaining`, and `RateLimit-Reset` headers.
- On 429, inspect GraphQL error extensions for `retryAfter`.
- Query complexity max: 175,000 points.
- Query depth max: 25.
- Alias max: 30.
- Directive max: 50.
- Query document max: 15,000 tokens.

## OAuth Notes

The API also supports OAuth 2.0 Authorization Code with PKCE for apps that access other users' accounts. This local skill is configured for the user's own API key, not OAuth.
