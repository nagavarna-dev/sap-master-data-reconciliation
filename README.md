# SAP Master-Data Reconciliation

SQL-based reconciliation of SAP master data. Models the core tables
(**MARA, MAKT, MARC, KNA1**), compares a **source** extract against the
**migrated target**, flags missing records and value mismatches, scores
data quality across five dimensions, and renders an interactive dashboard —
no Power BI or Tableau install required.

Built around a real data-migration workflow: when you move master data
between systems, you need objective proof that what landed in the target
matches what left the source.

## Roadmap

- [x] **Phase 1** — SAP master-data schema (MARA, MAKT, MARC, KNA1) with keys
- [x] **Phase 2** — Sample target data loaded
- [x] **Phase 3** — Reconciliation SQL (missing records, value mismatches, row-count checks)
- [x] **Phase 4** — Data-quality scorecard (completeness, validity, uniqueness, referential integrity, consistency)
- [x] **Phase 5** — Interactive HTML dashboard over the SQL results

## Quick start

Requires Python 3 (uses the built-in `sqlite3` module — no pip installs).

```bash
python3 run_pipeline.py
```

This builds `recon.db` from the SQL scripts, prints a console summary, and
writes `dashboard/index.html`. Open that file in any browser to explore the
results.

Prefer raw SQL? Run the scripts in order against SQLite:

```bash
sqlite3 recon.db < sql/01_create_tables.sql
sqlite3 recon.db < sql/02_insert_data.sql
sqlite3 recon.db < sql/03_source_tables.sql
sqlite3 recon.db < sql/04_source_data.sql
sqlite3 recon.db < sql/05_reconciliation.sql
sqlite3 recon.db < sql/06_data_quality_scorecard.sql
```

## Project structure

```
sql/
  01_create_tables.sql          Target schema (MARA, MAKT, MARC, KNA1) + keys
  02_insert_data.sql            Target (migrated) sample data
  03_source_tables.sql          Staging tables for the source extract
  04_source_data.sql            Source sample data (with seeded defects)
  05_reconciliation.sql         Missing records, value mismatches, row counts
  06_data_quality_scorecard.sql DQ_SCORECARD view + rollup queries
run_pipeline.py                 Builds the DB, runs checks, emits the dashboard
dashboard/index.html            Generated interactive dashboard
```

## Data-quality dimensions

The `DQ_SCORECARD` view returns one row per check
(`dimension, check_name, table, total_records, failed_records`) so a
pass-rate rolls up cleanly per dimension and overall.

| Dimension | What it verifies |
|---|---|
| **Completeness** | Mandatory fields (MTART, MEINS, MAKTX, NAME1) are populated |
| **Validity** | Values fall in allowed domains (material type, procurement type, ISO country, positive weight) |
| **Uniqueness** | Primary keys do not duplicate |
| **Referential Integrity** | Child rows (MAKT, MARC) point to a real MARA parent |
| **Consistency** | Target agrees with source — the migration check |

## Sample findings

The seeded sample data deliberately contains two defects so the checks have
something to catch:

- **Missing record** — `MATNR 1004` exists in source but not in the target.
- **Value mismatch** — `MATNR 1003` net weight is `8.00` in source vs `8.5` in target.

These surface as a sub-100% **Consistency** score and dedicated tables on the
dashboard.

## Tables modeled

| Table | Description | Key |
|---|---|---|
| MARA | Material master (general) | MATNR |
| MAKT | Material descriptions | MATNR + SPRAS |
| MARC | Material plant data | MATNR + WERKS |
| KNA1 | Customer master (general) | KUNNR |

## Notes

`recon.db` is regenerated on every run and is git-ignored. Swap the sample
INSERTs in `02`/`04` for your own extracts to reconcile real datasets.
