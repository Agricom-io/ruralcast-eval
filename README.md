# ruralcast-eval

Forecast-evaluation harness for **RURALCAST** — the protocol the pilot freezes at
On-boarding and reports against at its M5/M12 milestones (SMART ERA 2nd Open Call,
Followers Micro-Pilot; Goričko, Slovenia).

What it implements, exactly as stated in the application:

- **rolling-origin back-testing** (one forecast per step, expanding window),
- a **naïve comparator** (last value; optional seasonal-naïve),
- a built-in **reference model** (autoregressive least squares) — deliberately simple,
  NOT the AgriSyncAI engine: any forecasting system is evaluated against the same
  protocol by supplying its forecasts,
- **split-conformal prediction intervals** with empirical-coverage reporting,
- a **missingness audit** (gaps are reported, never filled).

## Reproduce the September 2026 Slovenian feasibility results

`data/` bundles two real public series fetched 2026-09-04 (SURS 0410811S monthly
indices, CC BY 4.0; DG AGRI Slovenian weekly market series, EU open data):

```
pip install numpy pytest
python -m ruralcast_eval.backtest data/SI_wheat_weekly_LJ.csv --column price_eur_t --h 1 --cal 52 --test-from 2022-01-01
python -m ruralcast_eval.backtest data/SI_SURS_0410811S_monthly_indices.csv --column 41000_fresh_vegetables --h 1 --cal 24 --test-from-index 72 --ar 6 --seasonal 12
```

Expected headline numbers (also asserted by the test suite): weekly h=1 MAPE ≈ 3.46%
with 80.5% empirical coverage of the 80% conformal interval; monthly fresh-vegetables
h=1 MAPE ≈ 6.83% vs 10.02% naïve.

## Tests

```
python -m pytest tests/
```

## Licence and governance

Apache 2.0 (see `LICENSE`). Docs CC BY 4.0.
Maintainer: Maria Abdallah (Agricom). Deputy: Jonas Westphal (Agricom).

*Planned under the SMART ERA project's 2nd Open Call. SMART ERA has received funding
from the European Union's Horizon Europe research and innovation programme.*
