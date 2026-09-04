# Data provenance — bundled Slovenian series

Both files under `data/` are public open data, retrieved **2026-09-04** for the RURALCAST
pre-submission feasibility back-test (SMART ERA 2nd Open Call). Nothing here is farm-level
or personal data.

---

## 1 · `data/SI_wheat_weekly_LJ.csv`

| Field | Value |
|---|---|
| Source | DG AGRI Agri-food Data Portal, agrifood API |
| Endpoint | `https://api.tech.ec.europa.eu/agrifood/api/cereal/prices` |
| Query parameters | `memberStateCodes=SI`, `years=` each of 2015…2026 (one request per year) |
| Series selected | `productName = "BLTPAN|PAN"` (breadmaking common wheat), `marketName = "Ljubljana"` |
| Geographic coverage | Slovenia, Ljubljana market quotation |
| Native frequency | **weekly** (`beginDate`/`endDate` week window) |
| Period retrieved | 2015-11-16 → 2026-08-24 |
| Rows after transformation | 559 |
| Unit | EUR / tonne |
| Licence / reuse | European Commission open data, free reuse with attribution |
| Retrieval date | 2026-09-04 |
| md5 | `2bce7e684cbe71174ed1e28b28cf2ea1` |
| sha256 | `8fdc1960c1179d10564ad49b123367dec78e12dd92d1485df94062bbab25ce7b` |

**Transformation log**
1. One GET per year; HTTP 404 from this API means "no data for these parameters" and is skipped, not treated as an error.
2. Filtered to the single product/market pair above.
3. `price` parsed from EU-formatted strings (`"€221,46"` → `221.46`: strip `€`, drop `.` thousands separator, `,` → `.`).
4. `beginDate` `dd/mm/yyyy` → ISO `yyyy-mm-dd`.
5. Where a week carried several price-stage variants, the week's value is their **arithmetic mean** (one observation per week).
6. Sorted ascending by date. **No gap filling, no interpolation, no resampling.**

**Known missingness** — 4 gaps in 11 years, all year-end holiday weeks:
2018-12-24 → 2019-01-07 · 2019-12-09 → 2019-12-23 · 2020-12-28 → 2021-01-11 · 2023-12-25 → 2024-01-08.
These are reported by `missingness_audit()` and asserted in the test suite; they are never filled.

Reproduce with `ruralcast-market-adapters`:
```
python -m ruralcast_adapters.dgagri --years 2015 2016 2017 2018 2019 2020 2021 2022 2023 2024 2025 2026 -o si_weekly.csv
```

---

## 2 · `data/SI_SURS_0410811S_monthly_indices.csv`

| Field | Value |
|---|---|
| Source | SURS (Statistical Office of the Republic of Slovenia), SiStat |
| Endpoint | `https://pxweb.stat.si/SiStatData/api/v1/en/Data/0410811S.px` (pxweb, POST) |
| Matrix | **0410811S** — Producer price indices of agricultural products |
| Query | variable `KMETIJSKI PRIDELEK` = `41000`, `61000`, `61100`, `70000`; variable `MERITVE` = `2`; response format `json` |
| Product definitions | `41000` Fresh vegetables · `61000` Fresh fruit (excl. grapes) · `61100` Dessert apples · `70000` Wine |
| Geographic coverage | Slovenia, national |
| Native frequency | **monthly** |
| Period retrieved | 2015M01 → 2026M06 (138 months, no gaps) |
| Unit | Index, **month / average of the year 2020 = 100** — an index, not a price level |
| Licence / reuse | SURS open data, CC BY 4.0 |
| Retrieval date | 2026-09-04 |
| md5 | `6d82e2b805a589e8f4f0b118b96d3f95` |
| sha256 | `a6e5581722245e0ddc59866ceb08c7ccb0d82f374ef9890fb5ab95d048ad851f` |

**Transformation log**
1. Single POST with the query above; response read as pxweb `json`, BOM stripped.
2. Missing-value markers (`..`, `.`, `-`, empty) are skipped, never imputed. None occurred in this extract.
3. Pivoted from long (`key = [product, month, measure]`) to wide: one row per month, one column per product code.
4. Sorted ascending by month. **No gap filling, no interpolation, no seasonal adjustment.**

Reproduce with `ruralcast-market-adapters`:
```
python -m ruralcast_adapters.surs --products 41000 61000 61100 70000 -o surs_monthly.csv
```
(The adapter emits long format with provenance columns; the wide layout bundled here is the
pivot described above.)

---

## Boundaries an evaluator should read with these files

- Both are **national / representative-market series**, not Goričko farm-gate prices. They
  demonstrate that the evaluation protocol runs on real Slovenian data with honest
  frequencies; they do not demonstrate product fit for any individual farm.
- The wheat series proves **weekly cadence and interval calibration**. Cereals are marginal
  to the target producer mix; the product-relevant results are the monthly indices.
- Per-series acceptance for the pilot happens at the M1 source gate (lawful reuse, stable
  identifiers, documented update route, ≥36 monthly or ≥52 weekly observations).
