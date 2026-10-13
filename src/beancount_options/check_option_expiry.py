# SPDX-License-Identifier: GPL-2.0-or-later
"""Error on option contracts still open after their expiry date.

Option contracts are recognized by their OCC symbol (see ``_occ``). Every
other commodity is ignored.

"Today" is the date of the last entry of any kind in the ledger, not the system clock,
so the result is the same on every run. A contract is reported when its net
units in an account are non-zero and the ledger contains an entry dated
after its expiry. A close dated on the expiry day itself is fine.

The plugin only reports: entries are returned unchanged, so a ledger stays
complete without it.

Python counterpart of rustledger's native ``check_option_expiry``; messages
and locations match it exactly.
"""

from collections import namedtuple
from decimal import Decimal

from beancount.core import data

from beancount_options._format import plain
from beancount_options._occ import parse_occ

__plugins__ = ("check_option_expiry",)

OptionExpiryError = namedtuple("OptionExpiryError", "source message entry")


class _Position:
    __slots__ = ("expiry", "net", "opened_by")

    def __init__(self, expiry, opened_by):
        self.expiry = expiry
        self.net = Decimal(0)
        # The entry that opened the current position: the last one that
        # moved it away from flat or across zero.
        self.opened_by = opened_by


def _entry_deltas(entry):
    """Net option units per (account, symbol) in one transaction.

    Netting first makes the result independent of posting order, and makes
    an entry whose legs cancel a no-op.
    """
    deltas = {}
    expiries = {}
    for posting in entry.postings:
        units = posting.units
        if units is None or not isinstance(units.number, Decimal):
            continue
        occ = parse_occ(units.currency)
        if occ is None:
            continue
        key = (posting.account, units.currency)
        deltas[key] = deltas.get(key, Decimal(0)) + units.number
        expiries[key] = occ.expiry
    return [(key, delta, expiries[key]) for key, delta in deltas.items()]


def check_option_expiry(entries, options_map, config=None):
    """Report option positions left open past expiry.

    Args:
      entries: the ledger's directives.
      options_map: the ledger's options (unused).
      config: unused; the plugin takes no configuration.
    Returns:
      The entries, unchanged, and a list of errors.
    """
    del options_map, config

    # sorted() is stable, so same-day entries keep their order.
    positions = {}
    for entry in sorted(entries, key=lambda e: e.date):
        if not isinstance(entry, data.Transaction):
            continue
        for key, delta, expiry in _entry_deltas(entry):
            pos = positions.get(key)
            if pos is None:
                pos = positions[key] = _Position(expiry, entry)
            new_net = pos.net + delta
            if pos.net == 0 or (pos.net < 0 < new_net) or (new_net < 0 < pos.net):
                pos.opened_by = entry
            pos.net = new_net

    errors = []
    if entries:
        last_date = max(entry.date for entry in entries)
        # Sorted by (account, symbol), the order rustledger reports them in.
        for (account, symbol), pos in sorted(positions.items(), key=lambda kv: kv[0]):
            if pos.net == 0 or pos.expiry >= last_date:
                continue
            message = (
                f"{symbol} expired {pos.expiry.isoformat()} but {plain(pos.net)} "
                f"contract(s) remain open in {account}"
            )
            errors.append(OptionExpiryError(pos.opened_by.meta, message, pos.opened_by))
    return entries, errors
