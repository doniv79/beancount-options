"""OCC option symbols.

Option contracts are recognized by their OCC symbol with spaces removed: a
root of 1-6 characters, the expiry as ``YYMMDD``, ``C`` or ``P``, and the
strike x 1000 as 8 digits. ``AAPL261016P00230000`` is the AAPL 2026-10-16
230 put.

Mirrors rustledger's ``option_symbol.rs``; the two must accept and reject
the same symbols.
"""

import datetime
import re
from decimal import Decimal
from typing import NamedTuple, Optional

_OCC_RE = re.compile(r"([A-Z][A-Z0-9.]{0,5})(\d{2})(\d{2})(\d{2})([CP])(\d{8})")


class OccSymbol(NamedTuple):
    """A parsed OCC option symbol."""

    root: str
    expiry: datetime.date
    right: str  # "C" or "P"
    strike: Decimal


def parse_occ(symbol: str) -> Optional[OccSymbol]:
    """Parse ``symbol`` as an OCC option symbol.

    Returns None for anything that is not one, including impossible dates
    such as month 13 or 2026-02-30.
    """
    match = _OCC_RE.fullmatch(symbol)
    if match is None:
        return None
    root, yy, mm, dd, right, strike = match.groups()
    try:
        expiry = datetime.date(2000 + int(yy), int(mm), int(dd))
    except ValueError:
        return None
    return OccSymbol(root, expiry, right, Decimal(strike) / 1000)
