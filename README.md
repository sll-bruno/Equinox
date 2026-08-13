# Equinox
Funding Regime Engine

Reproduce the current Bybit BTCUSDT pilot (Python 3.11+):

```bash
python -m pytest
python -m src.validate_data
python -m src.run_baselines
python -m src.run_margin
python -m src.run_dead_zone
python -m src.run_rally_margin
```

The versioned scenario tables live in `reports/`; detailed Parquet ledgers are
reproducible local outputs and are intentionally ignored by Git.

The original 2026 pilot and the 2023-24 rally stress window are analyzed
separately; they are never silently joined into one backtest.
