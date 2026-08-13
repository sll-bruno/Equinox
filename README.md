# Equinox
Funding Regime Engine

Reproduce the current Bybit BTCUSDT pilot (Python 3.11+):

```bash
python -m pytest
python -m src.validate_data
python -m src.run_baselines
python -m src.run_margin
python -m src.run_dead_zone
```

The versioned scenario tables live in `reports/`; detailed Parquet ledgers are
reproducible local outputs and are intentionally ignored by Git.
