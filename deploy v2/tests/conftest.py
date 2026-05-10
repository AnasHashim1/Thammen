"""Shared fixtures for Qatar real estate system tests."""
import csv
import pytest
from pathlib import Path

# Mini dataset: 20 transactions with known results
# Area: المعمورة 56, mix of land and villa, different sizes
MINI_TRANSACTIONS = [
    # --- Lands (10 rows) ---
    {"ref": "T001", "date": "2025-01-15", "muni": "الدوحة", "area": "المعمورة 56",
     "type": "أرض فضاء", "usage": "سكني", "m2": "600", "sold": "600",
     "ft2": "380", "pm2": "4090", "shares": "2400", "sv": "2454000", "total": "2454000"},
    {"ref": "T002", "date": "2025-02-10", "muni": "الدوحة", "area": "المعمورة 56",
     "type": "أرض فضاء", "usage": "سكني", "m2": "500", "sold": "500",
     "ft2": "400", "pm2": "4306", "shares": "2400", "sv": "2153000", "total": "2153000"},
    {"ref": "T003", "date": "2025-03-05", "muni": "الدوحة", "area": "المعمورة 56",
     "type": "أرض فضاء", "usage": "سكني", "m2": "450", "sold": "450",
     "ft2": "420", "pm2": "4522", "shares": "2400", "sv": "2035000", "total": "2035000"},
    {"ref": "T004", "date": "2024-12-20", "muni": "الدوحة", "area": "المعمورة 56",
     "type": "أرض فضاء", "usage": "سكني", "m2": "700", "sold": "700",
     "ft2": "350", "pm2": "3767", "shares": "2400", "sv": "2637000", "total": "2637000"},
    {"ref": "T005", "date": "2024-11-10", "muni": "الدوحة", "area": "المعمورة 56",
     "type": "أرض فضاء", "usage": "سكني", "m2": "550", "sold": "550",
     "ft2": "390", "pm2": "4198", "shares": "2400", "sv": "2309000", "total": "2309000"},
    {"ref": "T006", "date": "2024-08-01", "muni": "الدوحة", "area": "المعمورة 56",
     "type": "أرض فضاء", "usage": "سكني", "m2": "480", "sold": "480",
     "ft2": "410", "pm2": "4414", "shares": "2400", "sv": "2119000", "total": "2119000"},
    {"ref": "T007", "date": "2024-06-15", "muni": "الدوحة", "area": "المعمورة 56",
     "type": "أرض فضاء", "usage": "سكني", "m2": "620", "sold": "620",
     "ft2": "375", "pm2": "4037", "shares": "2400", "sv": "2503000", "total": "2503000"},
    {"ref": "T008", "date": "2024-04-01", "muni": "الدوحة", "area": "المعمورة 56",
     "type": "أرض فضاء", "usage": "سكني", "m2": "530", "sold": "530",
     "ft2": "395", "pm2": "4252", "shares": "2400", "sv": "2254000", "total": "2254000"},
    {"ref": "T009", "date": "2023-09-10", "muni": "الدوحة", "area": "المعمورة 56",
     "type": "أرض فضاء", "usage": "سكني", "m2": "660", "sold": "660",
     "ft2": "360", "pm2": "3875", "shares": "2400", "sv": "2558000", "total": "2558000"},
    {"ref": "T010", "date": "2023-06-20", "muni": "الدوحة", "area": "المعمورة 56",
     "type": "أرض\xa0فضاء", "usage": "سكني", "m2": "510", "sold": "510",  # NBSP intentional!
     "ft2": "405", "pm2": "4360", "shares": "2400", "sv": "2223000", "total": "2223000"},

    # --- Villas (10 rows, various sizes) ---
    {"ref": "T011", "date": "2025-04-15", "muni": "الدوحة", "area": "المعمورة 56",
     "type": "فيلا من طابقين وملحق", "usage": "سكني", "m2": "500", "sold": "500",
     "ft2": "497", "pm2": "5350", "shares": "2400", "sv": "2675000", "total": "2675000"},
    {"ref": "T012", "date": "2025-03-01", "muni": "الدوحة", "area": "المعمورة 56",
     "type": "فيلا", "usage": "سكني", "m2": "450", "sold": "450",
     "ft2": "520", "pm2": "5598", "shares": "2400", "sv": "2519000", "total": "2519000"},
    {"ref": "T013", "date": "2025-01-20", "muni": "الدوحة", "area": "المعمورة 56",
     "type": "فيلا", "usage": "سكني", "m2": "550", "sold": "550",
     "ft2": "480", "pm2": "5167", "shares": "2400", "sv": "2842000", "total": "2842000"},
    {"ref": "T014", "date": "2024-10-22", "muni": "الدوحة", "area": "المعمورة 56",
     "type": "بيت للسكن", "usage": "سكني", "m2": "600", "sold": "600",
     "ft2": "465", "pm2": "5006", "shares": "2400", "sv": "3004000", "total": "3004000"},
    {"ref": "T015", "date": "2024-09-05", "muni": "الدوحة", "area": "المعمورة 56",
     "type": "فيلا من طابقين وملحق", "usage": "سكني", "m2": "1100", "sold": "1100",
     "ft2": "443", "pm2": "4768", "shares": "2400", "sv": "5245000", "total": "5245000"},
    {"ref": "T016", "date": "2024-07-10", "muni": "الدوحة", "area": "المعمورة 56",
     "type": "فيلا", "usage": "سكني", "m2": "950", "sold": "950",
     "ft2": "460", "pm2": "4952", "shares": "2400", "sv": "4704000", "total": "4704000"},
    {"ref": "T017", "date": "2024-06-01", "muni": "الدوحة", "area": "المعمورة 56",
     "type": "فيلا", "usage": "سكني", "m2": "480", "sold": "480",
     "ft2": "510", "pm2": "5490", "shares": "2400", "sv": "2635000", "total": "2635000"},
    {"ref": "T018", "date": "2024-04-15", "muni": "الدوحة", "area": "المعمورة 56",
     "type": "بيت\xa0للسكن", "usage": "سكني", "m2": "520", "sold": "520",  # NBSP intentional!
     "ft2": "490", "pm2": "5274", "shares": "2400", "sv": "2743000", "total": "2743000"},
    {"ref": "T019", "date": "2023-11-01", "muni": "الدوحة", "area": "المعمورة 56",
     "type": "فيلا", "usage": "سكني", "m2": "1200", "sold": "1200",
     "ft2": "430", "pm2": "4629", "shares": "2400", "sv": "5555000", "total": "5555000"},
    {"ref": "T020", "date": "2023-08-15", "muni": "الدوحة", "area": "المعمورة 56",
     "type": "فيلا", "usage": "سكني", "m2": "650", "sold": "650",
     "ft2": "470", "pm2": "5060", "shares": "2400", "sv": "3289000", "total": "3289000"},
]

