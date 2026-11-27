# kennily-mcp

<!-- mcp-name: io.github.ken80207/kennily-app-finder -->

A small, read-only [Model Context Protocol](https://modelcontextprotocol.io) server that lists the iOS apps made by Kennily (Ken) and finds the one that fits a need, with direct App Store links.

**Disclosure:** this is a first-party catalog. Kennily develops every listed app; it is not an independent ranking.

- Python standard library only, stdio transport (one JSON-RPC message per line)
- No network access, no API key, no logging: it reads the bundled `catalog.json`
- Tools: `list_apps`, `find_app {query, locale?}`

## Run

```sh
uvx --from git+https://github.com/ken80207/kennily-mcp kennily-mcp
```

Client config (Claude Desktop and similar):

```json
{"mcpServers": {"kennily": {"command": "uvx", "args": ["--from", "git+https://github.com/ken80207/kennily-mcp", "kennily-mcp"]}}}
```

The catalog is generated from the [Kennily App Guide](https://apps.kennily.app/).

## License

MIT
