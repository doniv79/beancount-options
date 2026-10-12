# beancount-options

Beancount plugins that check option contracts written in a Beancount ledger:

- `check_option_expiry`: reports a contract that still has open units after it expires.
- `check_option_assignment`: checks an assigned short option (shares per contract, no gain on the option leg, and the stock's basis or proceeds of strike ∓ premium).

The plugins only check and report. They never generate entries.

These are the Python counterparts of native plugins in [rustledger](https://github.com/rustledger/rustledger). The same `plugin` line runs this package under `bean-check` and Fava, and rustledger's native implementation under `rledger`:

```beancount
plugin "beancount_options.check_option_expiry"
plugin "beancount_options.check_option_assignment"
```

rustledger's CI runs both implementations on the same ledgers and requires identical results.

Status: being designed in [rustledger#2555](https://github.com/rustledger/rustledger/issues/2555).

## License

GPL-2.0-or-later. See [LICENSE](LICENSE). This package imports Beancount, which is GPL-2.0-only, so it is not licensed under GPL-3.0-only like rustledger.
