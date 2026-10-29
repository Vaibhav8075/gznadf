"""Small helpers to move between ISO-8601 strings and epoch seconds."""

from __future__ import annotations

from datetime import datetime, timezone


def parse_iso(value: str) -> int:
    """Parse an Elexon timestamp such as '2026-01-01T00:30:00Z' to epoch seconds."""
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp())


def to_iso(epoch_s: int) -> str:
    return datetime.fromtimestamp(epoch_s, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def epoch(dt: datetime) -> int:
    return int(dt.timestamp())
