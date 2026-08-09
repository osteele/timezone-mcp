from __future__ import annotations

from pathlib import Path
from typing import cast

import pytest

from timezone_mcp.conversion import convert_time

JsonObject = dict[str, object]


def as_object(value: object) -> JsonObject:
    return cast(JsonObject, value)


def as_objects(value: object) -> list[JsonObject]:
    return cast(list[JsonObject], value)


def test_converts_china_to_edt_in_july() -> None:
    result = convert_time("2026-07-16 09:00", source_timezone="China")
    conversions = as_objects(result["conversions"])
    eastern = conversions[0]
    date_boundary = as_object(result["date_boundary"])

    assert [item["timezone"] for item in conversions] == ["America/New_York"]
    assert eastern["datetime"] == "2026-07-15T21:00:00-04:00"
    assert eastern["abbreviation"] == "EDT"
    assert date_boundary["different_dates"] == ["America/New_York"]


def test_converts_china_to_est_in_january() -> None:
    result = convert_time("2026-01-16 09:00", source_timezone="Asia/Shanghai")
    conversions = as_objects(result["conversions"])
    eastern = conversions[0]

    assert [item["timezone"] for item in conversions] == ["America/New_York"]
    assert eastern["datetime"] == "2026-01-15T20:00:00-05:00"
    assert eastern["abbreviation"] == "EST"


def test_converts_aoe_to_china_next_day() -> None:
    result = convert_time("2026-07-16 23:30", source_timezone="AoE")
    conversions = as_objects(result["conversions"])
    china = conversions[0]
    eastern = conversions[1]
    date_boundary = as_object(result["date_boundary"])

    assert china["datetime"] == "2026-07-17T19:30:00+08:00"
    assert eastern["abbreviation"] == "EDT"
    assert date_boundary["different_dates"] == ["Asia/Shanghai", "America/New_York"]


def test_includes_requested_extra_timezones_without_duplicate_core_zones() -> None:
    result = convert_time(
        "2026-07-16T09:00:00-04:00",
        output_timezones=["UTC", "eastern", "Pacific"],
    )

    conversions = as_objects(result["conversions"])
    zones = [item["timezone"] for item in conversions]

    assert zones == ["Asia/Shanghai", "UTC", "America/Los_Angeles"]
    assert conversions[1]["datetime"] == "2026-07-16T13:00:00+00:00"
    assert conversions[2]["abbreviation"] == "PDT"


def test_omits_equivalent_iana_source_timezone() -> None:
    result = convert_time("2026-07-16 09:00", source_timezone="US/Eastern")
    conversions = as_objects(result["conversions"])

    assert [item["timezone"] for item in conversions] == ["Asia/Shanghai"]


def test_configures_default_timezones(tmp_path: Path) -> None:
    config_path = tmp_path / "timezone-mcp.json"
    config_path.write_text('{"always_timezones": ["UTC"]}', encoding="utf-8")

    result = convert_time(
        "2026-07-16 09:00",
        source_timezone="China",
        config_path=str(config_path),
    )
    conversions = as_objects(result["conversions"])

    assert [item["timezone"] for item in conversions] == ["UTC"]
    assert conversions[0]["datetime"] == "2026-07-16T01:00:00+00:00"


def test_configures_default_timezones_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TIMEZONE_MCP_ALWAYS_TIMEZONES", "UTC,Pacific")

    result = convert_time("2026-07-16 09:00", source_timezone="China")
    conversions = as_objects(result["conversions"])

    assert [item["timezone"] for item in conversions] == ["UTC", "America/Los_Angeles"]


def test_requires_source_timezone_for_naive_time() -> None:
    with pytest.raises(ValueError, match="source_timezone is required"):
        convert_time("2026-07-16 09:00")


def test_rejects_date_only_time() -> None:
    with pytest.raises(ValueError, match="date-only"):
        convert_time("2026-07-16", source_timezone="China")


def test_rejects_nonexistent_local_time() -> None:
    with pytest.raises(ValueError, match="not a valid local time"):
        convert_time("2026-03-08 02:30", source_timezone="America/New_York")
