"""Isolated tests — Sprint 2.22.0a.4 (Disclosure & Framing Honesty).

Covers the two shipped surfaces:

  T-method (a+b) — methodology_ar headline honesty:
    (a) the misleading "توفيق ثلاثي الطرق" (three-way reconciliation) claim
        is dropped — Phase 0 (P0.2) proved the engine never blends the three
        approaches; valuation = primary['value'] = Sales Comparison alone.
    (b) the embedded Latin ("AVM"/"Sales Comparison Approach") that lived on
        the SAME headline string is gone — the replacement is pure Arabic.
    The VPS-4 provenance (formerly inside Layer A) relocates onto the
    methodology SURFACE as the methodology_ar second sentence.

  T2.8 — disclaimer consolidation (JSON-merge-only variant, per Anas):
    The main-path methodology_disclaimer_ar (Layer A) duplicated the
    top-level `disclaimer` (Layer D). P0.1 proved A was JSON-only (never
    rendered). It folds into D. The OTHER 5 methodology_disclaimer_ar sites
    carry genuine per-path methodology caveats (NOT duplicates of D) and are
    intentionally preserved. E (service_scope.disclaimer_ar) rename is
    DEFERRED (Rule #47 — rename is its own pass).

E14 compliance: ENGINE_VERSION / SPRINT_TAG are exercised against the live
production module (not echoed source). The methodology_ar headline is built
deep inside _build_unified_output, which requires a full live-evaluation
fixture (ev.valuation, factors_detail, …); that surface is exercised by the
post-deploy smoke (acceptance #3), while structure/copy invariants here use
source assertions (the project's accepted pattern — cf. c3, 2.22.0a.3).

Run: PYTHONIOENCODING=utf-8 python test_sprint_2p22p0a4_disclosure_framing.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent
sys.path.insert(0, str(REPO_ROOT))


def _read(name: str) -> str:
    return (REPO_ROOT / name).read_text(encoding='utf-8')


_EU_SRC = _read('evaluate_unified.py')
_INDEX_SRC = _read('index.html')

_PASS = 0
_TOTAL = 0


def _check(cond: bool, name: str, msg: str) -> None:
    global _PASS, _TOTAL
    _TOTAL += 1
    if cond:
        _PASS += 1
        print(f'  PASS {name}')
    else:
        print(f'  FAIL {name} — {msg}')


# ──────────────────────────────────────────────────────────────────────
# Live production constants (E14 — exercises the real module)
# ──────────────────────────────────────────────────────────────────────
def test_engine_version_and_sprint_tag_live():
    import evaluate_unified as eu
    # Forward-compatible: do NOT hard-pin the historical 2.22.0a.4 string — that
    # is the 2.19.1 brittle-pin anti-pattern (fails on every later version bump,
    # e.g. Sprint 2.22.0a.5). Assert the constants are well-formed instead.
    _check(
        isinstance(eu.ENGINE_VERSION, str) and eu.ENGINE_VERSION.startswith('thammen-sprint'),
        'test_engine_version_live',
        f'ENGINE_VERSION={eu.ENGINE_VERSION!r}',
    )
    _check(
        isinstance(eu.SPRINT_TAG, str) and eu.SPRINT_TAG != '',
        'test_sprint_tag_live',
        f'SPRINT_TAG={eu.SPRINT_TAG!r}',
    )


# ──────────────────────────────────────────────────────────────────────
# T-method (a) — reconciliation over-claim dropped
# ──────────────────────────────────────────────────────────────────────
def test_tmethod_a_reconciliation_claim_dropped():
    _check(
        'توفيق ثلاثي الطرق' not in _EU_SRC,
        'test_tmethod_a_reconciliation_claim_dropped',
        "misleading 'توفيق ثلاثي الطرق' headline still present (P0.2: no blend)",
    )


def test_tmethod_basis_statement_present():
    _check(
        'أساس التقدير هو منهج المقارنة بالمبيعات.' in _EU_SRC,
        'test_tmethod_basis_statement_present',
        'bare basis-of-estimate statement missing from methodology_ar',
    )


# ──────────────────────────────────────────────────────────────────────
# T-method (b) — Latin gone, provenance relocated to methodology surface
# ──────────────────────────────────────────────────────────────────────
def test_tmethod_b_old_latin_headline_gone():
    _check(
        'AVM مبني على Sales Comparison Approach' not in _EU_SRC,
        'test_tmethod_b_old_latin_headline_gone',
        'old Latin-in-Arabic headline string still present',
    )


def test_tmethod_headline_is_bare_no_provenance():
    # Per the completed multi-AI Resolution ("reduce, not add" + bare-line),
    # the VPS-4 provenance is NOT promoted to the visible headline. The
    # methodology_ar headline stays a single bare sentence; the previously
    # JSON-only/invisible provenance is dropped (deferred to a secondary
    # expandable surface in a future sub-sprint).
    _check(
        'نموذج تقييم آلي وفق معيار RICS VPS 4' not in _EU_SRC,
        'test_tmethod_headline_is_bare_no_provenance',
        'VPS-4 provenance was added to the headline — violates bare-line '
        'Resolution + reduce-not-add theme',
    )


# ──────────────────────────────────────────────────────────────────────
# T2.8 — A→D fold (main path only) + 5 other A-sites preserved
# ──────────────────────────────────────────────────────────────────────
def test_t28_main_path_A_disclaimer_folded():
    # The redundant main-path Layer A (the VPS-4 disclaimer that duplicated D)
    # must be gone. Its distinctive opening is the Latin "(Automated Valuation
    # Model) وفق RICS VPS 4" inside a methodology_disclaimer_ar.
    _check(
        'تقدير آلي (Automated Valuation Model) وفق RICS VPS 4.' not in _EU_SRC,
        'test_t28_main_path_A_disclaimer_folded',
        'main-path Layer A (duplicate of D) still present',
    )


def test_t28_other_five_A_sites_preserved():
    # These 5 per-path methodology caveats are NOT duplicates of D and must
    # survive the A→D fold (premise-check correction).
    preserved = [
        'تقدير الأصول من هذه الفئة يحتاج طريقة الدخل',          # @1932 unsupported
        "base['methodology_disclaimer_ar'] = copy['disclaimer_ar']",  # @2251 hybrid T2
        'هذا ليس تقييماً نهائياً، بل أداة فحص',                 # @2354 asking-price tool
        'تقدير آلي مبني على الإيجار المُقدَّم من العميل',        # @2585 income path
        'لإنتاج تقييم موثوق',                                    # @2703 scope (c3 pin)
    ]
    for frag in preserved:
        _check(
            frag in _EU_SRC,
            f'test_t28_preserved::{frag[:24]}',
            f'preserved per-path caveat missing: {frag!r}',
        )


# ──────────────────────────────────────────────────────────────────────
# C4 lock — Layer D not-a-formal-valuation wording preserved verbatim
# ──────────────────────────────────────────────────────────────────────
def test_c4_disclaimer_lock_preserved():
    c4 = 'ولا يُعتبر تقرير تثمين رسمي صادر عن مثمّن مرخّص وفق معايير RICS/IVS'
    _check(
        _EU_SRC.count(c4) >= 5,
        'test_c4_disclaimer_lock_preserved',
        f'C4 verbatim count {_EU_SRC.count(c4)} < 5 (Layer D regression)',
    )


# ──────────────────────────────────────────────────────────────────────
# Render invariants (P0.1 map — must stay true)
# ──────────────────────────────────────────────────────────────────────
def test_layer_D_renders_in_brief():
    _check(
        'd.disclaimer' in _INDEX_SRC,
        'test_layer_D_renders_in_brief',
        'top-level disclaimer (Layer D) render hook missing from index.html',
    )


def test_layer_A_not_rendered_in_brief():
    # P0.1 invariant: methodology_disclaimer_ar (A) is JSON-only — never
    # referenced by the brief renderer. Folding it is render-invisible.
    _check(
        'methodology_disclaimer_ar' not in _INDEX_SRC,
        'test_layer_A_not_rendered_in_brief',
        'index.html now references methodology_disclaimer_ar — P0.1 broken',
    )


def test_methodology_ar_reaches_ui():
    _check(
        'methodology_ar' in _INDEX_SRC,
        'test_methodology_ar_reaches_ui',
        'methodology_ar render hook missing — provenance would not surface',
    )


def test_E_rename_deferred_E_still_renders():
    # E (service_scope.disclaimer_ar) rename DEFERRED per Rule #47 — it must
    # still render as today (no silent disappearance).
    _check(
        'ss.disclaimer_ar' in _INDEX_SRC,
        'test_E_rename_deferred_E_still_renders',
        'service_scope.disclaimer_ar (Layer E) render hook missing',
    )


if __name__ == '__main__':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

    print('=' * 70)
    print('Sprint 2.22.0a.4 — Disclosure & Framing Honesty (isolated)')
    print('=' * 70)

    test_engine_version_and_sprint_tag_live()
    test_tmethod_a_reconciliation_claim_dropped()
    test_tmethod_basis_statement_present()
    test_tmethod_b_old_latin_headline_gone()
    test_tmethod_headline_is_bare_no_provenance()
    test_t28_main_path_A_disclaimer_folded()
    test_t28_other_five_A_sites_preserved()
    test_c4_disclaimer_lock_preserved()
    test_layer_D_renders_in_brief()
    test_layer_A_not_rendered_in_brief()
    test_methodology_ar_reaches_ui()
    test_E_rename_deferred_E_still_renders()

    print('=' * 70)
    print(f'PASSED: {_PASS}/{_TOTAL}')
    print('=' * 70)
    sys.exit(0 if _PASS == _TOTAL else 1)
