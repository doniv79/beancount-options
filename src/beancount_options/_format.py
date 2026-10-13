# SPDX-License-Identifier: GPL-2.0-or-later
"""Number formatting that matches rustledger's messages byte for byte."""

from decimal import Decimal


def plain(number: Decimal) -> str:
    """Print ``number`` without trailing zeros or an exponent.

    rust_decimal's ``normalize()`` prints ``100``; Python's prints ``1E+2``.
    """
    text = format(number.normalize(), "f")
    return "0" if text == "-0" else text
