#!/usr/bin/env python3
"""
test_sprint_2_22_0b42.py — Sprint 2.22.0b.42 «نسخة-المُشغِّل بالبريد»
(operator report-copy by email).

Exercises the PRODUCTION report_mailer functions (E14 / Rule #40 — no replica):
  * dormant-by-default gate (RESEND_API_KEY + REPORT_COPY_EMAIL)
  * pure build_email shape (subject/html/recipient/from/attachment)
  * send_report_copy: dormant -> no network; active -> one POST; failures swallowed
  * value-invariance: `result` is NEVER mutated
  * api.py wiring (BackgroundTasks + the two guarded seams)
Run: PYTHONIOENCODING=utf-8 python test_sprint_2_22_0b42.py
"""
import base64
import copy
import json
import os
import sys

import report_mailer as rm

# ── env helpers ─────────────────────────────────────────────────────────────
_VARS = ("RESEND_API_KEY", "REPORT_COPY_EMAIL", "REPORT_COPY_FROM")


def _save_env():
    return {k: os.environ.get(k) for k in _VARS}


def _restore_env(saved):
    for k in _VARS:
        if saved.get(k) is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = saved[k]


def _set(**kw):
    for k in _VARS:
        os.environ.pop(k, None)
    for k, v in kw.items():
        os.environ[k] = v


# ── sample engine results ───────────────────────────────────────────────────
SAMPLE = {
    "address": "54/541/6",
    "asset_type": "standalone_villa",
    # NOTE: the real engine result has NO top-level asset_type_ar; the Arabic label
    # lives in service_scope.label_ar (E14 — match production shape).
    "service_scope": {"label_ar": "فيلا منفردة"},
    "valuation_date": "2026-06-14",
    "engine_version": "thammen-sprint2p22p0b42-report-copy-email",
    "report_ref": "TH-20260614-54541006",
    "report_fp": "abc123def456",
    "valuation": {
        "amount": 2400000, "low": 2400000, "high": 5400000,
        "method": "comparison_thin",
        "leadership": {"rule": "cost_led", "note_ar": "قاد التقديرَ منهجُ الكلفة (DRC)"},
    },
    "material_uncertainty": {"level": "high"},
    # building_age_estimate is a DICT in the real result (b9 shape), NOT a string.
    # electricity_no + water_no are the Kahramaa utility ACCOUNT numbers — personal
    # data, stripped from the operator copy by b43 (E14 — both present in the real result).
    "property_basis": {"pin": "54360025", "electricity_no": "140502", "water_no": "131980",
                       "building_age_estimate": {
                           "surveyed_year": 2009, "age_floor_years": 17,
                           "basis": "qars_survey", "age_basis": "vintage_capped",
                           "note_ar": "عمر تقديري (حدّ أدنى من تاريخ مسح GIS سنة 2009): ≥ 17 سنة",
                           "note_en": "Indicative age (floor, from GIS survey 2009): >= 17 years"}},
}

REFUSAL = {
    "address": "52/903/90",
    "asset_type_ar": "عمارة شقق",
    "report_ref": "TH-20260614-52903090",
    "report_fp": None,
    "valuation": {"amount": None, "low": None, "high": None,
                  "method": "insufficient_data"},
    "material_uncertainty": {"level": "critical"},
}

_results = []


def check(name, cond):
    _results.append((name, bool(cond)))


# ── 1. activation gate ──────────────────────────────────────────────────────
def t_gate():
    _set()  # neither var
    check("dormant: no vars -> disabled", rm.mail_enabled() is False)
    _set(RESEND_API_KEY="re_x")
    check("dormant: key only -> disabled", rm.mail_enabled() is False)
    _set(REPORT_COPY_EMAIL="a@b.co")
    check("dormant: recipient only -> disabled", rm.mail_enabled() is False)
    _set(RESEND_API_KEY="re_x", REPORT_COPY_EMAIL="a@b.co")
    check("active: both set -> enabled", rm.mail_enabled() is True)
    _set(RESEND_API_KEY="   ", REPORT_COPY_EMAIL="a@b.co")
    check("dormant: blank key -> disabled", rm.mail_enabled() is False)


