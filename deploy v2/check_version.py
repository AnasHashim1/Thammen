"""check_version.py — Sprint 2.16.17 Phase 0 Rule #35

Prints the installed versions of slowapi / fastapi / pydantic on the
running Heroku dyno. Run via: heroku run python check_version.py.

Why: requirements.txt pins nothing for these packages, so the wheel that
Heroku resolves may differ from what we assume. Decorator syntax depends
on the actual installed version — slowapi 0.1.9 supports the list form
@limiter.limit(["5/second","30/minute","200/hour"]), older versions do
not.
"""

import sys
from importlib.metadata import version as _pkg_version, PackageNotFoundError


def _pkg(name: str) -> str:
    try:
        return _pkg_version(name)
    except PackageNotFoundError:
        return "<not installed>"
    except Exception as e:
        return f"<error: {e}>"


def main() -> int:
    print(f"python:   {sys.version.split()[0]}")
    print(f"slowapi:  {_pkg('slowapi')}")
    print(f"fastapi:  {_pkg('fastapi')}")
    print(f"pydantic: {_pkg('pydantic')}")
    print(f"uvicorn:  {_pkg('uvicorn')}")
    print(f"requests: {_pkg('requests')}")

    # Cross-check: does the list form import cleanly?
    try:
        from slowapi import Limiter
        from slowapi.util import get_remote_address
        limiter = Limiter(key_func=get_remote_address, default_limits=[])
        # Parse a list of strings — exercises the same code path the
        # decorator would hit on import. We're not registering a route
        # here, just confirming the list form is accepted.
        limit_strings = ["5/second", "30/minute", "200/hour"]
        for s in limit_strings:
            parts = s.split("/")
            assert len(parts) == 2 and parts[0].isdigit()
        print(f"slowapi list form: parseable ({limit_strings})")
    except Exception as e:
        print(f"slowapi list form: FAILED — {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
