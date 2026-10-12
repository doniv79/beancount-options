import datetime
from decimal import Decimal

import pytest

from beancount_options._format import plain
from beancount_options._occ import parse_occ


def test_parses_put_and_call():
    put = parse_occ("AAPL261016P00232500")
    assert put.root == "AAPL"
    assert put.expiry == datetime.date(2026, 10, 16)
    assert put.right == "P"
    assert put.strike == Decimal("232.5")

    call = parse_occ("SPXW261030C06800000")
    assert call.root == "SPXW"
    assert call.right == "C"
    assert call.strike == Decimal(6800)


@pytest.mark.parametrize(
    "symbol",
    [
        "AAPL",
        "AAPL261316P00230000",  # month 13
        "AAPL260230P00230000",  # Feb 30
        "AAPL261032P00230000",  # day 32
        "AAPL261016X00230000",  # not C/P
        "AAPL261016P0023000",  # 7 strike digits
        "TOOLONGX261016P00230000",  # root > 6
        "aapl261016P00230000",  # lowercase root
        "AAPL261016P002300000",  # trailing digit
    ],
)
def test_rejects_non_occ(symbol):
    assert parse_occ(symbol) is None


@pytest.mark.parametrize(
    "number, text",
    [
        ("100", "100"),
        ("1E+2", "100"),
        ("-1", "-1"),
        ("-3.000", "-3"),
        ("2.50", "2.5"),
        ("0.000", "0"),
        ("-0", "0"),
    ],
)
def test_plain(number, text):
    assert plain(Decimal(number)) == text
