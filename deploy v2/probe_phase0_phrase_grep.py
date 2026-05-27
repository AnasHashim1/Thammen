"""Sprint 2.22.0a.2 Phase 0.2 — grep flagged phrases in rendered anchors."""
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

PHRASES = {
    # C1: geopolitical narration (regulatory urgency)
    "C1_geo_war":       "الحرب الإقليمية",
    "C1_hormuz":        "هرمز",
    "C1_displacement":  "نزوح سكاني",
    "C1_collapse":      "انهيار",
    "C1_war_any":       "الحرب",
    "C1_econ_macro":    "الاقتصاد",
    "C1_security":      "أمن",
    "C1_geopolitical":  "جيوسياسي",
    # C2: internal-doc leak
    "C2_project_instr": "Project Instructions",
    "C2_oprules":       "Operational_Rules",
    "C2_sprint_tag":    "Sprint 2.",
    "C2_sprint_ar":     "سبرنت",
    "C2_changelog":     "CHANGELOG",
    # C3: tier badge
    "C3_mawthuq":       "موثوق",
    "C3_indicative":    "إرشادي",
    "C3_reliable_en":   "reliable",
    "C3_indicative_en": "indicative",
    # C4: IVS/RICS phrasing
    "C4_ivs_rics":      "IVS/RICS",
    "C4_rics":          "RICS",
    "C4_ivs":           "IVS",
    "C4_not_official":  "ليس تقييم",
    "C4_red_book":      "Red Book",
    "C4_vps":           "VPS",
    # C5: buyer prescriptive
    "C5_dont_pay":      "لا تدفع",
    "C5_start_offer":   "ابدأ بعرض",
    "C5_recommend_buy": "نوصي",
    "C5_dont_insist":   "لا تُصرّ",
    # Pattern A markers (Latin tokens inside Arabic flow — LRM target)
    "A_qar":            "QAR",
    "A_pin":            "PIN",
    "A_zone":           "zone",
    "A_rics_inline":    "(RICS",
}

OUT_DIR = os.path.join("docs", "phase0")
files = sorted(f for f in os.listdir(OUT_DIR) if f.endswith(".strings.txt"))

# Header
slugs = [f.replace("brief_", "").replace(".strings.txt", "") for f in files]
print("phrase".ljust(22), *[s.ljust(14) for s in slugs], sep="  ")
print("-" * 90)

per_phrase = {}
for tag, needle in PHRASES.items():
    row_counts = []
    for fn in files:
        path = os.path.join(OUT_DIR, fn)
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        hits = text.count(needle)
        row_counts.append(hits)
    per_phrase[tag] = (needle, row_counts)
    row_str = [str(c) if c else "." for c in row_counts]
    print(tag.ljust(22), *[s.ljust(14) for s in row_str], sep="  ")

print()
print("=" * 70)
print("PHRASES PRESENT IN AT LEAST ONE RENDERED ANCHOR (active scope):")
for tag, (needle, counts) in per_phrase.items():
    if sum(counts) > 0:
        cols = []
        for slug, c in zip(slugs, counts):
            if c:
                cols.append(f"{slug}:{c}")
        print(f"  [{tag}] '{needle}'  ->  {', '.join(cols)}")

print()
print("PHRASES NOT FOUND IN ANY RENDERED ANCHOR (drop or only-in-dead-path):")
for tag, (needle, counts) in per_phrase.items():
    if sum(counts) == 0:
        print(f"  [{tag}] '{needle}'")
