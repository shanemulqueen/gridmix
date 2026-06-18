# `eia_emissions_estimated.csv` — Column Reference

**90,907 rows | 410 plants | plant × fuel × prime mover × month | 2020-01 to 2027-03**

Source: `scripts/estimate_emissions_eia.py`. Applies EPA 40 CFR Part 98 Table C-1
default CO₂ emission factors to EIA monthly fuel consumption to produce plant-level
estimated CO₂ emissions. Covers actual EIA periods plus a 12-month seasonal forecast.

**Important limitation:** EIA facility-fuel is at plant level, not unit level. This file
cannot replicate CEMS unit-level granularity but is suitable for plant-level covered/
not-covered analysis.

---

## Columns

| Column | Type | Unit | Description |
|---|---|---|---|
| `period` | str | — | Calendar month, `YYYY-MM` |
| `plantCode` | str | — | EIA plant code (= EPA ORIS = CAMD `facilityId`) |
| `plantName` | str | — | Plant name |
| `state` | str | — | Two-letter state code |
| `fuel2002` | str | — | EIA-923 fuel code (see `eia_facility_fuel_monthly_all_columns.md` for reference) |
| `primeMover` | str | — | Prime mover code |
| `year` | int | — | Calendar year |
| `quarter` | int | — | Calendar quarter (1–4) |
| `consumption-for-eg-btu` | float | MMBtu | Fuel consumed for electricity generation (excludes thermal/steam sales at CHP plants) |
| `gross-generation` | float | MWh | Gross generation for this fuel/prime-mover row |
| `generation` | float | MWh | Net generation |
| `co2_factor_lb_per_mmbtu` | float | lb CO₂/MMBtu | EPA 40 CFR Part 98 default emission factor applied; 0 for biogenic/renewable fuels |
| `estimated_co2_tons` | float | short tons | `consumption-for-eg-btu × co2_factor_lb_per_mmbtu / 2000`; null where factor is null |
| `source` | str | — | Data provenance (see below) |

## Source values

| Value | Periods | Description |
|---|---|---|
| `eia_actual` | 2020-01 to 2025-12 | EIA actual fuel consumption data within CEMS window |
| `eia_gap_fill` | 2026-01 to 2026-03 | EIA actual data for months after CEMS dataset ends |
| `forecast` | 2026-04 to 2027-03 | 3-year seasonal average (2023–2025) applied to EIA patterns |

## Validation findings

Compared against CEMS actuals for 2020–2025 (see `eia_vs_cems_co2_validation.csv`):
- **Aggregate:** EIA estimated CO₂ is **−3.64%** below CEMS actual.
- **Reliable states** (error < 3%): CT, RI, WV, OH, NC — simple fossil power plants.
- **Systematic underestimate** in CHP-heavy states (NJ −8%, NY −11%, VA −7%): `consumption-for-eg-btu` excludes fuel allocated to thermal/steam sales, while CEMS measures total stack CO₂.
- **VT anomaly**: CEMS captures biogenic CO₂ from J.C. McNeil (biomass); EIA factor correctly uses 0 for WDS per RGGI accounting.

## Emission factors (EPA 40 CFR Part 98 Table C-1, selected)

| Fuel | Factor (lb CO₂/MMBtu) |
|---|---|
| Natural Gas (NG) | 117.0 |
| Distillate Fuel Oil (DFO) | 163.1 |
| Residual Fuel Oil (RFO) | 173.7 |
| Bituminous Coal (BIT) | 205.7 |
| Subbituminous Coal (SUB) | 213.0 |
| Petroleum Coke (PC) | 225.1 |
| Biomass/renewable fuels | 0.0 |
