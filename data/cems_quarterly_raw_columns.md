# `cems_quarterly_raw_2020_2025.csv` — Column Reference

**27,860 rows | 1,338 unique units | 16 states | 2020Q1–2025Q4**

Source: EPA CAMD Emissions Management API (`emissions/apportioned/quarterly`).
Fetched by `scripts/fetch_cems_quarterly.py`. One row per unit × quarter.
States: CT DE MA MD ME NH NJ NY RI VT (RGGI-10) + PA VA OH WV DC NC (surrounding).

---

## Identity columns

| Column | Type | Description |
|---|---|---|
| `stateCode` | str | Two-letter state code |
| `facilityName` | str | Plant name as registered in CAMD |
| `facilityId` | int | EPA ORIS code (= EIA `plantCode`) |
| `unitId` | str | CEMS unit identifier (monitoring plan unit) |
| `unit_id` | str | Alternate unit ID field returned by API (duplicate of `unitId`; dropped in clean version) |
| `associatedStacks` | str | Stack IDs associated with this unit (often null) |
| `year` | int | Calendar year |
| `quarter` | int | Calendar quarter (1–4) |

## Operating time columns

| Column | Unit | Description |
|---|---|---|
| `countOpTime` | hours | Count of operating hours reported |
| `sumOpTime` | hours | Sum of operating hours (may differ from count if fractional) |

## Generation columns

| Column | Unit | Description |
|---|---|---|
| `grossLoad` | MWh | Gross generation at generator terminals (before station service) |
| `steamLoad` | klb | Steam output (CHP units only; null for electric-only units) |

## Emissions columns

| Column | Unit | Description |
|---|---|---|
| `so2Mass` | short tons | SO₂ emissions |
| `so2Rate` | lb/MMBtu | SO₂ emission rate |
| `co2Mass` | short tons | CO₂ emissions (actual stack measurement; includes biogenic CO₂ from biomass units) |
| `co2Rate` | short tons/MWh | CO₂ rate |
| `noxMass` | short tons | NOₓ emissions |
| `noxRate` | lb/MMBtu | NOₓ emission rate |
| `heatInput` | MMBtu | Fuel heat input |

## Fuel and unit type columns

| Column | Description |
|---|---|
| `primaryFuelInfo` | Primary fuel type (text description, e.g. "Natural Gas", "Coal", "Other Oil") |
| `secondaryFuelInfo` | Secondary fuel if co-fired (often null) |
| `unitType` | Unit technology type (e.g. "Combined cycle", "Combustion turbine", "Boiler") |

## Control and program columns

| Column | Description |
|---|---|
| `so2ControlInfo` | SO₂ control technology installed (e.g. "Scrubber") |
| `noxControlInfo` | NOₓ control technology |
| `pmControlInfo` | Particulate matter control |
| `hgControlInfo` | Mercury control |
| `programCodeInfo` | Comma-separated list of regulatory programs the unit participates in (e.g. "RGGI,ARP,CAIR") |

## Notes

- CO₂ mass is the raw CEMS stack measurement and includes biogenic CO₂ from biomass-fired units (e.g. J.C. McNeil, VT). For RGGI compliance accounting, biogenic CO₂ is excluded.
- Null `co2Mass` typically indicates the unit is not required to monitor CO₂ (e.g. very small units or non-CO₂ monitored pollutants only).
- `facilityId` is the authoritative join key to EIA (`plantCode`) and RGGI COATS ORIS codes.
