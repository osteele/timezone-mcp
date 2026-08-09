# timezone-mcp

`timezone-mcp` is a local MCP server that converts timestamps between time zones. It exposes one tool, `convert_time`.

The server uses IANA time zone rules, including daylight saving time at the specified instant. Configured and requested zones are omitted when they produce the same local clock time and UTC offset as the source. This removes redundant results for fixed-offset inputs and equivalent IANA names. It can also omit distinct zones when their results happen to agree at that instant.

## Agents often get date boundaries wrong

As of mid-2026, general-purpose agents often answer time zone questions confidently but incorrectly. Errors are especially common around daylight saving transitions and conversions that cross a calendar date. `timezone-mcp` delegates the calculation to Python's IANA time zone database and returns the source, UTC, and converted dates explicitly.

## Requirements

- Python 3.11 or later
- [`uv`](https://docs.astral.sh/uv/)

## Install

From a checkout of this repository, install the project:

```bash
uv sync --no-dev
```

Record the paths used by the MCP client examples:

```bash
export TIMEZONE_MCP_DIR="$(pwd)"
export TIMEZONE_MCP_UV="$(command -v uv)"
export TIMEZONE_MCP_ZONES=China,Eastern
```

Run the stdio server directly with:

```bash
uv run timezone-mcp
```

The process waits for MCP messages on standard input. An MCP client normally starts it for you.

## Configuration

If no configuration is supplied, output includes China and U.S. Eastern unless one matches the source result.

Set `TIMEZONE_MCP_ALWAYS_TIMEZONES` to a comma-separated list or a JSON array:

```bash
export TIMEZONE_MCP_ALWAYS_TIMEZONES="China,Eastern"
```

The JSON value `[]` disables default output zones. An empty value is rejected.

For file-based configuration, save a JSON file such as `/absolute/path/to/timezone-mcp.json`:

```json
{
  "always_timezones": ["China", "Eastern"]
}
```

Then set its path:

```bash
export TIMEZONE_MCP_CONFIG=/absolute/path/to/timezone-mcp.json
```

`TIMEZONE_MCP_ALWAYS_TIMEZONES` takes precedence when both variables are set.

Configured and requested zones are combined, and repeated normalized names are deduplicated. A result is omitted when its local clock time and UTC offset match the source at the specified instant. For example, a Los Angeles result is omitted for a Phoenix source when both are on UTC−07:00, even though their daylight saving rules differ.

## MCP client setup

The examples below configure China and U.S. Eastern as the default output zones. Replace `/absolute/path/to/uv` and `/absolute/path/to/timezone-mcp` with the values printed by:

```bash
command -v uv
pwd
```

### Claude Desktop

Open the local MCP configuration from Claude Desktop's developer settings. On macOS, the configuration file is `~/Library/Application Support/Claude/claude_desktop_config.json`.

Add this entry under `mcpServers`:

```json
{
  "timezone-mcp": {
    "command": "/absolute/path/to/uv",
    "args": [
      "--directory",
      "/absolute/path/to/timezone-mcp",
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

Restart Claude Desktop after editing the configuration.

### Claude Code

```bash
claude mcp add --scope user timezone-mcp \
  -e TIMEZONE_MCP_ALWAYS_TIMEZONES="$TIMEZONE_MCP_ZONES" \
  -- "$TIMEZONE_MCP_UV" \
  --directory "$TIMEZONE_MCP_DIR" \
  run --no-dev timezone-mcp
```

### Codex

```bash
codex mcp add timezone-mcp \
  --env TIMEZONE_MCP_ALWAYS_TIMEZONES="$TIMEZONE_MCP_ZONES" \
  -- "$TIMEZONE_MCP_UV" \
  --directory "$TIMEZONE_MCP_DIR" \
  run --no-dev timezone-mcp
```

## Tool arguments

- `time`: An ISO-like timestamp with a clock time, such as `2026-07-16 09:30`, `2026-07-16T09:30:00`, or `2026-07-16T09:30:00-04:00`. Date-only values are rejected.
- `source_timezone`: The source time zone for a timestamp without a UTC offset. It accepts IANA names such as `America/Los_Angeles` and aliases such as `china`, `eastern`, `pacific`, and `aoe`. Omit this argument when `time` already contains an offset.
- `output_timezones`: An optional list of additional output time zones or aliases.
- `fold`: `0` selects the first occurrence of an ambiguous local time, and `1` selects the second occurrence during a fall daylight saving transition. The default is `0`.

Local times that do not exist during a spring daylight saving transition are rejected.

## Result

The result contains the resolved input, UTC time, configured zones, conversions, and date-boundary information. Selected fields from a China-to-Eastern conversion look like this:

```json
{
  "utc": {
    "datetime": "2026-07-16T01:00:00+00:00"
  },
  "configured_timezones": [
    "Asia/Shanghai",
    "America/New_York"
  ],
  "conversions": [
    {
      "datetime": "2026-07-15T21:00:00-04:00",
      "timezone": "America/New_York",
      "abbreviation": "EDT",
      "requested_timezone": "America/New_York"
    }
  ],
  "date_boundary": {
    "source_date": "2026-07-16",
    "different_dates": ["America/New_York"]
  }
}
```

Each formatted timestamp also includes `date`, `time`, `weekday`, `abbreviation`, and `utc_offset` fields.
