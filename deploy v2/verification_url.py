"""Sprint 2.22.0a/7 — verification_url generation.

Universal audit-trail URL emitted on every Thammen response (value-producing
AND refusal — orthogonal to tier_label / refusal_reason gating per
KICKOFF §5.2). The URL returns 404 in 2.22.0a — the /verify endpoint UI
is deferred to Sprint 2.22.0.1.

Design decisions (Anas, Sprint 2.22.0a/7 R-protocol):
  Q1 — Pure deterministic, NO salt.
       Verification URL ≠ authentication; same evaluation must yield
       same token; future audit-trail backfill needs to recompute tokens
       from historical evaluations.
  Q2 — Day boundary reads `valuation_date` directly (local-time YYYY-MM-DD,
       per /3 R3 finding). Single source of truth; immune to multi-second
       drift across midnight.
  Q3 — No versioning prefix in URL. Token is opaque; if format changes in
       2.22.0b+, the /verify endpoint redirector handles old-format → new-
       format. Honors "skip versioning in MVP".
  Q4 — Falsy `address` or `valuation_date` → returns None. Field present in
       response as None; mirrors tier_label=None / refusal_reason=None.

Token mechanics (R4 finding):
  identifier = response['address']     # uniform across ZSB and PIN modes
  day        = response['valuation_date']
  digest     = sha256(f'{identifier}|{day}'.encode('utf-8')).digest()
  token      = base32(digest)[:12].decode('ascii')   # 12-char [A-Z2-7]

Architectural note (R6 finding):
  Injection happens once in `evaluate_unified._attach_scope` — the
  universal response gate. NO per-site injection. This is a deliberate
  divergence from /5 (refusal_reason was per-site because each site
  needed different `method` + `asset_type` + `plot_area_m2` context that
  varies per call site; verification_url only needs `address` +
  `valuation_date` which are uniformly present at response top-level).
"""
from __future__ import annotations

import base64
import hashlib
import re
from typing import Optional

# Module-level base URL. Future env-var override can be added with a single
# `os.getenv('THAMMEN_VERIFY_BASE_URL', '<default>')` without touching
# evaluate_unified.py or any caller (R1 finding).
THAMMEN_VERIFY_BASE_URL = 'https://thammen.qa/verify'

# Token format: 12 characters from RFC 4648 base32 alphabet
# (uppercase A-Z + digits 2-7). URL-safe; no padding handling required after
# truncation. Regex used by `is_valid_token_format` and downstream /verify
# endpoint (Sprint 2.22.0.1) to reject malformed paths fast.
TOKEN_LENGTH = 12
_TOKEN_REGEX = re.compile(r'^[A-Z2-7]{12}$')


def generate_token(identifier: str, day: str) -> str:
    """Generate a deterministic 12-char token from (identifier, day).

    Args:
        identifier: The response['address'] string. Uniform across ZSB
            mode ('61/875/20') and PIN mode ('أرض في الدفنة — PIN 12345').
        day: The response['valuation_date'] string in YYYY-MM-DD format
            (local Qatar time per /3 R3 finding).

    Returns:
        A 12-character uppercase base32 token (alphabet A-Z + 2-7).

    Raises:
        TypeError: If identifier or day is not a string (mirrors strict
            stdlib hashlib behaviour — fail loud).

    Determinism guarantee:
        Same (identifier, day) tuple always yields the same token across
        processes and Python versions, because SHA-256 + base32 are
        standard, deterministic, and stdlib-stable.
    """
    if not isinstance(identifier, str) or not isinstance(day, str):
        raise TypeError(
            f'generate_token requires str identifier and str day; '
            f'got {type(identifier).__name__}, {type(day).__name__}'
        )
    payload = f'{identifier}|{day}'.encode('utf-8')
    digest = hashlib.sha256(payload).digest()
    # base32 yields ceil(len(digest) * 8 / 5) = 56 chars for a 32-byte
    # SHA-256 digest. Truncate to TOKEN_LENGTH (12). The base32 alphabet
    # contains no padding within the body, so a simple slice is safe.
    encoded = base64.b32encode(digest).decode('ascii')
    return encoded[:TOKEN_LENGTH]


def build_verification_url(
    address: Optional[str],
    valuation_date: Optional[str],
) -> Optional[str]:
    """Build the full verification URL from response top-level fields.

    Per Q4 (a) — defensive None handling: if either input is falsy (None,
    empty string, or the '—' sentinel sometimes used when no address can
    be derived), return None. The frontend skips link rendering when this
    field is None; mirrors the tier_label=None / refusal_reason=None
    pattern for orthogonal opt-out signaling.

    Args:
        address: The response['address'] string, or None.
        valuation_date: The response['valuation_date'] string in YYYY-MM-DD
            format, or None.

    Returns:
        A full URL like 'https://thammen.qa/verify/K3HBNZ2L5MQR' when both
        inputs are populated, else None.
    """
    if not address or not valuation_date:
        return None
    # Reject the '—' em-dash sentinel used by _build_reality_stop_response
    # when neither district nor PIN is available — that's not a real
    # identifier and a token over it has no audit value.
    if address.strip() in ('—', ''):
        return None
    try:
        token = generate_token(address, valuation_date)
    except (TypeError, ValueError, UnicodeError):
        # Defensive: any failure in the token math returns None rather
        # than poisoning the response. The verification URL is a non-
        # critical UI affordance — its absence does not break valuation.
        return None
    return f'{THAMMEN_VERIFY_BASE_URL}/{token}'


def is_valid_token_format(token: str) -> bool:
    """Return True iff `token` matches the canonical 12-char [A-Z2-7] shape.

    Used by:
      - The isolated test file to assert generated tokens stay in shape.
      - The future /verify endpoint (Sprint 2.22.0.1) for fast 404 short-
        circuit on malformed paths before any DB lookup.

    Args:
        token: Any string (or non-string — returns False).

    Returns:
        bool — True only for an exact 12-char uppercase base32 match.
    """
    if not isinstance(token, str):
        return False
    return bool(_TOKEN_REGEX.match(token))
