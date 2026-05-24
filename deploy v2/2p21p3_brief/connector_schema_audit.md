# Connector Schema Audit — Sprint 2.21.3

**Run timestamp (UTC):** 2026-05-24 17:22:45
**Total wall time:** 24.5s
**Origin:** Heroku
**Goal:** Confirm detail-page schema for one Lusail apartment listing per source.
**Source brief:** BRIEF_2p21p3 §9 step 2 + §12 (JS-rendering risk for arady).

---

## 1. Falsifiable predictions

| # | Prediction | Result | Evidence |
|---|---|:---:|---|
| **S1** | arady sales URL pattern identified | ✅ TRUE | winner: https://arady.qa/listings, verdict: SALE |
| **S2** | PF sales c/t combination identified | ❌ FALSE | combo: c=2&t=1, big_prices(>500K)=0, max=12,000 |
| **S3** | arady detail exposes price + area extractable | ❌ FALSE | price=None, area=None |
| **S4** | PF detail exposes price + area extractable | ✅ TRUE | price=('AED', 150000), area=120.0m² |
| **S5** | Neither source JS-rendered | ✅ TRUE | arady JS-risk=False, PF JS-risk=False |

---

## 2. arady — URL discovery + detail

### 2.1 Candidate scan

| URL | HTTP | sale/rent | big_prices |
|---|:---:|---|---:|
| `https://arady.qa/listings` | 200 | SALE (s=195 r=1) | 0 |
| `https://arady.qa/listings?type=sale` | 200 | SALE (s=195 r=1) | 0 |
| `https://arady.qa/listings/sale` | 200 | SALE (s=195 r=1) | 0 |
| `https://arady.qa/buy` | 404 | N/A (s=0 r=0) | 0 |
| `https://arady.qa/sale` | 404 | N/A (s=0 r=0) | 0 |
| `https://arady.qa/apartments-for-sale` | 404 | N/A (s=0 r=0) | 0 |

**Winner:** `https://arady.qa/listings` — verdict SALE

### 2.2 Detail page extracted

- **URL:** `https://arady.qa/listings/villas`
- **HTTP:** 200, **length:** 475,821
- **Title:** بيوت وفلل للبيع في قطر | أراضي قطر
- **Listing price:** None (apt range >100K)
- **Apartment area:** None m² (30-500 m² range)
- **Bedrooms:** 7
- **Lusail markers in body:** True
- **All prices found (first 10):** []
- **All areas found (first 10):** []

**CSS / data-attr markers:**
- `property-price` class: True
- `data-test="price"`: False
- `property-size` class: False

**JS-rendering signals:** {'react_root_marker': False, 'vue_app_marker': False, 'noscript_warning': False, 'spa_loading_text': False, 'low_static_content': True, 'high_script_ratio': True, 'scripts_count': 34}

**Raw HTML excerpt (first 2000 chars):**
```html
<!DOCTYPE html><html lang="ar" dir="rtl" class="plus_jakarta_sans_a0023b84-module__5ML5jG__variable"><head><meta charSet="utf-8"/><meta charSet="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1"/><meta name="viewport" content="initial-scale=1.0, width=device-width, viewport-fit=cover"/><link rel="stylesheet" href="/_next/static/chunks/cec9cc0b710c5caa.css" data-precedence="next"/><link rel="preload" as="script" fetchPriority="low" href="/_next/static/chunks/e09c802b347d760e.js"/><script src="/_next/static/chunks/c075bd4ffb62b2eb.js" async=""></script><script src="/_next/static/chunks/5d6254907fec6894.js" async=""></script><script src="/_next/static/chunks/449bf7173db38e34.js" async=""></script><script src="/_next/static/chunks/turbopack-9f53a81467eec6b2.js" async=""></script><script src="/_next/static/chunks/ff1a16fafef87110.js" async=""></script><script src="/_next/static/chunks/247eb132b7f7b574.js" async=""></script><script src="/_next/static/chunks/3137e035f6370678.js" async=""></script><script src="/_next/static/chunks/0c5e2baf31db2059.js" async=""></script><script src="/_next/static/chunks/9c2db669d4a56ffd.js" async=""></script><script src="/_next/static/chunks/74ab89fe70cbc255.js" async=""></script><script src="/_next/static/chunks/aeaff1f0a6702e1f.js" async=""></script><script src="/_next/static/chunks/da89af015477daa0.js" async=""></script><script src="/_next/static/chunks/e0d54bb2551a6625.js" async=""></script><script src="/_next/static/chunks/1a78d1b33b378e9f.js" async=""></script><script src="/_next/static/chunks/1196691e9a8d242c.js" async=""></script><script src="/_next/static/chunks/c6cec0a15d90814c.js" async=""></script><script src="/_next/static/chunks/ecd114ed3f77d373.js" async=""></script><script src="/_next/static/chunks/44110bb9f11232d6.js" async=""></script><script src="/_next/static/chunks/e1c12fcdd1881978.js" async=""></script><link rel="preload" href="/_next/static/chunks/70d6a7a0bfcd3642.css" as="style"/><link rel="p
```