# ── 2. pure build_email ─────────────────────────────────────────────────────
def t_build():
    _set(RESEND_API_KEY="re_x", REPORT_COPY_EMAIL="anas@example.qa")
    p = rm.build_email(SAMPLE, {"zone": 54, "street": 541, "building": 6})
    check("build: to == recipient list", p["to"] == ["anas@example.qa"])
    check("build: default from = resend test sender", p["from"] == rm._DEFAULT_FROM)
    check("build: subject carries ثمن tag", "[ثمن]" in p["subject"])
    check("build: subject carries report_ref", "TH-20260614-54541006" in p["subject"])
    check("build: subject carries grouped value", "2,400,000" in p["subject"])
    check("build: html carries address", "54/541/6" in p["html"])
    check("build: html carries report_ref", "TH-20260614-54541006" in p["html"])
    check("build: html carries the Arabic asset label (via service_scope.label_ar)",
          "فيلا منفردة" in p["html"] and "standalone_villa" not in p["html"])
    check("build: html carries leadership note", "منهجُ الكلفة" in p["html"])
    # b42.2 (E14 fix): age must render CLEAN, never the raw building_age_estimate dict
    check("build: age renders clean — no raw dict dump",
          "{'surveyed_year'" not in p["html"] and "age_floor_years" not in p["html"])
    check("build: age renders the floor years", "العمر ≥ 17 سنة" in p["html"])
    check("build: html rtl + ltr number islands", 'dir="rtl"' in p["html"] and 'dir="ltr"' in p["html"])
    # b43: personal utility ACCOUNT numbers are stripped from the body — the address
    # + property identity (PIN, age) stay; the account numbers do not.
    check("b43: html keeps the cadastral PIN (property data)", "54360025" in p["html"])
    check("b43: html does NOT carry the electricity account number",
          "140502" not in p["html"] and "كهرباء" not in p["html"])
    check("b43: html does NOT carry the water account number", "131980" not in p["html"])
    # attachment = base64 of the result MINUS the personal utility-account fields
    att = p["attachments"][0]
    check("build: attachment filename slug-safe (no /)", "/" not in att["filename"])
    decoded = json.loads(base64.b64decode(att["content"]).decode("utf-8"))
    check("b43: attachment == result minus the personal account fields",
          decoded == rm._scrub_personal(SAMPLE))
    check("b43: attachment keeps the property identity (address + PIN)",
          decoded["address"] == "54/541/6" and decoded["property_basis"]["pin"] == "54360025")
    check("b43: attachment dropped electricity_no + water_no",
          "electricity_no" not in decoded["property_basis"]
          and "water_no" not in decoded["property_basis"])
    check("b43: ISOLATION — build_email did NOT mutate the caller's result",
          SAMPLE["property_basis"]["electricity_no"] == "140502"
          and SAMPLE["property_basis"]["water_no"] == "131980")
    # from override
    _set(RESEND_API_KEY="re_x", REPORT_COPY_EMAIL="anas@example.qa",
         REPORT_COPY_FROM="Thammen <reports@thammen.qa>")
    p2 = rm.build_email(SAMPLE, {})
    check("build: REPORT_COPY_FROM override honored", p2["from"] == "Thammen <reports@thammen.qa>")


def t_build_refusal_and_fallback():
    _set(RESEND_API_KEY="re_x", REPORT_COPY_EMAIL="anas@example.qa")
    p = rm.build_email(REFUSAL, {})
    check("refusal: subject says لا تقييم", "لا تقييم" in p["subject"])
    check("refusal: html says لا تقييم", "لا تقييم" in p["html"])
    check("refusal: no fingerprint -> em dash, no crash", "—" in p["html"])
    # address fallback from inputs when result has no 'address'
    noaddr = {"report_ref": "TH-x", "valuation": {"amount": 100}}
    pa = rm.build_email(noaddr, {"zone": 55, "street": 296, "building": 13})
    check("fallback: address built from zone/street/building", "55/296/13" in pa["subject"])
    pp = rm.build_email({"report_ref": "TH-y", "valuation": {"amount": 1}},
                        {"pin": "74328443"})
    check("fallback: address built from PIN", "PIN 74328443" in pp["subject"])


# ── 3. send_report_copy isolation ───────────────────────────────────────────
def t_send_dormant_no_network():
    _set()  # dormant
    calls = []
    orig = rm._post
    rm._post = lambda payload: calls.append(payload)  # would record if reached
    try:
        sent = rm.send_report_copy(SAMPLE, {})
    finally:
        rm._post = orig
    check("send dormant -> returns False", sent is False)
    check("send dormant -> NO network (POST not reached)", calls == [])


