"""Sprint 2.22.0a.2 Phase 0.1 — summarize anchor briefs (throwaway, Rule #34).

Reads docs/phase0/brief_*.json and writes an ASCII-safe text summary
+ a per-anchor *flat-text dump* of rendered Arabic strings (for grep).
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

OUT_DIR = os.path.join("docs", "phase0")


def collect_strings(obj, out, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            collect_strings(v, out, f"{path}.{k}" if path else k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            collect_strings(v, out, f"{path}[{i}]")
    elif isinstance(obj, str):
        if obj.strip():
            out.append((path, obj))


def main():
    files = sorted(f for f in os.listdir(OUT_DIR) if f.startswith("brief_") and f.endswith(".json"))
    summary_rows = []
    for fn in files:
        with open(os.path.join(OUT_DIR, fn), encoding="utf-8") as fh:
            rec = json.load(fh)
        body = rec.get("body_parsed") or {}
        rb = body.get("refusal_reason") or {}
        row = {
            "file": fn,
            "anchor": rec["anchor_label"],
            "payload": rec["payload"],
            "status": rec["status"],
            "elapsed_s": rec["elapsed_s"],
            "engine_version": rec.get("engine_version"),
            "asset_type": rec.get("asset_type"),
            "asset_type_ar": rec.get("asset_type_ar"),
            "valuation_amount": rec.get("valuation_amount"),
            "decomp_status": rec.get("decomp_status"),
            "refusal_trigger_id": rb.get("trigger_id"),
            "refusal_message_ar_present": bool(rb.get("message_ar")),
            "methodology_ar_present": bool(body.get("methodology_ar")),
            "methodology_disclaimer_ar_present": bool(body.get("methodology_disclaimer_ar")),
            "subtype_zoning_mismatch": "subtype_zoning_mismatch" in body,
            "material_uncertainty_present": bool(body.get("material_uncertainty")),
            "brief_section_count": len((body.get("brief") or {}).get("sections", [])),
            "scope_of_service_status": (body.get("scope_of_service") or {}).get("status"),
        }
        summary_rows.append(row)

        # Flat string dump for grep
        strings = []
        collect_strings(body, strings)
        dump_path = os.path.join(OUT_DIR, fn.replace(".json", ".strings.txt"))
        with open(dump_path, "w", encoding="utf-8") as fh:
            for path, text in strings:
                # one line per string. Tab-separated path|text. Newlines in text replaced.
                clean = text.replace("\n", " \\n ").replace("\r", " ")
                fh.write(f"{path}\t{clean}\n")
        print(f"wrote {dump_path}  ({len(strings)} strings)")

    summary_path = os.path.join(OUT_DIR, "anchor_summary_clean.json")
    with open(summary_path, "w", encoding="utf-8") as fh:
        json.dump(summary_rows, fh, ensure_ascii=False, indent=2)
    print()
    print("=" * 70)
    for r in summary_rows:
        # ASCII-safe only
        print(f"  {r['file']:30s} status={r['status']} t={r['elapsed_s']}s "
              f"asset_type={r['asset_type']} val={r['valuation_amount']} "
              f"refusal={r['refusal_trigger_id']} sections={r['brief_section_count']}")


if __name__ == "__main__":
    main()
