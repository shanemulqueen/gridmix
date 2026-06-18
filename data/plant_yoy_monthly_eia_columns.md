# `plant_yoy_monthly_eia.csv` — Column Reference

**29,496 rows | 410 plants | plant × month | 2020-01 to 2026-12**

Source: `scripts/build_yoy_extension.py`. Plant-level monthly year-over-year
percentage change in fossil/thermal gross generation, derived from EIA facility-fuel
data. The fossil filter excludes biomass, hydro, wind, solar, nuclear, and storage
to match the scope of CEMS monitoring.

Used as the intermediate input to `cems_extended_quarterly.csv` — the monthly YoY
values are aggregated to quarterly ratios and applied to CEMS unit-level actuals.

---

## Columns

| Column | Type | Unit | Description |
|---|---|---|---|
| `plantCode` | str | — | EIA plant code (= EPA ORIS = CAMD `facilityId`) |
| `state` | str | — | Two-letter state code |
| `period` | str | — | Calendar month, `YYYY-MM` |
| `year` | int | — | Calendar year |
| `month` | int | — | Calendar month (1–12) |
| `fossil_gross_mwh` | float | MWh | Plant gross generation from fossil fuels only (current month); null for forecast rows |
| `fossil_mmbtu` | float | MMBtu | Fossil fuel consumed for electricity generation (current month); null for forecast rows |
| `fossil_gross_mwh_py` | float | MWh | Same plant, same calendar month, prior year (prior-year comparison); null for forecast rows |
| `fossil_mmbtu_py` | float | MMBtu | Prior-year fuel consumption; null for forecast rows |
| `yoy_pct` | float | — | `(fossil_gross_mwh / fossil_gross_mwh_py) − 1`; null if prior year unavailable or zero |
| `source` | str | — | `eia_actual` (both years have EIA data) or `eia_forecast` (current year estimated from seasonal average) |

## Source values

| Value | Periods | Method |
|---|---|---|
| `eia_actual` | 2021-01 to 2026-03 | Direct ratio of EIA actuals; 2020 rows have no prior year, so `yoy_pct = null` |
| `eia_forecast` | 2026-04 to 2026-12 | Mean of same plant × calendar month `yoy_pct` from 2023, 2024, 2025; state-median fallback if plant history insufficient |

## Fossil fuel scope

Only fuel codes in the FOSSIL_FUELS set are included:
NG, OG, BFG, PG (gas); DFO, RFO, KER, JF, WO (liquid); BIT, SUB, RC, WC, PC, ANT, LIG, SC, TDF, MSN (solid).
Biomass (WDS, BLQ, OBS, OBL, OBG, LFG, MSB), hydro (WAT), solar (SUN), wind (WND), nuclear (NUC), and storage (MWH) are excluded.

## Robustness controls applied in quarterly aggregation

When rolling to quarterly YoY (for `cems_extended_quarterly.csv`):
- Plant-quarters where prior-year fossil generation < **10,000 MWh** are excluded from the plant-level ratio (unreliable base); those plants receive state-median fallback.
- Quarterly YoY values are **winsorised to [−75%, +100%]** before application to CEMS data.
