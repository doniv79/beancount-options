"""Shared helpers: load a ledger through beancount with a plugin enabled."""

import textwrap

from beancount import loader

HEADER = """\
2026-01-01 open Assets:Broker:Options
2026-01-01 open Assets:Broker:Cash
2026-01-01 open Assets:IRA:Options
2026-01-01 open Expenses:Fees
"""


def load(plugin, body):
    """Load ``body`` after the standard opens, with ``plugin`` enabled.

    Returns (errors from the plugin, every other error, entries).
    """
    text = f'plugin "beancount_options.{plugin}"\n\n{HEADER}\n{textwrap.dedent(body)}'
    entries, errors, _ = loader.load_string(text)
    ours = [e for e in errors if type(e).__module__.startswith("beancount_options")]
    others = [e for e in errors if e not in ours]
    return ours, others, entries


def leg(date, units, symbol, account="Assets:Broker:Options"):
    """One option leg against cash, at a price so the transaction balances."""
    cash = -int(units) * 100
    return f"""
{date} * "option leg"
  {account}  {units} {symbol} @ 100 USD
  Assets:Broker:Cash  {cash} USD
"""


def later(date):
    """A transaction with no option postings, moving the last date forward."""
    return f"""
{date} * "unrelated"
  Assets:Broker:Cash  -1.00 USD
  Expenses:Fees  1.00 USD
"""
