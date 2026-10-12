"""Error on option contracts still open after their expiry date.

Option contracts are recognized by their OCC symbol (see ``_occ``). Every
other commodity is ignored.

"Today" is the date of the last entry in the ledger, not the system clock,
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
        # The entry that last opened the position from flat.
        self.opened_by = opened_by


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
        for posting in entry.postings:
            units = posting.units
            if units is None or not isinstance(units.number, Decimal):
                continue
            occ = parse_occ(units.currency)
            if occ is None:
                continue
            key = (posting.account, units.currency)
            pos = positions.get(key)
            if pos is None:
                pos = positions[key] = _Position(occ.expiry, entry)
            if pos.net == 0:
                pos.opened_by = entry
            pos.net += units.number

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
