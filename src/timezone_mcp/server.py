"""MCP server entry point."""

from __future__ import annotations

from typing import Literal

from mcp.server.fastmcp import FastMCP

from timezone_mcp.conversion import ConversionResult
from timezone_mcp.conversion import convert_time as convert_time_impl

mcp = FastMCP("Time Zone Converter")


@mcp.tool(
    name="convert_time",
    description=(
        "Convert a timestamp from a source timezone. Returns configured default "
        "timezones plus any requested additional timezones, omitting the source "
        "timezone when it would duplicate the input."
    ),
)
def convert_time(
    time: str,
    source_timezone: str | None = None,
    output_timezones: list[str] | None = None,
    fold: Literal[0, 1] = 0,
) -> ConversionResult:
    return convert_time_impl(
        time=time,
        source_timezone=source_timezone,
        output_timezones=output_timezones,
        fold=fold,
    )


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
