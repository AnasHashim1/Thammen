# Thammen (ثمّن) — Logo & Mark Brief v1

> **Purpose:** brief the designer so the returned logo asset fits the **locked brand system** and the
> real usage contexts — instead of being retrofitted later. Authored 2026-06-15 (brand-review track,
> Sprint C). Pairs with the locked color system (below) + `index.html` `.thmr` design language.

## 1. The problem with the current asset (why we need this)

The live logo is a **detailed emblem** (scales + tower) shipped as a **727 KB raster PNG**, with **no SVG**
and **no light/mono variant**. Consequences, observed live:

- **Degrades at small sizes** → a dim blob on the consent gate (40 px) and the toolbar (36 px); the
  «THAMMEN» wordmark is barely legible there.
- **Cannot sit on navy** (no light cut) → the gate/result navy surfaces look "off" because the dark
  emblem can't live on a dark field. **This is the single biggest brand gap.**
- Heavy + not crisp on retina; can't be recolored per surface.

## 2. Deliverables (what we need back)

1. **Primary mark** — simplified so it **reads cleanly at 16 px** (favicon) and scales to a billboard.
   Keep the «ثمّن» identity + the valuation/justice concept, but reduce detail.
2. **Formats:** **SVG** (master) + exported PNG @1×/2×/3× for: 340 px (home), 96 px, 40 px, favicon 32/16.
3. **Variants (mandatory):**
   - **Full color** on light/cream surfaces (navy + bronze).
   - **Light / reversed** for **navy surfaces** (white or champagne-gold mark on `#16324F`).
   - **Monochrome** (single navy; single white) for stamps, print, the report header.
4. **Lockups:** (a) mark + «ثمّن» wordmark + «تقييم العقارات · قطر» tagline (home); (b) compact mark-only
   (toolbar/favicon).
5. **Clear-space + min-size** rules.

## 3. The brand system the mark must fit (locked)

| Token | Hex | Role |
|---|---|---|
| navy `--primary` | `#16324F` | identity / trust / dark fields |
| bronze `--bronze` | `#A4814A` | accent on **light** surfaces |
| gold `--gold` | `#E8C99A` | accent on **navy** surfaces (champagne — reads on dark) |
| cream `--bg` | `#FBF8F2` | paper / background |

- **Type:** IBM Plex Sans Arabic (the app + report are unified on it). The «ثمّن» wordmark should sit
  comfortably beside Plex Arabic.
- **Rule of metal:** bronze on light, **champagne-gold on navy** (muted bronze goes muddy on navy).
- **Mark must work on BOTH** cream `#FBF8F2` and navy `#16324F`.

## 4. Usage contexts + minimum sizes (design against these)

| Surface | Background | Size | Variant |
|---|---|---|---|
| Home hero | cream | ~340 px wide | full color |
| Consent gate / result hero header | **navy** | ~40–48 px | **light / gold** |
| Toolbar (in-app) | white | 36 px | full color or mono-navy |
| Report header (`.thmr`) | navy band | ~40 px | light |
| Favicon / app icon | — | 16/32 px | simplified mark only |

## 5. Constraints / do-not

- Keep the «ثمّن» name central; don't drift to a generic real-estate house icon.
- No gradients/3D/bevels — flat, premium, scalable.
- The scales-of-justice motif (MoJ-data association) may stay **only if** it survives 16 px; otherwise
  simplify to a clean wordmark/monogram.

## 6. Integration (our side — fast once the asset lands)

The moment the SVG + variants arrive, we wire them per-surface (full on home, **light/gold on every navy
surface** — gate, result hero, report header) in minutes; no logic change. Until then the current raster
stays as a placeholder.
