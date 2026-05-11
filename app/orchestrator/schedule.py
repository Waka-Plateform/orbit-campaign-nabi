from __future__ import annotations

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo


DEFAULT_WINDOWS = {"days": [1, 2, 3, 4, 5], "opening_hour": 9, "closing_hour": 19, "timezone": "Europe/Paris"}


def normalize_schedule(schedule: dict | None) -> dict:
    s = dict(DEFAULT_WINDOWS)
    if schedule:
        s.update(schedule)
    if "start" in s and "start_at" not in s:
        s["start_at"] = s.get("start")
    return s


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def is_paused_or_outside_global_window(schedule: dict, now: datetime | None = None) -> tuple[bool, str]:
    now = now or now_utc()
    s = normalize_schedule(schedule)
    if s.get("paused"):
        return True, "paused"
    start_at = _parse_dt(s.get("start_at") or s.get("start"))
    end_at = _parse_dt(s.get("end_at") or s.get("end"))
    if start_at and now < start_at:
        return True, "before_start"
    if end_at and now > end_at:
        return True, "after_end"
    return False, "ok"


def is_in_allowed_window(schedule: dict, now: datetime | None = None) -> bool:
    now = now or now_utc()
    s = normalize_schedule(schedule)
    tz = ZoneInfo(s.get("timezone", "Europe/Paris"))
    local = now.astimezone(tz)
    day = local.isoweekday()
    return day in s.get("days", []) and s.get("opening_hour", 0) <= local.hour < s.get("closing_hour", 24)


def next_allowed_time(schedule: dict, now: datetime | None = None) -> datetime:
    now = now or now_utc()
    s = normalize_schedule(schedule)
    tz = ZoneInfo(s.get("timezone", "Europe/Paris"))
    local = now.astimezone(tz)
    for i in range(14):
        candidate = (local + timedelta(days=i)).replace(hour=s.get("opening_hour", 9), minute=0, second=0, microsecond=0)
        if i == 0 and local.hour < s.get("opening_hour", 9):
            pass
        elif i == 0 and local.hour >= s.get("closing_hour", 19):
            continue
        elif i == 0 and s.get("opening_hour", 9) <= local.hour < s.get("closing_hour", 19):
            candidate = local
        if candidate.isoweekday() in s.get("days", []) and candidate >= local:
            return candidate.astimezone(timezone.utc)
    return (now + timedelta(days=1)).replace(hour=8, minute=0, second=0, microsecond=0)


def parse_iso_duration(value: str) -> timedelta:
    if value == "P5D":
        return timedelta(days=5)
    if value.startswith("PT") and value.endswith("H"):
        return timedelta(hours=int(value[2:-1]))
    if value.startswith("P") and value.endswith("D"):
        return timedelta(days=int(value[1:-1]))
    raise ValueError(f"Unsupported ISO-8601 duration: {value}")