---

## 3. PropertyFinder — URL discovery + detail

### 3.1 Candidate scan

| Combo | HTTP | sale/rent | big_prices(>500K) | max_price |
|---|:---:|---|---:|---:|
| `c=1&t=1` | 404 | N/A | 0 | 0 |
| `c=2&t=1` | 200 | RENT | 0 | 12,000 |
| `c=1&t=2` | 404 | N/A | 0 | 0 |

**Winner combo:** `c=2&t=1` — `https://www.propertyfinder.qa/en/search?c=2&t=1&l=63`

### 3.2 Detail page extracted

- **URL:** `https://www.propertyfinder.qa/en/plp/rent/apartment-for-rent-doha-al-messila-urwa-bin-masoud-street-53099004.html`
- **HTTP:** 200, **length:** 316,534
- **Title:** Rent in Urwa Bin Masoud Street: CALM ENVIRONMENT | 3BR W/ BALCONY |IN MESSILA DOHA | Property Finder
- **Listing price:** ('AED', 150000)
- **Apartment area:** 120.0 m²
- **Bedrooms:** 1
- **Lusail markers in body:** False
- **All prices found (first 10):** [('QAR', 10000), ('QAR', 10000), ('AED', 580), ('AED', 2000), ('AED', 4000), ('AED', 6000), ('AED', 8000), ('AED', 2000), ('AED', 130), ('AED', 4000)]
- **All areas found (first 10):** [120.0, 120.0, 120.0, 120.0, 120.0, 120.0, 120.0, 131.0, 120.0]

**CSS / data-attr markers:**
- `property-price` class: True
- `data-test="price"`: False
- `property-size` class: False

**JS-rendering signals:** {'react_root_marker': True, 'vue_app_marker': False, 'noscript_warning': True, 'spa_loading_text': True, 'low_static_content': False, 'high_script_ratio': False, 'scripts_count': 26}

**Raw HTML excerpt (first 2000 chars):**
```html
<!DOCTYPE html><html dir="ltr" platform="desktop" lang="en" style="scroll-behavior:smooth"><head><meta charSet="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1"/><style>
          :root {
            --styleguide-font-family: '__Open_Sans_c18496', '__Open_Sans_Fallback_c18496'
          }

          [dir='rtl']:root {
            --styleguide-font-family: '__arFont_6d632a', '__arFont_Fallback_6d632a'
          }
        </style><meta name="page-name" content="plp"/><script id="plp-schema" type="application/ld+json">{"@context":"https://schema.org/","@id":"http://schema.org/53099004","@type":["webpage","ApartmentComplex","RealEstateListing","House","product"],"speakable":{"@type":"SpeakableSpecification","xpath":["/html/head/meta[@name='description']/@content"]},"breadcrumb":{"@context":"http://schema.org","@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","name":"Property Finder","item":"https://www.propertyfinder.qa/","position":1},{"@type":"ListItem","name":"Apartments for rent in Doha","item":"https://www.propertyfinder.qa/en/rent/doha/apartments-for-rent.html","position":2},{"@type":"ListItem","name":"Al Messila","item":"https://www.propertyfinder.qa/en/rent/doha/apartments-for-rent-al-messila.html","position":3},{"@type":"ListItem","name":"Urwa Bin Masoud Street","item":"https://www.propertyfinder.qa/en/rent/doha/apartments-for-rent-al-messila-urwa-bin-masoud-street.html","position":4},{"@type":"ListItem","name":"CALM ENVIRONMENT | 3BR W/ BALCONY |IN MESSILA DOHA","item":"https://www.propertyfinder.qa/en/plp/rent/apartment-for-rent-doha-al-messila-urwa-bin-masoud-street-53099004.html","position":5}],"numberOfItems":5},"mainEntity":{"@type":"WebPage","mainEntity":{"@type":["ApartmentComplex","RealEstateListing","House"],"@id":"http://schema.org/53099004","name":"CALM ENVIRONMENT | 3BR W/ BALCONY |IN MESSILA DOHA","description":"Looking to rent a Brand New 3-Bedroom Apartment in the Desirable Al Messila Area? Look no furthe
```

---

## 4. Recommendations for connector build (Sprint 2.21.3 Step 3)

(Filled at build time based on which predictions came back TRUE.)

- If S1 + S3 TRUE → arady connector builds against the winning search URL
- If S2 + S4 TRUE → PF connector builds against the winning c/t combo
- If S5 FALSE on arady → shrink Sprint to PF-only per BRIEF §12 contingency
- If S5 FALSE on PF → Sprint blocked; pause and reassess (no fallback)

---

*Generated by `2p21p3_pre/probe_schema_2p21p3.py`. Cleanup pattern: same as
Pre-Sprint smoke v108→v109 (push probe, run, push cleanup without probe).*
