# timezone-mcp

MCP server for precise time zone conversion. It exposes one tool:

- `convert_time`: converts a specified timestamp from a source timezone, returning configured default zones plus any requested additional zones.

Configured or requested zones that produce the same local clock time and UTC offset as the source at the specified instant are omitted. This also removes redundant results for fixed-offset inputs and equivalent IANA names. Distinct zones with different rules can therefore be omitted when they happen to agree at that instant. U.S. Eastern results use `EST` or `EDT` according to the specified instant.

## Install

```bash
uv sync
```

## Run

```bash
uv run timezone-mcp
```

## Configuration

Set `TIMEZONE_MCP_ALWAYS_TIMEZONES` to a comma-separated list. This is the simplest way to configure local MCP client entries:

```bash
TIMEZONE_MCP_ALWAYS_TIMEZONES="China,Eastern"
```

This variable takes precedence over `TIMEZONE_MCP_CONFIG`. Use the JSON value `[]` to configure no default output zones; an empty value is rejected as a likely configuration error.

Alternatively, set `TIMEZONE_MCP_CONFIG` to a JSON file:

```json
{
  "always_timezones": ["China", "Eastern"]
}
```

If no config is specified, the built-in defaults are China and U.S. Eastern.

The configured zones are always included unless they are the same as the source timezone. For example, with `China,Eastern`, converting from China prints Eastern but omits China; converting from Eastern prints China but omits Eastern.

## MCP Client Install

These examples install the server with the local default zones set to China and U.S. Eastern:

```bash
export TIMEZONE_MCP_DIR=/Users/osteele/code/utils/timezone-mcp
export TIMEZONE_MCP_ZONES=China,Eastern
```

### Claude Desktop

Add this entry under `mcpServers` in `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "timezone-mcp": {
    "command": "/Users/osteele/.local/bin/uv",
    "args": [
      "--directory",
      "/Users/osteele/code/utils/timezone-mcp",
      "run",
      "--no-dev",
      "timezone-mcp"
    ],
    "env": {
      "TIMEZONE_MCP_ALWAYS_TIMEZONES": "China,Eastern"
    }
  }
}
```

Restart Claude Desktop after editing the config.

### Claude Code

```bash
claude mcp add --scope user timezone-mcp \
  -e TIMEZONE_MCP_ALWAYS_TIMEZONES="$TIMEZONE_MCP_ZONES" \
  -- /Users/osteele/.local/bin/uv \
  --directory "$TIMEZONE_MCP_DIR" \
  run --no-dev timezone-mcp
```

### Codex

```bash
codex mcp add timezone-mcp \
  --env TIMEZONE_MCP_ALWAYS_TIMEZONES="$TIMEZONE_MCP_ZONES" \
  -- /Users/osteele/.local/bin/uv \
  --directory "$TIMEZONE_MCP_DIR" \
  run --no-dev timezone-mcp
```

## Tool Arguments

- `time`: Timestamp to convert. ISO-like forms are supported, such as `2026-07-16 09:30`, `2026-07-16T09:30:00`, or `2026-07-16T09:30:00-04:00`.
- `source_timezone`: Source timezone. Required when `time` has no UTC offset. Accepts IANA names such as `America/Los_Angeles`, plus aliases such as `china`, `eastern`, `pacific`, and `aoe`.
- `output_timezones`: Optional list of additional output timezones or aliases.
- `fold`: Use `0` for the first occurrence of an ambiguous local time and `1` for the second occurrence. This matters during fall DST transitions.
