# timezone-mcp

`timezone-mcp` is a local MCP server that converts timestamps between time zones. It exposes one tool, `convert_time`.

The server uses IANA time zone rules, including daylight saving time at the specified instant, and returns the source, UTC, and converted times with their dates.

## Agents often get date boundaries wrong

As of mid-2026, general-purpose agents often answer time zone questions confidently but incorrectly. Errors are especially common around daylight saving transitions and conversions that cross a calendar date. `timezone-mcp` delegates the calculation to Python's IANA time zone database and returns each date explicitly.

## Install

Requires [`uv`](https://docs.astral.sh/uv/), which installs Python for the tool if the machine does not have a suitable version. Nothing to clone: [add-mcp](https://github.com/neon-solutions/add-mcp) registers the server with your agent in one command, and knows where each client keeps its config.

```bash
npx add-mcp "$(command -v uvx)" \
  --args --from --args git+https://github.com/osteele/timezone-mcp@v0.1.0 --args timezone-mcp \
  --name timezone-mcp \
  --env TIMEZONE_MCP_ALWAYS_TIMEZONES="China,Eastern" \
  --global --agent claude-code --agent codex
```

Every argument after the command needs its own `--args`. add-mcp does not split a quoted command string, so folding them into the first argument writes a command name containing spaces, without reporting an error. Drop `--global` to register the server for one project instead of the whole machine, and see `npx add-mcp list-agents` for the other clients it supports.

That writes an entry equivalent to this, which you can also add by hand to whichever file your client uses:

```json
{
  "timezone-mcp": {
    "command": "/absolute/path/to/uvx",
    "args": [
      "--from",
      "git+https://github.com/osteele/timezone-mcp@v0.1.0",
      "timezone-mcp"
    ],
    "env": {
      "TIMEZONE_MCP_ALWAYS_TIMEZONES": "China,Eastern"
    }
  }
}
```

Claude Desktop keeps that file at `~/Library/Application Support/Claude/claude_desktop_config.json` on macOS, under `mcpServers`; open it from the developer settings, and restart the app after editing. Claude Code and Codex also take it from their own CLIs:

```bash
claude mcp add --scope user timezone-mcp \
  -e TIMEZONE_MCP_ALWAYS_TIMEZONES="China,Eastern" \
  -- "$(command -v uvx)" --from git+https://github.com/osteele/timezone-mcp@v0.1.0 timezone-mcp

codex mcp add timezone-mcp \
  --env TIMEZONE_MCP_ALWAYS_TIMEZONES="China,Eastern" \
  -- "$(command -v uvx)" --from git+https://github.com/osteele/timezone-mcp@v0.1.0 timezone-mcp
```

`@v0.1.0` pins the install to a tagged release, so a later push to `main` cannot change what an already-registered client runs. Drop it to track `main`, or raise it when a newer tag exists.

To run the server by hand, `uvx --from git+https://github.com/osteele/timezone-mcp@v0.1.0 timezone-mcp` waits for MCP messages on standard input, so it will appear to hang. That is what a client expects; press Ctrl-C.

## Configuration

Every result carries the zones you asked for. `TIMEZONE_MCP_ALWAYS_TIMEZONES` adds zones that appear in every result without being requested. With no configuration, those standing zones are China and U.S. Eastern.

Set it to a comma-separated list or a JSON array:

```bash
export TIMEZONE_MCP_ALWAYS_TIMEZONES="China,Eastern"
```

The JSON value `[]` disables standing zones entirely. An empty string is rejected.

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

Standing and requested zones are combined, and repeated names are deduplicated after normalization. A zone is dropped from the result when its local clock time and UTC offset match the source at that instant. A Los Angeles result is dropped for a Phoenix source when both are on UTC−07:00, for example, even though their daylight saving rules differ.

## Tool arguments

- `time`: An ISO-like timestamp with a clock time, such as `2026-07-16 09:30`, `2026-07-16T09:30:00`, or `2026-07-16T09:30:00-04:00`. Date-only values are rejected.
- `source_timezone`: The source time zone for a timestamp without a UTC offset. Omit it when `time` already contains an offset.
- `output_timezones`: An optional list of additional output time zones.
- `fold`: `0` selects the first occurrence of an ambiguous local time, and `1` selects the second occurrence during a fall daylight saving transition. The default is `0`.

Local times that do not exist during a spring daylight saving transition are rejected.

### Time zone names

Any zone argument accepts an IANA name, such as `America/Los_Angeles` or `Europe/Berlin`.

Five zones also have short aliases, matched case-insensitively:

| Zone | Aliases |
| --- | --- |
| `AoE` (fixed UTC−12) | `aoe`, `anywhere on earth` |
| `Asia/Shanghai` | `china`, `beijing`, `shanghai`, `china standard time`, `cst china`, `beijing time` |
| `America/New_York` | `eastern`, `et`, `est`, `edt`, `us eastern`, `u.s. eastern`, `new york`, `eastern time` |
| `America/Los_Angeles` | `pacific`, `pt`, `pst`, `pdt`, `us pacific`, `u.s. pacific`, `pacific time` |
| `UTC` | `utc`, `z` |

That table is the whole alias set. Anything else must be a valid IANA name; an unrecognized name is rejected with `unknown timezone`.

`AoE` is Anywhere on Earth, the fixed UTC−12 offset that conference and journal deadlines are usually quoted in. It is the last place on the planet where a given calendar date is still in progress, so a deadline stated as AoE expires later than the same wall-clock time anywhere else.

## Result

The result contains the resolved input, UTC time, standing zones, conversions, and date-boundary information. Selected fields from a China-to-Eastern conversion look like this:

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

`date_boundary.different_dates` names the zones whose calendar date differs from the source, which is the case these conversions most often get wrong.

Each formatted timestamp also includes `date`, `time`, `weekday`, `abbreviation`, and `utc_offset` fields.

## Development

```bash
git clone https://github.com/osteele/timezone-mcp
cd timezone-mcp
uv sync
uv run --frozen pytest
uv run --frozen ruff check .
uv run --frozen ty check
```

To point a client at a checkout rather than at the published source, replace the `--from git+...` argument with `--directory /absolute/path/to/timezone-mcp run --no-dev`, invoking `uv` instead of `uvx`.

## Related

`timezone-mcp` is one of a set of tools for agent sessions and the environments
they run in, listed at
[osteele.com/software/agent-tools](https://osteele.com/software/agent-tools).
