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


# Every per-series figure quoted in the RURALCAST application, asserted here so a
# reader can re-run the harness and reproduce each one. Added 2026-09-05.
MONTHLY_EXPECTED = {
    # column                    mape   mae_ratio_vs_naive  coverage80
    "41000_fresh_vegetables": (6.83,  0.688, 78.6),
    "61000_fresh_fruit":      (9.90,  0.746, 85.7),
    "61100_dessert_apples":   (11.60, 0.724, 85.7),
    "70000_wine":             (7.38,  0.917, 88.1),
}

def test_reproduces_every_quoted_monthly_series():
    rows = list(csv.DictReader(open(ROOT / "data/SI_SURS_0410811S_monthly_indices.csv")))
    for col, (mape, ratio, cov) in MONTHLY_EXPECTED.items():
        y = [float(r[col]) for r in rows]
        m = rolling_backtest(y, h=1, cal_n=24, test_start=72, ar_p=6, seasonal=12)
        assert m["n"] == 66, col
        assert abs(m["mape_pct"] - mape) < 0.05, (col, m["mape_pct"])
        assert abs(m["mae_ratio_vs_naive"] - ratio) < 0.002, (col, m["mae_ratio_vs_naive"])
        assert abs(m["coverage80_pct"] - cov) < 0.6, (col, m["coverage80_pct"])

def test_beat_naive_percentages_as_published():
    """The application states 31% fresh vegetables, 28% dessert apples, 25% fresh
    fruit and 8% wine. Each is 100*(1 - mae_ratio_vs_naive), rounded."""
    rows = list(csv.DictReader(open(ROOT / "data/SI_SURS_0410811S_monthly_indices.csv")))
    published = {"41000_fresh_vegetables": 31, "61100_dessert_apples": 28,
                 "61000_fresh_fruit": 25, "70000_wine": 8}
    for col, pct in published.items():
        y = [float(r[col]) for r in rows]
        m = rolling_backtest(y, h=1, cal_n=24, test_start=72, ar_p=6, seasonal=12)
        assert round(100 * (1 - m["mae_ratio_vs_naive"])) == pct, (col, m["mae_ratio_vs_naive"])

def test_coverage_band_as_published():
    """The application states empirical 80% coverage of 78.6-88.1% across series."""
    rows = list(csv.DictReader(open(ROOT / "data/SI_SURS_0410811S_monthly_indices.csv")))
    covs = []
    for col in MONTHLY_EXPECTED:
        y = [float(r[col]) for r in rows]
        covs.append(rolling_backtest(y, h=1, cal_n=24, test_start=72, ar_p=6, seasonal=12)["coverage80_pct"])
    wrows = list(csv.DictReader(open(ROOT / "data/SI_wheat_weekly_LJ.csv")))
    wy = [float(r["price_eur_t"]) for r in wrows]
    wts = next(i for i, r in enumerate(wrows) if r["date"] >= "2022-01-01")
    covs.append(rolling_backtest(wy, h=1, cal_n=52, test_start=wts, ar_p=4)["coverage80_pct"])
    assert abs(min(covs) - 78.6) < 0.6 and abs(max(covs) - 88.1) < 0.6, covs