# CSV column headers (with NBSP to match real file)
CSV_HEADERS = [
    'رقم المعامله المرجعي',
    'رقم العقار المرجعي',
    'تاريخ\xa0التثبيت',        # NBSP — matches real CSV
    'اسم البلدية',
    'اسم المنطقة',
    'نوع العقار',
    'الاستخدام',
    'المساحة بالمتر المربع',
    'مساحة الحصص المباعة',
    'سعر القدم المربع',
    'سعر المتر المربع',
    'عدد الحصص المباعة',
    'قيمة الحصص المباعة',
    'قيمة العقار',
]


@pytest.fixture
def mini_csv(tmp_path):
    """Write mini CSV and return its path."""
    csv_path = tmp_path / "mini_moj.csv"
    with open(csv_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(CSV_HEADERS)
        for t in MINI_TRANSACTIONS:
            writer.writerow([
                t['ref'], t['ref'],     # ref_no, property_ref
                t['date'],
                t['muni'], t['area'],
                t['type'], t['usage'],
                t['m2'], t['sold'],
                t['ft2'], t['pm2'],
                t['shares'], t['sv'], t['total'],
            ])
    return csv_path


@pytest.fixture
def mini_db(mini_csv):
    """Create SQLite DB from mini CSV and return path."""
    import sys
    sys.path.insert(0, str(mini_csv.parent.parent.parent))
    from moj_db import init_db
    conn = init_db(mini_csv, force=True)
    conn.close()
    return mini_csv.with_suffix('.db')


@pytest.fixture
def mini_rows(mini_csv):
    """Load mini CSV as list of dicts (for moj_reference.py tests)."""
    with open(mini_csv, 'r', encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))
