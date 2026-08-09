from __future__ import annotations

import asyncio

import pytest
from mcp.shared.memory import create_connected_server_and_client_session

from timezone_mcp.server import mcp


def test_mcp_lists_and_invokes_convert_time(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TIMEZONE_MCP_ALWAYS_TIMEZONES", "UTC")

    async def exercise_protocol() -> None:
        async with create_connected_server_and_client_session(mcp) as session:
            listed = await session.list_tools()
            assert [tool.name for tool in listed.tools] == ["convert_time"]
            output_schema = listed.tools[0].outputSchema
            assert output_schema is not None
            assert output_schema["required"] == [
                "input",
                "utc",
                "configured_timezones",
                "conversions",
                "date_boundary",
            ]

            result = await session.call_tool(
                "convert_time",
                arguments={"time": "2026-07-16 09:00", "source_timezone": "China"},
            )

            assert not result.isError
            assert result.structuredContent is not None
            assert result.structuredContent["utc"]["datetime"] == "2026-07-16T01:00:00+00:00"

    asyncio.run(exercise_protocol())
