# CHANGELOG — Sprint 2.7: Data Freshness Transparency

**Engine version:** `thammen-sprint2p7-data-freshness`
**Date:** 2026-05-13
**Files changed:** `api.py`, `index.html`
**Files added:** `data_freshness.py`
**Builds on:** Sprint 2.6 (v12)

---

## Why this matters

The thammen home page footer claimed:

> "بيانات حقيقية — **تُحدَّث أسبوعياً** من سجلات البيع الرسمية"

A direct check of the source revealed:

| المصدر | آخر سجل | فحص اليوم |
|---|---|---|
| ملف `moj_weekly.csv` المحلي | **2025-12-31** | matches source |
| `data.gov.qa` records API | **2025-12-31** | **133 يوماً قديمة** |
| MME API (qrep) | لا نتائج 2025-2026 | معطّل |

The source itself stopped publishing after Dec 31, 2025. Our "weekly
updates" claim became false the day after that. Sprint 2.7 makes the
real freshness visible to users instead of hiding it behind an
out-of-date marketing line.

This is a credibility patch, not a model patch — every valuation
thammen produced in the last 4 months silently assumed end-of-2025
data was current. Now the user sees the gap.

## What this patch does

### Backend (`data_freshness.py` — NEW)

A self-contained module (Python stdlib only) that:
1. Scans `moj_weekly.csv` once and finds `max(registration_date)`.
2. Classifies staleness into four tiers:

   | days_old | tier        | severity |
   |----------|-------------|----------|
   | 0–30     | `fresh`     | info     |
   | 31–90    | `mild`      | info     |
   | 91–180   | `stale`     | warning  |
   | 181+     | `very_stale`| alert    |

3. Pre-renders three Arabic strings per tier:
   - `banner_ar` — home-page sticky banner
   - `result_caveat_ar` — under each evaluation
   - `homepage_subtitle_ar` — hero footer replacement
4. Tolerates: UTF-8 BOM, NBSP in the "تاريخ التثبيت" header,
   English column names, extra whitespace in cells.

### Backend (`api.py`)

Five additions, all backward-compatible:

1. **Import** of `data_freshness` helpers near other engine imports.
2. **Module-level cache** (`_freshness_cache`) plus three functions:
   - `get_freshness()` — lazy, returns `None` on failure (never raises)
   - `refresh_freshness()` — forces recompute (cron hook)
   - `_attach_freshness(result)` — mutates a response dict to add
     `data_freshness`; tolerates non-dict and never raises
3. **`/api/health` enhanced** — calls `refresh_freshness()` (so a
   daily cron pinging `/api/health` keeps the banner current),
   embeds `moj_freshness` summary, and bumps `version` to
   `3.1.0-sprint2.7`.
4. **New endpoint `GET /api/freshness`** — public, returns
   `banner_ar` / `subtitle_ar` / `severity` / `tier` / `days_old`.
   Frontend fetches once on `DOMContentLoaded`.
5. **`_attach_freshness()` wraps** all four return paths in
   `/api/evaluate` and `/api/evaluate/details` (unified + v2 fallback),
   so every evaluation response now carries a `data_freshness` field.

### Frontend (`index.html`)

Five surgical edits, no markup rewrite, theme variables reused:

1. **CSS** — new `.dfb` (sticky banner) and `.dfc` (per-result caveat)
   classes using existing `--alt`, `--warn`, `--warn-bg`, `--bad`,
   `--bad-bg`, `--primary` variables. Body padding shifts when banner
   is visible (`body.has-dfb`).
2. **`<div id="dfBanner">`** — sticky banner immediately after `<body>`,
   hidden by default; populated by JS on load.
