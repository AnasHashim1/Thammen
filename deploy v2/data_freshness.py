#!/usr/bin/env python3
"""
data_freshness.py — Sprint 2.7: Data Freshness Transparency
============================================================

Computes how stale the MoJ CSV is and emits user-facing Arabic
strings for the home banner, hero subtitle, and per-result caveat.

Why this module exists
----------------------
data.gov.qa stopped publishing the weekly bulletin after 2025-12-31.
The thammen home page previously claimed "بيانات تُحدَّث أسبوعياً" —
which became misleading once the source itself went silent. This
module reads the actual latest record from `moj_weekly.csv`, computes
days_old, and provides honest messaging that scales with severity.

Usage
-----
    from data_freshness import (
        compute_freshness,
        freshness_for_response,
        freshness_for_homepage,
    )

    # Once at startup; refresh after CSV reload via /healthz hook.
    FRESHNESS = compute_freshness("moj_weekly.csv")

    # Home page:
    home_data = freshness_for_homepage(FRESHNESS)

    # Per-evaluation response:
    result["data_freshness"] = freshness_for_response(FRESHNESS)

Tier classification (days_old)
------------------------------
    0–30       fresh        info       (rest tone)
    31–90      mild         info       (subtle dated note)
    91–180     stale        warning    (amber banner)
    181+       very_stale   alert      (red banner)

Failure mode
------------
If the CSV is missing or unparseable, `compute_freshness()` raises.
Caller should wrap in try/except and degrade gracefully (no banner,
keep the legacy subtitle) — never crash the app on a freshness fault.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional


# ────────────────────────────────────────────────────────────
# Constants
# ────────────────────────────────────────────────────────────

ARABIC_MONTHS = {
    1: "يناير", 2: "فبراير", 3: "مارس", 4: "أبريل",
    5: "مايو", 6: "يونيو", 7: "يوليو", 8: "أغسطس",
    9: "سبتمبر", 10: "أكتوبر", 11: "نوفمبر", 12: "ديسمبر",
}

TIER_FRESH = 30
TIER_MILD = 90
TIER_STALE = 180


# ────────────────────────────────────────────────────────────
# Data class
# ────────────────────────────────────────────────────────────

@dataclass
class FreshnessReport:
    """Computed freshness state, ready for serialization."""

    latest_record: str              # ISO date, e.g. "2025-12-31"
    latest_record_ar: str           # "31 ديسمبر 2025"
    latest_record_month_ar: str     # "ديسمبر 2025"
    days_old: int                   # vs today (or override `today`)
    tier: str                       # fresh | mild | stale | very_stale
    severity: str                   # info | warning | alert
    record_count: int               # total CSV rows with parseable dates
    csv_path: str                   # source CSV (audit trail)
    computed_at: str                # ISO timestamp

    # Pre-rendered user-facing strings
    banner_ar: str                  # home-page sticky banner
    result_caveat_ar: str           # under each evaluation result
    homepage_subtitle_ar: str       # replaces hero "weekly updates" line


# ────────────────────────────────────────────────────────────
# Public API
# ────────────────────────────────────────────────────────────

def compute_freshness(
    csv_path: str | Path,
    *,
    today: Optional[datetime] = None,
) -> FreshnessReport:
    """Build a FreshnessReport by scanning the MoJ CSV.

    Args:
        csv_path: Path to moj_weekly.csv (or compatible bulletin export).
        today:    Override for deterministic tests. Defaults to now().

    Raises:
        FileNotFoundError: CSV missing.
        ValueError:        no date column, or no parseable dates.
    """
    today = today or datetime.now()
    latest_date, record_count = _scan_latest_date(csv_path)

    days_old = (today.date() - latest_date.date()).days
    tier = _classify_tier(days_old)
    severity = _severity_for_tier(tier)

    latest_iso = latest_date.strftime("%Y-%m-%d")
    latest_ar = f"{latest_date.day} {ARABIC_MONTHS[latest_date.month]} {latest_date.year}"
    month_ar = f"{ARABIC_MONTHS[latest_date.month]} {latest_date.year}"

    return FreshnessReport(
        latest_record=latest_iso,
        latest_record_ar=latest_ar,
        latest_record_month_ar=month_ar,
        days_old=days_old,
        tier=tier,
        severity=severity,
        record_count=record_count,
        csv_path=str(csv_path),
        computed_at=today.isoformat(timespec="seconds"),
        banner_ar=_render_banner(month_ar, days_old, tier),
        result_caveat_ar=_render_caveat(latest_ar, tier),
        homepage_subtitle_ar=_render_subtitle(month_ar),
    )


def freshness_for_response(report: FreshnessReport) -> dict:
    """Slim subset for embedding in /api/evaluate response payloads."""
    return {
        "latest_record": report.latest_record,
        "latest_record_ar": report.latest_record_ar,
        "days_old": report.days_old,
        "tier": report.tier,
        "severity": report.severity,
        "caveat_ar": report.result_caveat_ar,
    }


def freshness_for_homepage(report: FreshnessReport) -> dict:
    """Subset for the home-page banner + subtitle."""
    return {
        "banner_ar": report.banner_ar,
        "subtitle_ar": report.homepage_subtitle_ar,
        "tier": report.tier,
        "severity": report.severity,
        "days_old": report.days_old,
        "latest_record": report.latest_record,
    }


def freshness_for_health(report: FreshnessReport) -> dict:
    """Subset embedded in /api/health for ops monitoring."""
    return {
        "latest_record": report.latest_record,
        "days_old": report.days_old,
        "tier": report.tier,
        "record_count": report.record_count,
    }


# ────────────────────────────────────────────────────────────
# Internal helpers
# ────────────────────────────────────────────────────────────

def _scan_latest_date(csv_path: str | Path) -> tuple[datetime, int]:
    """Single-pass CSV scan returning (max_date, parseable_row_count).

    Robust to:
      - UTF-8 BOM
      - NBSP (\xa0) inside the header "تاريخ التثبيت"
      - English column name "registration_date"
      - extra whitespace inside cells
    """
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    latest: Optional[datetime] = None
    count = 0

    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError(f"CSV has no header: {csv_path}")

        date_col = _find_date_column(reader.fieldnames)
        if date_col is None:
            raise ValueError(
                "Could not locate a date column. Looked for variants of "
                "'تاريخ التثبيت' / 'registration_date'. "
                f"Header sample: {reader.fieldnames[:5]}"
            )

        for row in reader:
            raw = row.get(date_col) or ""
            raw = re.sub(r"\s+", " ", raw).strip()
            if not raw:
                continue
            try:
                d = datetime.strptime(raw, "%Y-%m-%d")
            except ValueError:
                continue
            count += 1
            if latest is None or d > latest:
                latest = d

    if latest is None:
        raise ValueError(f"No parseable dates in CSV: {csv_path}")

    return latest, count


def _find_date_column(fieldnames: list[str]) -> Optional[str]:
    for name in fieldnames:
        normalized = re.sub(r"\s+", " ", name).strip()
        if "تاريخ" in normalized and "تثبيت" in normalized:
            return name
        if normalized.lower() == "registration_date":
            return name
    return None


def _classify_tier(days_old: int) -> str:
    if days_old <= TIER_FRESH:
        return "fresh"
    if days_old <= TIER_MILD:
        return "mild"
    if days_old <= TIER_STALE:
        return "stale"
    return "very_stale"


def _severity_for_tier(tier: str) -> str:
    return {
        "fresh": "info",
        "mild": "info",
        "stale": "warning",
        "very_stale": "alert",
    }[tier]


def _render_banner(month_ar: str, days_old: int, tier: str) -> str:
    if tier == "fresh":
        return f"📅 آخر تحديث لبيانات وزارة العدل: {month_ar}"
    if tier == "mild":
        return (f"📅 آخر تحديث لبيانات وزارة العدل: {month_ar} "
                f"(قبل {days_old} يوماً)")
    if tier == "stale":
        return (f"⚠️ آخر تحديث لبيانات وزارة العدل: {month_ar} "
                f"(قبل {days_old} يوماً) — قد لا تعكس آخر تحركات السوق")
    # very_stale
    return (f"⚠️ تنبيه: بيانات وزارة العدل لم تُحدَّث منذ {month_ar} "
            f"({days_old} يوماً) — استخدم النتائج كمرجع إرشادي فقط")


def _render_caveat(latest_ar: str, tier: str) -> str:
    if tier in ("fresh", "mild"):
        return f"المرجع مبني على بيانات حتى {latest_ar}."
    if tier == "stale":
        return (f"المرجع مبني على بيانات حتى {latest_ar}. "
                f"للحالات الحساسة، تحقق من السوق الحالي قبل اتخاذ القرار.")
    # very_stale
    return (f"⚠️ المرجع مبني على بيانات وزارة العدل المتاحة حتى {latest_ar}. "
            f"الحكومة لم تنشر بيانات أحدث. النتائج إرشادية ولا تعكس "
            f"بالضرورة الأسعار الحالية.")


def _render_subtitle(month_ar: str) -> str:
    return f"بيانات وزارة العدل القطرية الرسمية — آخر تحديث {month_ar}"


# ────────────────────────────────────────────────────────────
# CLI for manual inspection
# ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import json
    import sys

    if len(sys.argv) != 2:
        print("Usage: python3 data_freshness.py <path/to/moj_weekly.csv>")
        sys.exit(1)

    report = compute_freshness(sys.argv[1])
    print(json.dumps(asdict(report), indent=2, ensure_ascii=False))
