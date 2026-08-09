from __future__ import annotations

from pathlib import Path

import pytest

from timezone_mcp.config import load_config
from timezone_mcp.conversion import convert_time


def test_rejects_empty_environment_value(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TIMEZONE_MCP_ALWAYS_TIMEZONES", "")

    with pytest.raises(ValueError, match="cannot be empty"):
        load_config()


def test_rejects_malformed_environment_json(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TIMEZONE_MCP_ALWAYS_TIMEZONES", '["UTC"')

    with pytest.raises(ValueError, match="is not valid JSON"):
        load_config()


def test_json_environment_value_can_disable_default_zones(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TIMEZONE_MCP_ALWAYS_TIMEZONES", "[]")

    assert load_config().always_timezones == []


def test_environment_timezones_override_config_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_path = tmp_path / "timezone-mcp.json"
    config_path.write_text('{"always_timezones": ["Pacific"]}', encoding="utf-8")
    monkeypatch.setenv("TIMEZONE_MCP_ALWAYS_TIMEZONES", "UTC")

    config = load_config(str(config_path))

    assert config.always_timezones == ["UTC"]


def test_rejects_missing_config_file(tmp_path: Path) -> None:
    missing_path = tmp_path / "missing.json"

    with pytest.raises(ValueError, match="config file does not exist"):
        load_config(str(missing_path))


def test_rejects_malformed_config_file(tmp_path: Path) -> None:
    config_path = tmp_path / "timezone-mcp.json"
    config_path.write_text("{", encoding="utf-8")

    with pytest.raises(ValueError, match="config file is not valid JSON"):
        load_config(str(config_path))


def test_rejects_invalid_configured_timezone(tmp_path: Path) -> None:
    config_path = tmp_path / "timezone-mcp.json"
    config_path.write_text('{"always_timezones": ["Mars/Olympus"]}', encoding="utf-8")

    with pytest.raises(ValueError, match="unknown timezone"):
        convert_time("2026-07-16 09:00", source_timezone="UTC", config_path=str(config_path))
