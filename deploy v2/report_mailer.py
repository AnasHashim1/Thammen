"""
report_mailer.py — Operator report-copy by email (the "memory of every report").
Sprint 2.22.0b.42.

WHAT: after every evaluation the operator (Anas) receives an email copy of the
report. The operator's mailbox IS the memory — durable, searchable (by
`report_ref`), backed-up by the mail provider — so there is NO database to run
or back up (Heroku's filesystem is ephemeral; a runtime SQLite would be lost on
every dyno restart). One mechanism gives both "a copy reaches me" AND "a memory
of every report."

DORMANT BY DEFAULT. Sends NOTHING unless BOTH are set at runtime:
  * RESEND_API_KEY      (the transactional-email API key), AND
  * REPORT_COPY_EMAIL   (the recipient — the operator's inbox).
Dormant => every entry point is a silent no-op => zero external data flow.
Optional REPORT_COPY_FROM overrides the sender (default = Resend's test sender
`onboarding@resend.dev`, which delivers ONLY to the Resend account owner's own
verified email — a structural "my reports only" until a domain is verified).

SCOPE / GOVERNANCE (Sprint 2.22.0b.42 decision): enabled for the OPERATOR'S OWN
testing now (no third-party data while the invited beta is unlaunched). The live
a24 privacy notice says the address is processed in-memory and NOT stored;
turning this on for REAL beta users stores a copy (operator inbox + mail
provider) → that line MUST be updated to disclose the operator copy (+ a PDPPL
nod) BEFORE the invited beta opens. The flag is the on/off; the notice update is
the gate for beta-wide use.

ISOLATION: reads ONLY the engine `result` + request identifiers; NEVER mutates
`result`; never raises into the caller (failures are swallowed + logged). Runs in
a FastAPI BackgroundTask so it adds ZERO latency to the response. urllib (stdlib)
is used for the POST — no new dependency.
"""
from __future__ import annotations

import base64
import json
import logging
import os
from typing import Optional

log = logging.getLogger("thammen.report_mailer")

_RESEND_URL = "https://api.resend.com/emails"
_DEFAULT_FROM = "Thammen <onboarding@resend.dev>"
_HTTP_TIMEOUT = 10  # seconds — the background task is off the response path anyway
# api.resend.com is Cloudflare-fronted and blocks the bare Python-urllib User-Agent
# with "error code: 1010" (Operational #61 / RISK_REGISTER R12 — the same bot-integrity
# block thammen.qa has). A browser User-Agent passes. Caught by the b42 live email-send
# test (the dormant-until-activation path 403'd on the first real send).
_BROWSER_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
               "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


# ── activation gate ────────────────────────────────────────────────────────

def mail_enabled() -> bool:
    """Opt-IN, OFF by default. True only when a key AND a recipient are set
    (mirrors the EVAL_CAPTURE_ENABLED / T3_INVENTORY_ENABLED env-flag convention)."""
    return bool(os.getenv("RESEND_API_KEY", "").strip()
                and os.getenv("REPORT_COPY_EMAIL", "").strip())


# ── small pure helpers ─────────────────────────────────────────────────────

def _num(x) -> str:
    """Group-formatted integer for display; '—' when absent."""
    if x is None:
        return "—"
    try:
        return f"{int(round(float(x))):,}"
    except (TypeError, ValueError):
        return str(x)


def _ltr(s) -> str:
    """Wrap a Latin/numeric token as an LTR island so it reads correctly inside
    an RTL email (Rule #25)."""
    return f'<span dir="ltr">{s}</span>'


def _age_str(age):
    """A clean one-line age from the property_basis `building_age_estimate` — which
    is a DICT in the real engine result (b9 shape), NOT a string. Renders the
    floor years, never the raw dict dump."""
    if isinstance(age, dict):
        yrs = age.get("age_floor_years")
        return f"العمر ≥ {yrs} سنة (تقديري)" if yrs else age.get("note_ar")
    return str(age) if age else None


def _asset_label(result: dict) -> str:
    """Arabic asset label, preferring the human label over the engine slug:
    top-level asset_type_ar → service_scope.label_ar → the raw asset_type."""
    return (result.get("asset_type_ar")
            or (result.get("service_scope") or {}).get("label_ar")
            or result.get("asset_type") or "—")


def _summary_fields(result: dict, inputs: dict) -> dict:
    """The salient record drawn from the engine `result` — what the human body
    and the subject are built from. Pure (no I/O, no mutation)."""
    result = result or {}
    inputs = inputs or {}
    v = result.get("valuation") or {}
    lead = v.get("leadership") or {}
    muc = result.get("material_uncertainty") or {}
    pb = result.get("property_basis") or {}
    addr = result.get("address")
    if not addr:
        z, s, b, pin = (inputs.get("zone"), inputs.get("street"),
                        inputs.get("building"), inputs.get("pin"))
        addr = (f"{z}/{s}/{b}" if z is not None else (f"PIN {pin}" if pin else "—"))
    return {
        "report_ref": result.get("report_ref") or "—",
        "report_fp": result.get("report_fp"),                 # None when dormant key
        "address": addr,
        "asset_type": _asset_label(result),
        "amount": v.get("amount"),
        "low": v.get("low"),
        "high": v.get("high"),
        "method": v.get("method") or "—",
        "rule": lead.get("rule") or (v.get("income_triangulation") or {}).get("mode") or "—",
        "lead_note": lead.get("note_ar") or "",
        "muc": muc.get("level") or "—",
        "pin": pb.get("pin"),
        "electricity_no": pb.get("electricity_no"),
        "age": _age_str(pb.get("building_age_estimate")),
        "date": result.get("valuation_date") or "—",
        "engine": result.get("engine_version") or "—",
    }


