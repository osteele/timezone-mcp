"""Configuration loading for timezone-mcp."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT_ALWAYS_TIMEZONES = ["Asia/Shanghai", "America/New_York"]
CONFIG_ENV_VAR = "TIMEZONE_MCP_CONFIG"
ALWAYS_TIMEZONES_ENV_VAR = "TIMEZONE_MCP_ALWAYS_TIMEZONES"


@dataclass(frozen=True)
class TimezoneConfig:
    always_timezones: list[str]


def load_config(config_path: str | None = None) -> TimezoneConfig:
    env_timezones = os.environ.get(ALWAYS_TIMEZONES_ENV_VAR)
    if env_timezones:
        return TimezoneConfig(always_timezones=_parse_timezone_list(env_timezones))

    path = config_path or os.environ.get(CONFIG_ENV_VAR)
    if path is None:
        return TimezoneConfig(always_timezones=DEFAULT_ALWAYS_TIMEZONES.copy())

    data = _load_json(Path(path).expanduser())
    always_timezones = data.get("always_timezones", DEFAULT_ALWAYS_TIMEZONES)
    if not isinstance(always_timezones, list) or not all(
        isinstance(item, str) for item in always_timezones
    ):
        raise ValueError("always_timezones must be a list of timezone names")

    return TimezoneConfig(always_timezones=always_timezones.copy())


def _parse_timezone_list(value: str) -> list[str]:
    stripped = value.strip()
    if not stripped:
        raise ValueError(f"{ALWAYS_TIMEZONES_ENV_VAR} cannot be empty")

    if stripped.startswith("["):
        parsed = json.loads(stripped)
        if not isinstance(parsed, list) or not all(isinstance(item, str) for item in parsed):
            raise ValueError(f"{ALWAYS_TIMEZONES_ENV_VAR} must be a JSON array of strings")
        return parsed.copy()

    return [item.strip() for item in stripped.split(",") if item.strip()]


def _load_json(path: Path) -> dict[str, object]:
    try:
        with path.open(encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError as exc:
        raise ValueError(f"timezone-mcp config file does not exist: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"timezone-mcp config file is not valid JSON: {path}") from exc

    if not isinstance(data, dict):
        raise ValueError("timezone-mcp config must be a JSON object")

    return data
