# `eia_facility_fuel_monthly_all.csv` — Column Reference

**77,407 rows | 410 plants | 15 states (CT DE MA MD ME NC NH NJ NY OH PA RI VA VT WV) | 2020-01 to 2026-03**

Each row represents one plant × fuel type × prime mover × calendar month. ALL-rollup rows have been excluded; summing within a plant-month gives plant totals.

Source: EIA API v2 `electricity/facility-fuel` endpoint, fetched via `scripts/fetch_eia_facility_fuel_all.py`. Plant IDs sourced from `cems_quarterly_raw_2020_2025.csv` (all 445 CEMS plants across 16 states; 35 plants returned no EIA data — see fetch script for detail). DC has no EIA-reporting plants; its facilities report under MD/VA in EIA's system.

---

## Identity columns

| Column | Type | Description |
|---|---|---|
| `period` | str | Calendar month, `YYYY-MM` format |
| `plantCode` | str | EIA plant code (equals EPA ORIS / CAMD `facilityId`) |
| `plantName` | str | EIA plant name |
| `state` | str | Two-letter state code |
| `fuel2002` | str | EIA-923 fuel code (see reference below) |
| `fuelTypeDescription` | str | Human-readable fuel label |
| `primeMover` | str | Prime mover code (see reference below) |

## Generation columns

| Column | Unit | Description |
|---|---|---|
| `generation` | MWh | **Net** generation (after station service / auxiliary loads) |
| `gross-generation` | MWh | **Gross** generation at generator terminals; matches EPA CEMS `grossLoad` basis |

## Fuel consumption columns

| Column | Unit | Description |
|---|---|---|
| `total-consumption-btu` | MMBtu | All fuel consumed at the unit (including for heat/steam sales at CHP plants) |
| `consumption-for-eg-btu` | MMBtu | Fuel consumed **for electricity generation only**; use this for emission factor calculations to avoid over-counting CHP thermal output |
| `average-heat-content` | MMBtu/unit | Fuel-specific heat content; denominator varies by fuel (see `average-heat-content-units`) |
| `average-heat-content-units` | str | Denominator for heat content: `MMBtu per Mcf` (gas), `MMBtu per barrels` (liquid), `MMBtu per short tons` (solid), `MMBtu per megawatthours` (storage/electricity). Null for 2,025 rows where EIA does not report heat content (solar, hydro, battery, some waste streams). |

---

## Fuel codes (`fuel2002`)

### Fossil — Gas
| Code | Description |
|---|---|
| `NG` | Natural Gas |
| `OG` | Other Gases |
| `BFG` | Blast Furnace Gas |
| `PG` | Gaseous Petroleum Products |

### Fossil — Liquid
| Code | Description |
|---|---|
| `DFO` | Distillate Fuel Oil (diesel / No. 2) |
| `RFO` | Residual Fuel Oil (heavy oil / No. 6) |
| `KER` | Kerosene / Jet Fuel |
| `JF` | Waste Oils and Other Oils |
| `WO` | Waste Oil |

### Fossil — Solid
| Code | Description |
|---|---|
| `BIT` | Bituminous Coal |
| `SUB` | Subbituminous Coal |
| `RC` | Refined Coal |
| `PC` | Petroleum Coke |
| `WC` | Waste Coal |
| `ANT` | Anthracite Coal |
| `LIG` | Lignite Coal |
| `SC` | Synthetic Coal |

### Renewable / Biogenic
| Code | Description |
|---|---|
| `WDS` | Wood Waste Solids (biomass) |
| `BLQ` | Black Liquor (pulp/paper mill byproduct) |
| `OBS` | Other Biomass Solids |
| `OBL` | Other Biomass Liquids |
| `OBG` | Other Biomass Gas |
| `LFG` | Landfill Gas |
| `MSB` | Municipal Solid Waste — Biogenic |
| `WAT` | Water (hydroelectric) |
| `SUN` | Solar |
| `WND` | Wind |

### Other / Non-fossil
| Code | Description |
|---|---|
| `NUC` | Nuclear |
| `MSN` | Municipal Solid Waste — Non-biogenic |
| `TDF` | Tire-Derived Fuel |
| `SLW` | Sludge Waste |
| `MWH` | Electricity (storage charging / discharging) |
| `OTH` | Other |

---

## Prime mover codes (`primeMover`)

| Code | Description |
|---|---|
| `ST` | Steam turbine (coal, oil, nuclear, biomass boilers) |
| `GT` | Gas turbine (simple cycle) |
| `CT` | Combustion turbine (older EIA classification, functionally similar to GT) |
| `CA` | Combined-cycle steam turbine (heat recovery steam generator side) |
| `CS` | Combined-cycle single-shaft |
| `IC` | Internal combustion engine |
| `HY` | Hydraulic turbine |
| `PV` | Photovoltaic |
| `BA` | Battery storage |
| `WT` | Wind turbine |
| `OT` | Other |

---

## Cross-check vs EPA CEMS

A plant-quarter comparison against `cems_quarterly_clean_2020_2025.csv` (see `scripts/check_cems_vs_eia.py`, output in `cems_eia_generation_check.csv`) found:

- **Aggregate:** EIA gross generation is +2.86% above CEMS across all shared plant-quarters.
- **Median plant-quarter difference: 0.02%** — near-identical for most plants.
- **Sources of divergence (not measurement error):**
  1. Biomass/waste units (WDS, BLQ, etc.) report to EIA but are exempt from CEMS monitoring — largest example is Burgess BioPower (NH), ~2.7M MWh/year from wood waste.
  2. CHP steam-recovery turbines and small units below the CEMS monitoring threshold appear in EIA but not CEMS.
- States with <2% gap (reliable for either source): MD, OH, VA, WV, VT.
- States with persistent positive EIA bias: NH (~30%), CT (~10%), MA (~10–17%), RI (~13–18%).

For CO2 emission factor work: filter to fossil fuel codes and use `consumption-for-eg-btu` as the activity variable.
