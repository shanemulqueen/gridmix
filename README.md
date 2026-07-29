# GridMix — RGGI Emissions Data Pipeline

An end-to-end pipeline that pulls, cleans, cross-validates, and forecasts power-plant
CO₂ emissions and generation for the RGGI carbon market and surrounding states. It joins
two authoritative sources — **EPA CAMD CEMS** (unit-level, measured stack emissions) and
**EIA facility-fuel** (plant-level, self-reported fuel & generation) — and layers RGGI
regulatory obligation logic on top.

**Scope:** 16 states — RGGI-10 (CT, DE, MA, MD, ME, NH, NJ, NY, RI, VT) plus PA, VA, OH,
WV, DC, NC. Quarterly grain, 2020–2025 actuals, extended through 2026Q4.

For the dataset index, column references, and processing diagram, see
[`data/README.md`](data/README.md).

## Functional areas

### 1. Data acquisition (`fetch_*` scripts)

- **`scripts/fetch_cems_quarterly.py`** — pulls unit × quarter emissions from the EPA CAMD
  API (gross load, CO₂, SO₂, NOₓ, heat input, fuel/unit type). Handles pipe-delimited
  multi-value params and pagination. Keys read from env (`CAMD_API_KEY`) — never committed.
- **`scripts/fetch_eia_facility_fuel_all.py`** — pulls monthly generation & fuel consumption
  at plant × fuel × prime-mover granularity for all 445 CEMS plants (`EIA_API_KEY`).
- **`scripts/fetch_eia_capacity.py`** — pulls nameplate/summer/winter capacity per generator,
  monthly, for capacity-factor calculation.
- **`scripts/fetch_eia_generation.py`** — earlier EIA generation pull plus the COATS RGGI
  facility roster parser.

### 2. RGGI obligation modeling

- **`scripts/build_unit_crosswalk.py`** — reconciles COATS unit IDs against CEMS unit IDs
  per ORIS plant; classifies matched / COATS-only / CEMS-only.
- **`scripts/build_regime_flags.py`** — the regulatory engine. Encodes six historical
  obligation regimes and exports `regime_for(year, quarter)`, which auto-selects the correct
  obligation column for any period. Captures the real timeline: VA in 2021Q1–2023Q4 and
  rejoining 2026Q3 (HB 29); PA tracked 2022Q3–2023Q4 but court-voided → never obligated;
  NY's lower 15 MWe threshold.
- **`scripts/build_cems_clean.py`** — applies obligation flags per unit-quarter
  (`rggi_obligated`, `camd_rggi_program`, COATS match flags) using that regime logic.

### 3. Coverage & capacity analysis

- **`scripts/build_covered_table.py`** — aggregates CEMS to plant-quarter, auto-picks the
  right regime flag, splits covered vs non-covered CO₂ and generation, and computes
  gross-basis capacity factor against EIA nameplate (leap-year aware).

### 4. Cross-validation

- **`scripts/check_cems_vs_eia.py`** — reconciles CEMS vs EIA quarterly gross MWh for 410
  shared plants (EIA +2.86% aggregate; divergence traced to biomass/CHP/sub-threshold units).
- **`scripts/estimate_emissions_eia.py`** — estimates CO₂ from EIA fuel consumption × EPA
  40 CFR Part 98 factors, then validates against CEMS actuals (−3.64% aggregate; documents
  the systematic CHP underestimate and biogenic-CO₂ handling).

### 5. Forecast / gap-fill

- **`scripts/build_yoy_extension.py`** — the headline product. Computes plant-level monthly
  YoY% change in fossil generation from EIA, forecasts forward with a 3-year seasonal average,
  winsorizes and floors on a min-base guard, then applies those quarterly YoY factors to
  unit-level CEMS actuals to extend the measured series through 2026Q4 (holding emission
  intensity constant).

### 6. Documentation

- **`data/README.md`** — dataset index, pipeline diagram, script→output map, caveats.
- **14 `data/*_columns.md`** — per-file column references (types, units, row counts,
  methodology, validation stats).

## Data products (in `data/`)

The clean CEMS series, unit crosswalk, regime flag matrix, covered/non-covered state-quarter
summary, EIA facility-fuel & capacity tables, two CEMS↔EIA validation tables, the plant YoY
table, and the YoY-extended CEMS series (`cems_extended_quarterly.csv`) — the primary
analysis dataset when you need coverage past 2025Q4.

## Configuration

API keys are read from environment variables and are never committed to the repository:

- `CAMD_API_KEY` — EPA CAMD (data.gov) key for CEMS
- `EIA_API_KEY` — EIA API v2 key
