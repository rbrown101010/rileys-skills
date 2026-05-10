# Official Notes

Primary sources used to shape this skill:

- Readwise MCP docs: <https://docs.readwise.io/tools/mcp>
- Readwise MCP landing page: <https://readwise.io/mcp>
- Readwise CLI docs: <https://docs.readwise.io/tools/cli>
- Readwise CLI landing page: <https://readwise.io/cli>

Key points:

- The current official remote MCP endpoint is `https://mcp2.readwise.io/mcp`.
- The official MCP setup for Codex and Codex CLI uses OAuth/browser authentication.
- The official headless, token-based flow is the CLI command:
  `readwise login-with-token <your-access-token>`
- The official docs say the CLI is usually the simpler option for terminal-based agents like Codex.
- The CLI supports readonly mode via:
  `readwise config set readonly true`
