# `eia_generator_attributes.csv` — Column Reference

**1,008 rows | latest snapshot per generator | 12 states (COATS facilities only)**

Source: `scripts/fetch_eia_generation.py`, `electricity/operating-generator-capacity` endpoint.
This was the original generator attributes pull, scoped to the 266 RGGI COATS facilities
(12 states). **Does not include nameplate capacity values** — that pull was made separately.
See `eia_generator_capacity_latest.csv` for the full 16-state pull with capacity MW.

One row per generator (most-recent period snapshot, deduplicated by plantid + generatorid).

---

## Columns

| Column | Type | Description |
|---|---|---|
| `period` | str | Most recent month this snapshot was pulled, `YYYY-MM` |
| `stateid` | str | Two-letter state code |
| `stateName` | str | Full state name |
| `sector` | str | EIA sector code (e.g. `ipp-non-chp`, `electric-utility`) |
| `sectorName` | str | Human-readable sector label |
| `entityid` | str | EIA entity/owner ID |
| `entityName` | str | Owner/operator name |
| `plantid` | str | EIA plant code (= ORIS = CAMD `facilityId`) |
| `plantName` | str | Plant name |
| `generatorid` | str | EIA generator ID |
| `technology` | str | Technology description (e.g. "Natural Gas Fired Combined Cycle") |
| `energy_source_code` | str | Primary fuel code (EIA-923 fuel code; see `eia_facility_fuel_monthly_all_columns.md`) |
| `energy-source-desc` | str | Fuel description |
| `prime_mover_code` | str | Prime mover code (ST/GT/CT/CA/CS/IC/etc.) |
| `balancing_authority_code` | str | ISO/RTO/BA code (e.g. `ISNE`, `PJM`, `NYIS`) |
| `balancing-authority-name` | str | Balancing authority full name |
| `status` | str | Operational status code (e.g. `OP` = Operating, `RE` = Retired) |
| `statusDescription` | str | Status description |
| `unit` | str | Unit label within a combined-cycle or multi-unit configuration |

## Notes

- Limited to COATS facilities (12 states: CT DE MA MD ME NH NJ NY PA RI VA VT). Missing OH, WV, NC, DC.
- No capacity MW values — use `eia_generator_capacity_latest.csv` for nameplate/summer/winter capacity.
- This file is primarily useful for technology type, balancing authority, and fuel code lookups.
