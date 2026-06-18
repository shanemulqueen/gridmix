# `unit_regime_flags.csv` — Column Reference

**1,338 rows | one row per unique CEMS unit across all 16 states**

Source: `scripts/build_regime_flags.py`. Indexes every unit in the CEMS quarterly
dataset with a boolean obligation flag for each distinct RGGI regulatory regime.
Designed as the lookup table for automated regime selection in downstream analysis
(see `build_covered_table.py`).

---

## Identity columns

| Column | Type | Description |
|---|---|---|
| `oris` | str | EPA ORIS code (= EIA `plantCode` = CAMD `facilityId`) |
| `cems_unit` | str | CEMS unit ID (normalised: stripped, uppercased) |
| `coats_unit` | str | COATS unit label where a direct match was found; null otherwise (765 of 1,338 units mapped) |
| `state` | str | Two-letter state code |
| `facility_name` | str | Plant name from CEMS |
| `coats_linked` | bool | `True` if the unit is linked to RGGI COATS via any of: direct unit match, facility-level match, or CAMD RGGI program flag. This is the RGGI-linked indicator independent of regime/timing. |

---

## Regime obligation columns

Each column is `True` when `coats_linked = True` AND the unit's state participated
in RGGI during that regime window. A unit that is not COATS-linked is `False` in
all regime columns regardless of state.

| Column | Period | Participating states | Obligated units |
|---|---|---|---|
| `oblig_pre2009` | Before 2009 | None | 0 (RGGI did not exist) |
| `oblig_2020` | 2020Q1–2020Q4 | RGGI-10 | 618 |
| `oblig_2021q1_2022q2` | 2021Q1–2022Q2 | RGGI-10 + VA | 709 |
| `oblig_2022q3_2023q4` | 2022Q3–2023Q4 | RGGI-10 + VA + PA | 858 |
| `oblig_2024q1_2026q2` | 2024Q1–2026Q2 | RGGI-10 | 618 |
| `oblig_2026q3_on` | 2026Q3 onward | RGGI-10 + VA | 709 |

### Regime boundary notes

- **VA** joined 2021Q1, withdrew end of 2023Q4, rejoining with compliance obligations from July 1, 2026 (HB 29 / DEQ Revision A26, effective 2026-04-24). Jan–Jun 2026 VA generation carries no obligation.
- **PA** had regulation effective 2022Q3 but allowance surrender was never enforced before courts voided participation. Emissions are tracked in COATS and match RGGI's official PA totals, so the flag reflects the tracked window.
- **RGGI-10** (NJ rejoined 2020Q1): CT DE MA MD ME NH NJ NY RI VT — obligated throughout the full dataset window.

## Helper function

`build_regime_flags.py` also exports `regime_for(year, quarter)` which returns the
applicable column name for a given observation period. Used in `build_covered_table.py`
to auto-select the correct flag without hardcoding period logic in analysis scripts.