def t_send_active_one_post():
    _set(RESEND_API_KEY="re_x", REPORT_COPY_EMAIL="anas@example.qa")
    calls = []
    orig = rm._post
    rm._post = lambda payload: calls.append(payload)
    try:
        sent = rm.send_report_copy(SAMPLE, {"zone": 54, "street": 541, "building": 6})
    finally:
        rm._post = orig
    check("send active -> returns True", sent is True)
    check("send active -> exactly one POST", len(calls) == 1)
    check("send active -> payload to recipient", calls and calls[0]["to"] == ["anas@example.qa"])


def t_send_swallows_failure():
    _set(RESEND_API_KEY="re_x", REPORT_COPY_EMAIL="anas@example.qa")

    def boom(payload):
        raise RuntimeError("resend 500 / network down")

    orig = rm._post
    rm._post = boom
    raised = False
    try:
        try:
            sent = rm.send_report_copy(SAMPLE, {})
        except Exception:
            raised = True
            sent = None
    finally:
        rm._post = orig
    check("send failure -> never raises into caller", raised is False)
    check("send failure -> returns False", sent is False)


# ── 4. value-invariance (the result is NEVER mutated) ───────────────────────
def t_value_invariance():
    _set(RESEND_API_KEY="re_x", REPORT_COPY_EMAIL="anas@example.qa")
    before = copy.deepcopy(SAMPLE)
    rm.build_email(SAMPLE, {"zone": 54})
    orig = rm._post
    rm._post = lambda payload: None
    try:
        rm.send_report_copy(SAMPLE, {"zone": 54})
    finally:
        rm._post = orig
    check("value-invariance: result unchanged by build+send", SAMPLE == before)


# ── 5. api.py wiring ────────────────────────────────────────────────────────
def t_api_wiring():
    src = open("api.py", encoding="utf-8").read()
    check("api: imports BackgroundTasks", "BackgroundTasks" in src
          and "import report_mailer as _mailer" in src)
    check("api: defensive _MAIL_OK guard", "_MAIL_OK = True" in src)
    check("api: quick handler takes background_tasks",
          "background_tasks: BackgroundTasks" in src)
    check("api: seam guarded + add_task(send_report_copy)",
          src.count("background_tasks.add_task(") == 2
          and "_mailer.send_report_copy" in src)
    check("api: seam gated on _MAIL_OK", src.count("if _MAIL_OK:") == 2)


# ── 6. the real _post sets a browser User-Agent (Cloudflare 1010 fix, #61) ──
def t_post_browser_ua():
    import urllib.request
    os.environ["RESEND_API_KEY"] = "re_unit_key"
    captured = {}

    class _FakeResp:
        def read(self): return b'{"id":"x"}'
        def __enter__(self): return self
        def __exit__(self, *a): return False

    orig = urllib.request.urlopen
    urllib.request.urlopen = lambda req, timeout=None: (captured.setdefault("req", req), _FakeResp())[1]
    try:
        rm._post({"from": "x", "to": ["a@b.co"], "subject": "s", "html": "h"})
    finally:
        urllib.request.urlopen = orig
    req = captured.get("req")
    check("_post: reached urlopen (real path)", req is not None)
    check("_post: sets a browser User-Agent (Cloudflare 1010 fix #61)",
          req is not None and "Mozilla/5.0" in (req.get_header("User-agent") or ""))
    check("_post: carries the Authorization bearer",
          req is not None and (req.get_header("Authorization") or "").startswith("Bearer re_"))
    check("_post: targets the Resend /emails endpoint",
          req is not None and req.full_url == rm._RESEND_URL)


def main():
    saved = _save_env()
    try:
        for fn in (t_gate, t_build, t_build_refusal_and_fallback,
                   t_send_dormant_no_network, t_send_active_one_post,
                   t_send_swallows_failure, t_value_invariance, t_api_wiring,
                   t_post_browser_ua):
            fn()
    finally:
        _restore_env(saved)
    passed = sum(1 for _, ok in _results if ok)
    total = len(_results)
    for name, ok in _results:
        print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    print(f"\n{passed}/{total} PASS")
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
