"""
High-RPM US / Tier-1 Prime Time Scheduler (`utils/us_scheduler.py`).

Computes upcoming optimal publish timestamps in US Eastern (`America/New_York`,
automatically adjusting for EST/EDT Daylight Saving Time) and converts them to
RFC-3339 UTC (`YYYY-MM-DDTHH:MM:SSZ`) for YouTube Data API v3 `status.publishAt`,
avoiding collisions with previously scheduled clips.
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Set
from zoneinfo import ZoneInfo

import config


def _window_label_for_et(hour: int) -> str:
    if 6 <= hour < 12:
        return "US Morning Commute + UK/EU Afternoon"
    if 12 <= hour < 17:
        return "US After-School / West Coast Noon + UK Evening"
    if 17 <= hour < 22:
        return "US Evening Prime Time (Peak High-RPM)"
    return "Late Night US / APAC Early Window"


def _parse_utc_iso(iso_str: str) -> Optional[datetime]:
    if not iso_str:
        return None
    try:
        cleaned = iso_str.strip().replace("Z", "+00:00")
        dt = datetime.fromisoformat(cleaned)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def compute_next_us_prime_slots(
    count: int,
    min_lead_minutes: int = 45,
    min_spacing_minutes: int = 90,
    tz_name: Optional[str] = None,
    slots_et: Optional[List[str]] = None,
    reserved_utc_iso: Optional[Set[str]] = None,
    now_utc: Optional[datetime] = None,
) -> List[Dict[str, str]]:
    """
    Return `count` chronologically ordered future US Prime Time publish slots.
    Each slot includes `publish_at_utc` (`YYYY-MM-DDTHH:MM:SSZ`), `publish_at_et`,
    `publish_at_wib`, and `window_label`.
    """
    target_tz = ZoneInfo(tz_name or config.US_TARGET_TIMEZONE)
    wib_tz = ZoneInfo("Asia/Jakarta")
    raw_slots = slots_et or config.US_PRIME_SLOTS_ET or ["08:00", "12:30", "16:30", "20:00"]

    parsed_hhmm = []
    for item in raw_slots:
        parts = item.strip().split(":")
        if len(parts) != 2:
            continue
        try:
            hh, mm = int(parts[0]), int(parts[1])
            if 0 <= hh <= 23 and 0 <= mm <= 59:
                parsed_hhmm.append((hh, mm))
        except ValueError:
            continue
    if not parsed_hhmm:
        parsed_hhmm = [(8, 0), (12, 30), (16, 30), (20, 0)]

    ref_utc = now_utc or datetime.now(timezone.utc)
    earliest_utc = ref_utc + timedelta(minutes=max(10, min_lead_minutes))
    base_et_date = ref_utc.astimezone(target_tz).date()

    reserved_dts: List[datetime] = []
    for s in (reserved_utc_iso or set()):
        dt = _parse_utc_iso(s)
        if dt and dt >= ref_utc - timedelta(minutes=30):
            reserved_dts.append(dt)

    # Generate candidate slots across the next 14 days sorted chronologically
    candidates_utc: List[datetime] = []
    for day_offset in range(15):
        d = base_et_date + timedelta(days=day_offset)
        for hh, mm in parsed_hhmm:
            local_et = datetime(d.year, d.month, d.day, hh, mm, 0, tzinfo=target_tz)
            cand_utc = local_et.astimezone(timezone.utc)
            if cand_utc >= earliest_utc:
                candidates_utc.append(cand_utc)
    candidates_utc.sort()

    selected: List[Dict[str, str]] = []
    spacing = timedelta(minutes=max(15, min_spacing_minutes))
    for cand in candidates_utc:
        if len(selected) >= count:
            break
        if any(abs((cand - r).total_seconds()) < spacing.total_seconds() for r in reserved_dts):
            continue
        reserved_dts.append(cand)
        et_dt = cand.astimezone(target_tz)
        wib_dt = cand.astimezone(wib_tz)
        selected.append({
            "publish_at_utc": cand.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "publish_at_et": et_dt.strftime("%Y-%m-%d %H:%M %Z"),
            "publish_at_wib": wib_dt.strftime("%Y-%m-%d %H:%M WIB"),
            "window_label": _window_label_for_et(et_dt.hour),
        })

    return selected