3. **`<div class="hfoot" id="dfSubtitle">`** — the old footer line was
   replaced with a neutral placeholder ("بيانات وزارة العدل القطرية
   الرسمية"); JS overwrites it with the dated subtitle.
4. **`loadFreshness()`** — async fetch to `/api/freshness`, sets banner
   text + class, updates subtitle, adds `has-dfb` to body so layout
   shifts cleanly. Silent failure: if API is unreachable the home page
   stays clean.
5. **Caveat injection inside `show()`** — right before the existing
   disclaimer card, when `d.data_freshness.caveat_ar` is present, an
   inline `.dfc` block renders the per-result caveat with severity
   color.

### Output schema additions

```json
"data_freshness": {
  "latest_record": "2025-12-31",
  "latest_record_ar": "31 ديسمبر 2025",
  "days_old": 133,
  "tier": "stale",
  "severity": "warning",
  "caveat_ar": "المرجع مبني على بيانات حتى 31 ديسمبر 2025. للحالات الحساسة، تحقق من السوق الحالي قبل اتخاذ القرار."
}
```

And on `/api/health`:

```json
"moj_freshness": {
  "latest_record": "2025-12-31",
  "days_old": 133,
  "tier": "stale",
  "record_count": 25673
}
```

---

## Verification — concrete numbers (local tested)

```
$ python3 data_freshness.py moj_weekly.csv
{
  "latest_record": "2025-12-31",
  "days_old": 133,
  "tier": "stale",
  "severity": "warning",
  "record_count": 25673,
  "banner_ar": "⚠️ آخر تحديث لبيانات وزارة العدل: ديسمبر 2025 (قبل 133 يوماً) — قد لا تعكس آخر تحركات السوق",
  "result_caveat_ar": "المرجع مبني على بيانات حتى 31 ديسمبر 2025. للحالات الحساسة، تحقق من السوق الحالي قبل اتخاذ القرار.",
  "homepage_subtitle_ar": "بيانات وزارة العدل القطرية الرسمية — آخر تحديث ديسمبر 2025"
}
```

Tier transitions verified for: fresh (1d), mild (59d), stale (133d),
very_stale (213d). All match expected severity + banner text.

## Deployment

```cmd
cd /d "C:\Thammen\deploy v2"
copy /Y api.py api.py.bak3 && copy /Y index.html index.html.bak9
tar -xf "%USERPROFILE%\Downloads\sprint2p7-data-freshness.zip"
findstr /C:"sprint2p7" api.py
git add api.py index.html data_freshness.py CHANGELOG_v13.md
git commit -m "Sprint 2.7: Data freshness transparency (banner + caveat)"
git push heroku master
```

## Verification curl

```bash
# 1. New endpoint
curl https://thammen.qa/api/freshness

# Expected:
# {"banner_ar":"⚠️ ...","subtitle_ar":"بيانات وزارة العدل ...",
#  "tier":"stale","severity":"warning","days_old":133,
#  "latest_record":"2025-12-31"}

# 2. /api/health now includes moj_freshness
curl https://thammen.qa/api/health | jq .moj_freshness

# 3. Every evaluation response now has data_freshness
curl -X POST https://thammen.qa/api/evaluate/details \
  -H "Content-Type: application/json" \
  -d '{"zone":52,"street":903,"building":90,"audience":"buyer"}' \
  | jq .data_freshness
```

## What's NOT in this patch (intentional Sprint 2.7 scope)

- Switching to MME API as alternative data source — separate Sprint
  (requires schema mapping + auth flow design)
- Auto-download of fresh CSV from data.gov.qa — pointless until the
  source resumes publishing (still stuck at 2025-12-31)
- Per-area / per-asset-type freshness (some areas may have data
  newer than others) — would require per-bracket scans, low value
  while the source is uniformly stale
- A "data is X% stale, here's the projected current price" feature —
  deliberately not built. Projecting forward without underlying
  transactions is exactly the false-confidence trap we declined in
  Sprint 2.5 (see CHANGELOG_v11)

## Self-healing behavior

When `data.gov.qa` resumes publishing:
1. The `update_moj.sh` cron downloads the new CSV.
2. Next `/api/health` hit calls `refresh_freshness()` automatically.
3. As soon as `days_old ≤ 90`, banner shifts from `s-warning` (amber)
   to `s-info` (rest tone) without code changes.
4. At `days_old ≤ 30` the banner becomes a neutral
   "📅 آخر تحديث لبيانات وزارة العدل: [الشهر]" line.

The patch degrades smoothly from "stale" back to "fresh" with no
manual intervention.
