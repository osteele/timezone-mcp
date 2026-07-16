"""Time zone conversion logic for the MCP tool."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from timezone_mcp.config import load_config

UTC_MINUS_12 = timezone(timedelta(hours=-12), name="AoE")
CHINA_ZONE = "Asia/Shanghai"
EASTERN_ZONE = "America/New_York"

ALIASES: dict[str, str] = {
    "aoe": "AoE",
    "anywhere on earth": "AoE",
    "china": CHINA_ZONE,
    "china standard time": CHINA_ZONE,
    "cst china": CHINA_ZONE,
    "beijing": CHINA_ZONE,
    "beijing time": CHINA_ZONE,
    "shanghai": CHINA_ZONE,
    "eastern": EASTERN_ZONE,
    "eastern time": EASTERN_ZONE,
    "et": EASTERN_ZONE,
    "est": EASTERN_ZONE,
    "edt": EASTERN_ZONE,
    "us eastern": EASTERN_ZONE,
    "u.s. eastern": EASTERN_ZONE,
    "new york": EASTERN_ZONE,
    "pacific": "America/Los_Angeles",
    "pacific time": "America/Los_Angeles",
    "pt": "America/Los_Angeles",
    "pst": "America/Los_Angeles",
    "pdt": "America/Los_Angeles",
    "us pacific": "America/Los_Angeles",
    "u.s. pacific": "America/Los_Angeles",
    "utc": "UTC",
    "z": "UTC",
}


@dataclass(frozen=True)
class ResolvedZone:
    key: str
    tz: tzinfo


def convert_time(
    time: str,
    source_timezone: str | None = None,
    output_timezones: list[str] | None = None,
    fold: Literal[0, 1] = 0,
    config_path: str | None = None,
) -> dict[str, object]:
    """Convert a timestamp to configured and requested timezones."""
    parsed = _parse_datetime(time)
    source = _resolve_source(parsed, source_timezone, fold)
    requested_zones = output_timezones or []
    config = load_config(config_path)

    utc_time = source.astimezone(UTC)
    source_key = _source_zone_key(source, source_timezone)
    zone_keys = _dedupe_without_source(
        [*config.always_timezones, *requested_zones],
        source_key=source_key,
    )
    conversions = [_format_conversion(utc_time, zone_key) for zone_key in zone_keys]

    return {
        "input": {
            "time": time,
            "source_timezone": source_timezone,
            "fold": fold,
            "resolved": _format_datetime(source),
        },
        "utc": _format_datetime(utc_time),
        "configured_timezones": [_normalize_zone_key(zone) for zone in config.always_timezones],
        "conversions": conversions,
        "date_boundary": {
            "source_date": source.date().isoformat(),
            "different_dates": [
                conversion["timezone"]
                for conversion in conversions
                if conversion["date"] != source.date().isoformat()
            ],
        },
    }


def _parse_datetime(value: str) -> datetime:
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = f"{normalized[:-1]}+00:00"
    normalized = normalized.replace(" ", "T", 1)

    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError(
            "time must be an ISO-like timestamp such as '2026-07-16 09:30' "
            "or '2026-07-16T09:30:00-04:00'"
        ) from exc

    if (
        parsed.hour == parsed.minute == parsed.second == parsed.microsecond == 0
        and "T" not in normalized
    ):
        raise ValueError("time must include a clock time; date-only values are ambiguous")

    return parsed


def _resolve_source(parsed: datetime, source_timezone: str | None, fold: Literal[0, 1]) -> datetime:
    if parsed.tzinfo is not None:
        if source_timezone is not None:
            raise ValueError(
                "source_timezone must be omitted when time already includes a UTC offset"
            )
        return parsed

    if source_timezone is None:
        raise ValueError("source_timezone is required when time does not include a UTC offset")

    zone = _resolve_zone(source_timezone)
    candidate = parsed.replace(tzinfo=zone.tz, fold=fold)
    _validate_local_time(candidate, parsed, source_timezone)
    return candidate


def _resolve_zone(value: str) -> ResolvedZone:
    key = _normalize_zone_key(value)
    if key == "AoE":
        return ResolvedZone(key=key, tz=UTC_MINUS_12)
    if key == "UTC":
        return ResolvedZone(key=key, tz=UTC)
    try:
        return ResolvedZone(key=key, tz=ZoneInfo(key))
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"unknown timezone: {value!r}") from exc


def _normalize_zone_key(value: str) -> str:
    stripped = value.strip()
    if not stripped:
        raise ValueError("timezone names cannot be empty")
    alias = ALIASES.get(stripped.casefold())
    return alias or stripped


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        key = _normalize_zone_key(value)
        if key not in seen:
            seen.add(key)
            result.append(key)
    return result


def _dedupe_without_source(values: list[str], *, source_key: str | None) -> list[str]:
    return [key for key in _dedupe(values) if key != source_key]


def _source_zone_key(source: datetime, source_timezone: str | None) -> str | None:
    if source_timezone is not None:
        return _normalize_zone_key(source_timezone)
    key = _timezone_key(source.tzinfo)
    if key not in {"unknown", None}:
        return key
    return None


def _validate_local_time(candidate: datetime, parsed: datetime, source_timezone: str) -> None:
    roundtrip = candidate.astimezone(UTC).astimezone(candidate.tzinfo)
    naive_roundtrip = roundtrip.replace(tzinfo=None)
    if naive_roundtrip != parsed:
        raise ValueError(
            f"{parsed.isoformat(sep=' ')} is not a valid local time in {source_timezone!r}"
        )


def _format_conversion(utc_time: datetime, zone_key: str) -> dict[str, object]:
    zone = _resolve_zone(zone_key)
    local = utc_time.astimezone(zone.tz)
    return _format_datetime(local) | {
        "requested_timezone": zone_key,
    }


def _format_datetime(value: datetime) -> dict[str, object]:
    offset = value.utcoffset()
    if offset is None:
        raise ValueError("datetime must be timezone-aware")
    return {
        "datetime": value.isoformat(),
        "date": value.date().isoformat(),
        "time": value.strftime("%H:%M:%S"),
        "weekday": value.strftime("%A"),
        "timezone": _timezone_key(value.tzinfo),
        "abbreviation": value.tzname(),
        "utc_offset": _format_offset(offset),
    }


def _timezone_key(value: tzinfo | None) -> str:
    if value is UTC:
        return "UTC"
    if value is UTC_MINUS_12:
        return "AoE"
    key = getattr(value, "key", None)
    if isinstance(key, str):
        return key
    name = value.tzname(None) if value is not None else None
    return name or "unknown"


def _format_offset(offset: timedelta) -> str:
    total_seconds = int(offset.total_seconds())
    sign = "+" if total_seconds >= 0 else "-"
    total_seconds = abs(total_seconds)
    hours, remainder = divmod(total_seconds, 3600)
    minutes = remainder // 60
    return f"{sign}{hours:02d}:{minutes:02d}"
