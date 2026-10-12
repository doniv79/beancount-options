"""Ports of rustledger's check_option_expiry tests (T01-T10).

Each test asserts an exact error count and that beancount itself reported
nothing, so a fixture that doesn't balance can't hide behind the plugin.
"""

from helpers import later, leg, load

from beancount_options import check_option_expiry as plugin_module

PUT = "AAPL261016P00230000"


def errors(body):
    ours, others, _ = load("check_option_expiry", body)
    assert others == [], others
    return ours


def test_t01_closed_before_expiry():
    assert (
        errors(leg("2026-09-02", "-1", PUT) + leg("2026-09-20", "1", PUT) + later("2026-11-01"))
        == []
    )


def test_t02_closed_on_expiry_day():
    assert (
        errors(leg("2026-09-02", "-1", PUT) + leg("2026-10-16", "1", PUT) + later("2026-11-01"))
        == []
    )


def test_t03_short_left_open():
    ours, others, _ = load(
        "check_option_expiry", leg("2026-09-02", "-1", PUT) + later("2026-10-17")
    )
    assert others == []
    assert len(ours) == 1
    err = ours[0]
    assert err.message == (
        "AAPL261016P00230000 expired 2026-10-16 but -1 contract(s) remain open "
        "in Assets:Broker:Options"
    )
    # Reported at the transaction that opened the position.
    assert err.entry.narration == "option leg"
    assert err.entry.date.isoformat() == "2026-09-02"
    assert err.source["filename"] == err.entry.meta["filename"]
    assert err.source["lineno"] == err.entry.meta["lineno"]


def test_t04_long_left_open():
    found = errors(leg("2026-09-03", "1", "SPXW261030C06800000") + later("2026-11-02"))
    assert len(found) == 1
    assert " but 1 contract(s) " in found[0].message


def test_t05_ledger_ends_on_or_before_expiry():
    assert errors(leg("2026-09-02", "-1", PUT) + later("2026-10-16")) == []
    assert errors(leg("2026-09-02", "-1", PUT)) == []


def test_t06_tracked_per_account():
    found = errors(
        leg("2026-09-02", "-1", PUT)
        + leg("2026-09-02", "-1", PUT, account="Assets:IRA:Options")
        + leg("2026-09-20", "1", PUT)
        + later("2026-11-01")
    )
    assert len(found) == 1
    assert found[0].message.endswith(" in Assets:IRA:Options")


def test_t07_partial_close():
    sym = "AAPL261016P00232500"
    found = errors(leg("2026-09-02", "-3", sym) + leg("2026-09-20", "2", sym) + later("2026-11-01"))
    assert len(found) == 1
    assert " but -1 contract(s) " in found[0].message


def test_t08_ignores_non_option_commodities():
    body = "".join(
        leg("2026-09-02", "-1", sym)
        for sym in [
            "AAPL261316P00230000",  # month 13
            "AAPL261032P00230000",  # day 32
            "AAPL261016X00230000",  # not C/P
            "AAPL261016P0023000",  # 7 strike digits
            "TOOLONGX261016P00230000",  # root > 6
        ]
    )
    assert errors(leg("2026-09-02", "100", "AAPL") + body + later("2027-01-01")) == []


def test_t09_roll():
    roll = """
2026-09-15 * "roll"
  Assets:Broker:Options  1 AAPL260918C00270000 @ 100 USD
  Assets:Broker:Options  -1 AAPL261016C00280000 @ 100 USD
"""
    assert errors(leg("2026-09-05", "-1", "AAPL260918C00270000") + roll + later("2026-10-01")) == []


def test_t10_two_contracts_in_symbol_order():
    found = errors(
        leg("2026-09-03", "1", "SPY261016C00700000")
        + leg("2026-09-02", "-1", PUT)
        + later("2026-11-01")
    )
    assert [e.message.split()[0] for e in found] == [PUT, "SPY261016C00700000"]


def test_reopened_position_reports_the_reopening_entry():
    found = errors(
        leg("2026-09-02", "-1", PUT)
        + leg("2026-09-10", "1", PUT)
        + leg("2026-09-12", "-2", PUT)
        + later("2026-11-01")
    )
    assert len(found) == 1
    assert found[0].entry.date.isoformat() == "2026-09-12"
    assert " but -2 contract(s) " in found[0].message


def test_entries_returned_unchanged():
    _, _, loaded = load("check_option_expiry", leg("2026-09-02", "-1", PUT) + later("2026-11-01"))
    out, _ = plugin_module.check_option_expiry(loaded, {})
    assert out is loaded


def test_empty_ledger():
    assert plugin_module.check_option_expiry([], {}) == ([], [])


def test_errors_sorted_by_account_then_symbol():
    found = errors(
        leg("2026-09-02", "-1", "SPY261016C00700000")
        + leg("2026-09-02", "-1", PUT, account="Assets:IRA:Options")
        + leg("2026-09-03", "-1", PUT)
        + later("2026-11-01")
    )
    assert [(e.message.split()[0], e.message.split()[-1]) for e in found] == [
        (PUT, "Assets:Broker:Options"),
        ("SPY261016C00700000", "Assets:Broker:Options"),
        (PUT, "Assets:IRA:Options"),
    ]


def test_unsorted_input_is_walked_in_date_order():
    # Walked backwards, the 09-02 entry would look like the opener.
    body = leg("2026-09-02", "-1", PUT) + leg("2026-09-10", "1", PUT) + leg("2026-09-12", "-1", PUT)
    _, _, loaded = load("check_option_expiry", body + later("2026-11-01"))
    _, found = plugin_module.check_option_expiry(list(reversed(loaded)), {})
    assert len(found) == 1
    assert found[0].entry.date.isoformat() == "2026-09-12"


def test_posting_with_missing_number_is_skipped():
    import datetime

    from beancount.core import amount, data
    from beancount.core.number import MISSING

    meta = data.new_metadata("ledger.beancount", 1)
    posting = data.Posting(
        "Assets:Broker:Options", amount.Amount(MISSING, PUT), None, None, None, None
    )
    txn = data.Transaction(
        meta, datetime.date(2026, 9, 2), "*", None, "x", frozenset(), frozenset(), [posting]
    )
    later_txn = txn._replace(date=datetime.date(2026, 11, 1), postings=[])
    assert plugin_module.check_option_expiry([txn, later_txn], {}) == ([txn, later_txn], [])
