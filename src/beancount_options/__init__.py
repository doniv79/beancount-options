# SPDX-License-Identifier: GPL-2.0-or-later
"""Beancount plugins that check option contracts written in a ledger.

Enable a plugin with its full module path, which rustledger also resolves to
its native implementation:

    plugin "beancount_options.check_option_expiry"
"""

__version__ = "0.1.0"