def _subject(f: dict) -> str:
    """[ثمن] {ref} — {address} — {value} ر.ق  (the inbox search key is the ref)."""
    val = _num(f["amount"]) + " ر.ق" if f["amount"] is not None else "لا تقييم"
    return f"[ثمن] {f['report_ref']} — {f['address']} — {val}"


def _html(f: dict) -> str:
    """A compact, self-contained RTL summary of the report. The full visual report
    is reproducible on thammen.qa from the address + report_ref; the complete JSON
    is attached for an exact archive."""
    fp = _ltr(f["report_fp"]) if f["report_fp"] else "—"
    if f["amount"] is not None:
        value_line = (f'<b>{_ltr(_num(f["amount"]))} ر.ق</b> '
                      f'(النطاق {_ltr(_num(f["low"]))} – {_ltr(_num(f["high"]))})')
    else:
        value_line = "<b>لا تقييم</b> (رفض / بيانات غير كافية)"
    pb_bits = []
    if f["pin"]:
        pb_bits.append(f'الرقم المساحي {_ltr(f["pin"])}')
    if f["electricity_no"]:
        pb_bits.append(f'كهرباء {_ltr(f["electricity_no"])}')
    if f["age"]:
        pb_bits.append(str(f["age"]))
    pb_line = " · ".join(pb_bits) if pb_bits else "—"
    lead_note = f'<div style="color:#555;margin-top:6px">{f["lead_note"]}</div>' if f["lead_note"] else ""
    rows = [
        ("الرقم المرجعيّ", _ltr(f["report_ref"])),
        ("العنوان", f["address"]),
        ("نوع العقار", f["asset_type"]),
        ("القيمة", value_line),
        ("القائد / المنهج", f'{f["rule"]} / {f["method"]}'),
        ("التحفّظ المادّي (MUC)", f["muc"]),
        ("أساس العقار", pb_line),
        ("التاريخ", _ltr(f["date"])),
        ("المحرّك", _ltr(f["engine"])),
        ("البصمة", fp),
    ]
    tr = "".join(
        f'<tr><td style="padding:4px 10px;color:#777;white-space:nowrap">{k}</td>'
        f'<td style="padding:4px 10px">{val}</td></tr>'
        for k, val in rows
    )
    return (
        '<div dir="rtl" style="font-family:Tahoma,Arial,sans-serif;font-size:14px;'
        'color:#16324F;max-width:560px">'
        '<h2 style="color:#A4814A;margin:0 0 4px">ثمّن — نسخة تقرير</h2>'
        f'<table style="border-collapse:collapse;width:100%">{tr}</table>'
        f'{lead_note}'
        '<div style="color:#999;font-size:12px;margin-top:14px">'
        'نسخة آليّة للسجلّات. التقرير الكامل قابل لإعادة التوليد على thammen.qa من العنوان + الرقم '
        'المرجعيّ؛ ملفّ JSON الكامل مرفق.'
        '</div></div>'
    )


def build_email(result: dict, inputs: Optional[dict] = None) -> dict:
    """Engine `result` (+ request identifiers) -> the Resend payload dict. Pure /
    unit-testable: no env, no network. Attaches the FULL result JSON so the email
    is a complete archive of the report."""
    f = _summary_fields(result, inputs or {})
    raw = json.dumps(result or {}, ensure_ascii=False, default=str).encode("utf-8")
    attach_name = f"report-{f['report_ref']}.json".replace("/", "_")
    return {
        "from": os.getenv("REPORT_COPY_FROM", "").strip() or _DEFAULT_FROM,
        "to": [os.getenv("REPORT_COPY_EMAIL", "").strip()],
        "subject": _subject(f),
        "html": _html(f),
        "attachments": [{
            "filename": attach_name,
            "content": base64.b64encode(raw).decode("ascii"),
        }],
    }


# ── guarded entry point (never raises into the caller) ─────────────────────

def _post(payload: dict) -> None:
    """POST the payload to Resend via stdlib urllib (lazy). Raises on HTTP error
    — the caller swallows it."""
    import urllib.request  # stdlib; no new dependency
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        _RESEND_URL, data=body, method="POST",
        headers={
            "Authorization": f"Bearer {os.environ['RESEND_API_KEY'].strip()}",
            "Content-Type": "application/json",
            "User-Agent": _BROWSER_UA,   # Cloudflare 1010 blocks bare urllib (#61)
        },
    )
    with urllib.request.urlopen(req, timeout=_HTTP_TIMEOUT) as resp:
        resp.read()  # drain; a 4xx/5xx raises HTTPError -> swallowed by caller


def send_report_copy(result: dict, inputs: Optional[dict] = None) -> bool:
    """Email ONE report copy to the operator iff enabled; return True iff sent.
    Dormant -> False, no network, NO mutation of `result`. Failures are swallowed
    (the response has already been sent — this runs as a BackgroundTask)."""
    if not mail_enabled():
        return False
    try:
        _post(build_email(result, inputs))
        return True
    except Exception:
        log.warning("report-copy email failed (non-fatal)", exc_info=True)
        return False
