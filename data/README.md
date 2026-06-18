# RGGI Emissions Data Pipeline — Dataset Reference

This directory contains the output datasets from the RGGI emissions data pipeline covering
EPA CAMD CEMS unit-level data (2020–2025), EIA plant-level data (2020–2026), and derived
analysis products including emissions estimates, cross-validation, and a YoY-extended CEMS
series through 2026Q4.

**State scope:** CT, DE, MA, MD, ME, NH, NJ, NY, RI, VT (RGGI-10) plus PA, VA, OH, WV, DC, NC

---

## Dataset Index

### CEMS Core

| File | Rows | Grain | Description |
|---|---|---|---|
| [`cems_quarterly_raw_2020_2025.csv`](cems_quarterly_raw_columns.md) | ~130,000 | unit × quarter | Raw quarterly CEMS pull from EPA CAMD API, 2020–2025, 16 states |
| [`cems_quarterly_clean_2020_2025.csv`](cems_quarterly_clean_columns.md) | ~130,000 | unit × quarter | Cleaned CEMS with RGGI obligation flags (`rggi_obligated`, `camd_rggi_program`, COATS match flags) |
| [`cems_extended_quarterly.csv`](cems_extended_quarterly_columns.md) | 32,174 | unit × quarter | CEMS actuals (2020–2025) stacked with YoY-extended estimates for 2026Q1–Q4 |

### RGGI Obligation Crosswalk

| File | Rows | Grain | Description |
|---|---|---|---|
| [`unit_crosswalk.csv`](unit_crosswalk_columns.md) | 836 | ORIS × unit pair | COATS-to-CEMS unit ID crosswalk; classifies matched / coats_only / cems_only |
| [`unit_regime_flags.csv`](unit_regime_flags_columns.md) | 1,338 | unit | Per-unit boolean flags for each RGGI obligation regime (pre-2009 through 2026Q3+) |

### Coverage & Emissions Summary

| File | Rows | Grain | Description |
|---|---|---|---|
| [`state_quarter_covered_summary.csv`](state_quarter_covered_summary_columns.md) | 954 | state × quarter | Covered vs non-covered generation, CO₂, and capacity factor by state-quarter |
| [`va_co2_by_quarter_groups.csv`](va_co2_by_quarter_groups_columns.md) | — | state × obligation period | Virginia CO₂ aggregated by RGGI obligation status groups |

### EIA Capacity

| File | Rows | Grain | Description |
|---|---|---|---|
| [`eia_generator_attributes.csv`](eia_generator_attributes_columns.md) | — | generator | EIA generator attributes (fuel type, prime mover, online/retire dates) |
| [`eia_plant_capacity_monthly.csv`](eia_plant_capacity_monthly_columns.md) | 28,654 | plant × month | Monthly nameplate/summer/winter capacity by plant, used for capacity factor calculation |
| [`eia_generator_capacity_latest.csv`](eia_generator_capacity_latest_columns.md) | 1,434 | generator | Most recent capacity snapshot per generator |

### EIA Facility-Fuel (Generation & Fuel Consumption)

| File | Rows | Grain | Description |
|---|---|---|---|
| [`eia_facility_fuel_monthly_all.csv`](eia_facility_fuel_monthly_all_columns.md) | 77,407 | plant × fuel × prime mover × month | Monthly EIA generation and fuel consumption at plant-fuel-primemover level, 2020-01 to 2026-03 |

### Validation & Cross-Checks

| File | Rows | Grain | Description |
|---|---|---|---|
| [`cems_eia_generation_check.csv`](cems_eia_generation_check_columns.md) | 8,074 | plant × quarter | CEMS vs EIA quarterly gross MWh comparison for 410 shared plants (EIA +2.86% aggregate) |
| [`eia_emissions_estimated.csv`](eia_emissions_estimated_columns.md) | 90,907 | plant × fuel × prime mover × month | CO₂ estimated from EIA fuel consumption × EPA 40 CFR Part 98 emission factors |
| [`eia_vs_cems_co2_validation.csv`](eia_vs_cems_co2_validation_columns.md) | 7,127 | plant × quarter | EIA-estimated vs CEMS-actual CO₂ comparison for 2020–2025 (EIA −3.64% aggregate) |

### YoY Extension Inputs

| File | Rows | Grain | Description |
|---|---|---|---|
| [`plant_yoy_monthly_eia.csv`](plant_yoy_monthly_eia_columns.md) | 29,496 | plant × month | Plant-level monthly YoY% in fossil/thermal generation (EIA actuals 2021–2026-03; seasonal forecast 2026-04+) |

---

## Processing Pipeline

```
EPA CAMD API  ──►  cems_quarterly_raw  ──►  cems_quarterly_clean
                                                    │
EIA API  ──►  eia_facility_fuel_monthly_all  ──►  plant_yoy_monthly_eia
                          │                              │
                          ▼                              ▼
              eia_emissions_estimated         cems_extended_quarterly
                          │
                          ▼
              eia_vs_cems_co2_validation

EIA API  ──►  eia_plant_capacity_monthly  ──►  state_quarter_covered_summary
                                                  (via cems_quarterly_clean)

COATS sources_raw.xlsx  ──►  unit_crosswalk  ──►  unit_regime_flags
                                                        │
                                               (feeds rggi_obligated
                                                in cems_quarterly_clean)
```

## Scripts

| Script | Produces |
|---|---|
| `scripts/fetch_cems_quarterly.py` | `cems_quarterly_raw_2020_2025.csv` |
| `scripts/build_cems_clean.py` | `cems_quarterly_clean_2020_2025.csv` |
| `scripts/build_unit_crosswalk.py` | `unit_crosswalk.csv` |
| `scripts/build_regime_flags.py` | `unit_regime_flags.csv` |
| `scripts/fetch_eia_capacity.py` | `eia_plant_capacity_monthly.csv`, `eia_generator_capacity_latest.csv` |
| `scripts/build_covered_table.py` | `state_quarter_covered_summary.csv` |
| `scripts/fetch_eia_facility_fuel_all.py` | `eia_facility_fuel_monthly_all.csv` |
| `scripts/check_cems_vs_eia.py` | `cems_eia_generation_check.csv` |
| `scripts/estimate_emissions_eia.py` | `eia_emissions_estimated.csv`, `eia_vs_cems_co2_validation.csv` |
| `scripts/build_yoy_extension.py` | `plant_yoy_monthly_eia.csv`, `cems_extended_quarterly.csv` |

## Key Caveats

- **RGGI obligation (`rggi_obligated`)**: derived from COATS unit roster + CAMD program flag, subject to per-period state rules. VA obligated 2021Q1–2023Q4 and from 2026Q3 onward (HB 29 / DEQ Revision A26). PA tracked 2022Q3–2023Q4 but courts voided enforcement; always `False`.
- **CHP underestimate**: EIA `consumption-for-eg-btu` excludes fuel for thermal/steam sales; EIA-estimated CO₂ is systematically low for CHP-heavy states (NJ −8%, NY −11%, VA −7%).
- **Biogenic CO₂**: CEMS reports actual stack CO₂ including biogenic (biomass). EIA factor method uses 0 for biogenic fuels per RGGI accounting. VT shows extreme discrepancy from this cause.
- **2026 extended values**: `cems_extended` rows are estimates. Uncertainty grows further from the 2025 base; treat as indicative.
