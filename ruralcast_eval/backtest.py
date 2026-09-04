"""Rolling-origin back-test with naive comparator and split-conformal intervals.

Reference model: AR(p) ordinary least squares on a trailing window. This is a
deliberately simple benchmark, not a production forecasting system; external
forecasters are evaluated by passing their own predictions through `metrics()`.
Missing periods are never filled - the audit reports them.
"""
import argparse, csv, math, sys

def rolling_backtest(y, h=1, cal_n=52, test_start=0, ar_p=4, seasonal=None, window=156):
    import numpy as np
    y = np.asarray(y, dtype=float)
    preds, naives, actuals, lo, hi = [], [], [], [], []
    resid_hist = []
    for t in range(test_start, len(y) - h + 1):
        train = y[:t]
        win = train[-window:] if len(train) > window else train
        p = ar_p
        X = np.array([win[i:i + p] for i in range(len(win) - p - h + 1)])
        Y = np.array([win[i + p + h - 1] for i in range(len(win) - p - h + 1)])
        A = np.hstack([X, np.ones((len(X), 1))])
        coef, *_ = np.linalg.lstsq(A, Y, rcond=None)
        f = float(np.append(train[-p:], 1.0) @ coef)
        nv = float(train[-seasonal]) if seasonal and len(train) >= seasonal else float(train[-1])
        a = float(y[t + h - 1])
        if len(resid_hist) >= cal_n:
            q = sorted(resid_hist[-cal_n:])[max(0, int(math.ceil(0.8 * (cal_n + 1))) - 1)]
            lo.append(f - q); hi.append(f + q)
        else:
            lo.append(None); hi.append(None)
        preds.append(f); naives.append(nv); actuals.append(a)
        resid_hist.append(abs(a - f))
    return metrics(preds, naives, actuals, lo, hi)

def metrics(preds, naives, actuals, lo=None, hi=None):
    import numpy as np
    P, N, A = map(np.asarray, (preds, naives, actuals))
    out = {
        "n": int(len(P)),
        "mae": float(np.mean(np.abs(P - A))),
        "mae_naive": float(np.mean(np.abs(N - A))),
        "mape_pct": float(np.mean(np.abs((P - A) / A))) * 100,
        "mape_naive_pct": float(np.mean(np.abs((N - A) / A))) * 100,
    }
    out["mae_ratio_vs_naive"] = out["mae"] / out["mae_naive"]
    if lo is not None:
        pairs = [(l, u, a) for l, u, a in zip(lo, hi, actuals) if l is not None]
        if pairs:
            out["coverage80_pct"] = 100 * sum(1 for l, u, a in pairs if l <= a <= u) / len(pairs)
            out["coverage_n"] = len(pairs)
            out["interval_width_mean"] = float(sum(u - l for l, u, a in pairs) / len(pairs))
    return out

def missingness_audit(dates, expected_step_days=7):
    gaps = []
    for a, b in zip(dates, dates[1:]):
        if (b - a).days > expected_step_days:
            gaps.append((a.isoformat(), b.isoformat()))
    return gaps

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("csv_path")
    ap.add_argument("--column", required=True)
    ap.add_argument("--date-column", default=None)
    ap.add_argument("--h", type=int, default=1)
    ap.add_argument("--cal", type=int, default=52)
    ap.add_argument("--ar", type=int, default=4)
    ap.add_argument("--seasonal", type=int, default=None)
    ap.add_argument("--test-from", default=None, help="ISO date; test starts at first row >= this date")
    ap.add_argument("--test-from-index", type=int, default=None)
    a = ap.parse_args(argv)
    rows = list(csv.DictReader(open(a.csv_path)))
    y = [float(r[a.column]) for r in rows]
    if a.test_from is not None:
        import datetime
        dc = a.date_column or list(rows[0].keys())[0]
        ts = next(i for i, r in enumerate(rows) if r[dc] >= a.test_from)
    else:
        ts = a.test_from_index or 0
    res = rolling_backtest(y, h=a.h, cal_n=a.cal, test_start=ts, ar_p=a.ar, seasonal=a.seasonal)
    import json
    print(json.dumps({k: round(v, 3) if isinstance(v, float) else v for k, v in res.items()}, indent=1))

if __name__ == "__main__":
    main()
