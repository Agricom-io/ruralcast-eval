import csv, datetime, pathlib
from ruralcast_eval.backtest import rolling_backtest, metrics, missingness_audit

ROOT = pathlib.Path(__file__).resolve().parents[1]

def test_metrics_basics():
    m = metrics([10, 10], [12, 8], [11, 9])
    assert m["mae"] == 1.0 and m["mae_naive"] == 1.0 and m["n"] == 2

def test_reproduces_weekly_headline_numbers():
    rows = list(csv.DictReader(open(ROOT / "data/SI_wheat_weekly_LJ.csv")))
    y = [float(r["price_eur_t"]) for r in rows]
    ts = next(i for i, r in enumerate(rows) if r["date"] >= "2022-01-01")
    m = rolling_backtest(y, h=1, cal_n=52, test_start=ts, ar_p=4)
    assert abs(m["mape_pct"] - 3.46) < 0.05
    assert abs(m["coverage80_pct"] - 80.5) < 0.6

def test_reproduces_monthly_headline_numbers():
    rows = list(csv.DictReader(open(ROOT / "data/SI_SURS_0410811S_monthly_indices.csv")))
    y = [float(r["41000_fresh_vegetables"]) for r in rows]
    m = rolling_backtest(y, h=1, cal_n=24, test_start=72, ar_p=6, seasonal=12)
    assert abs(m["mape_pct"] - 6.83) < 0.05
    assert m["mae_ratio_vs_naive"] < 0.75

def test_missingness_audit_finds_holiday_gaps():
    rows = list(csv.DictReader(open(ROOT / "data/SI_wheat_weekly_LJ.csv")))
    dates = [datetime.date.fromisoformat(r["date"]) for r in rows]
    gaps = missingness_audit(dates, 7)
    assert len(gaps) == 4
