-- =====================================================================
-- Phase 4 — Data-Quality Scorecard
-- Dimensions: Completeness, Validity, Uniqueness, Referential Integrity,
--             Consistency (source vs target)
-- Each check returns one row: dimension, check_name, table, total, failed.
-- A single UNION ALL view (DQ_SCORECARD) rolls every check up so a BI tool
-- (Phase 5) can compute pass-rate = (total - failed) / total.
-- Pure SQLite; no extensions required.
-- =====================================================================

DROP VIEW IF EXISTS DQ_SCORECARD;

CREATE VIEW DQ_SCORECARD AS

-- ---------------------------------------------------------------------
-- COMPLETENESS — mandatory fields must not be NULL / blank in TARGET
-- ---------------------------------------------------------------------
SELECT 'Completeness' AS dimension,
       'MARA.MTART not null'        AS check_name,
       'MARA'                       AS table_name,
       (SELECT COUNT(*) FROM MARA)  AS total_records,
       (SELECT COUNT(*) FROM MARA WHERE MTART IS NULL OR TRIM(MTART) = '') AS failed_records
UNION ALL
SELECT 'Completeness', 'MARA.MEINS not null', 'MARA',
       (SELECT COUNT(*) FROM MARA),
       (SELECT COUNT(*) FROM MARA WHERE MEINS IS NULL OR TRIM(MEINS) = '')
UNION ALL
SELECT 'Completeness', 'MAKT.MAKTX not null', 'MAKT',
       (SELECT COUNT(*) FROM MAKT),
       (SELECT COUNT(*) FROM MAKT WHERE MAKTX IS NULL OR TRIM(MAKTX) = '')
UNION ALL
SELECT 'Completeness', 'KNA1.NAME1 not null', 'KNA1',
       (SELECT COUNT(*) FROM KNA1),
       (SELECT COUNT(*) FROM KNA1 WHERE NAME1 IS NULL OR TRIM(NAME1) = '')

-- ---------------------------------------------------------------------
-- VALIDITY — values must fall inside the allowed SAP domain / format
-- ---------------------------------------------------------------------
UNION ALL
SELECT 'Validity', 'MARA.MTART in allowed material types', 'MARA',
       (SELECT COUNT(*) FROM MARA),
       (SELECT COUNT(*) FROM MARA
        WHERE MTART NOT IN ('FERT','HALB','ROH','HAWA','DIEN','VERP'))
UNION ALL
SELECT 'Validity', 'MARA.NTGEW positive number', 'MARA',
       (SELECT COUNT(*) FROM MARA),
       (SELECT COUNT(*) FROM MARA WHERE NTGEW IS NULL OR NTGEW <= 0)
UNION ALL
SELECT 'Validity', 'MARC.BESKZ in (E,F,X)', 'MARC',
       (SELECT COUNT(*) FROM MARC),
       (SELECT COUNT(*) FROM MARC WHERE BESKZ NOT IN ('E','F','X'))
UNION ALL
SELECT 'Validity', 'KNA1.LAND1 is 2-char ISO code', 'KNA1',
       (SELECT COUNT(*) FROM KNA1),
       (SELECT COUNT(*) FROM KNA1 WHERE LENGTH(TRIM(LAND1)) <> 2)

-- ---------------------------------------------------------------------
-- UNIQUENESS — primary keys must not duplicate
-- ---------------------------------------------------------------------
UNION ALL
SELECT 'Uniqueness', 'MARA.MATNR unique', 'MARA',
       (SELECT COUNT(*) FROM MARA),
       (SELECT COALESCE(SUM(c - 1), 0) FROM
            (SELECT COUNT(*) c FROM MARA GROUP BY MATNR HAVING c > 1))
UNION ALL
SELECT 'Uniqueness', 'MAKT (MATNR,SPRAS) unique', 'MAKT',
       (SELECT COUNT(*) FROM MAKT),
       (SELECT COALESCE(SUM(c - 1), 0) FROM
            (SELECT COUNT(*) c FROM MAKT GROUP BY MATNR, SPRAS HAVING c > 1))
UNION ALL
SELECT 'Uniqueness', 'KNA1.KUNNR unique', 'KNA1',
       (SELECT COUNT(*) FROM KNA1),
       (SELECT COALESCE(SUM(c - 1), 0) FROM
            (SELECT COUNT(*) c FROM KNA1 GROUP BY KUNNR HAVING c > 1))

-- ---------------------------------------------------------------------
-- REFERENTIAL INTEGRITY — child rows must point to a real MARA parent
-- ---------------------------------------------------------------------
UNION ALL
SELECT 'Referential Integrity', 'MAKT.MATNR exists in MARA', 'MAKT',
       (SELECT COUNT(*) FROM MAKT),
       (SELECT COUNT(*) FROM MAKT m
        LEFT JOIN MARA a ON m.MATNR = a.MATNR WHERE a.MATNR IS NULL)
UNION ALL
SELECT 'Referential Integrity', 'MARC.MATNR exists in MARA', 'MARC',
       (SELECT COUNT(*) FROM MARC),
       (SELECT COUNT(*) FROM MARC c
        LEFT JOIN MARA a ON c.MATNR = a.MATNR WHERE a.MATNR IS NULL)

-- ---------------------------------------------------------------------
-- CONSISTENCY — TARGET must agree with SOURCE (the migration check)
-- ---------------------------------------------------------------------
UNION ALL
SELECT 'Consistency', 'Source MARA rows present in target', 'MARA',
       (SELECT COUNT(*) FROM SRC_MARA),
       (SELECT COUNT(*) FROM SRC_MARA s
        LEFT JOIN MARA t ON s.MATNR = t.MATNR WHERE t.MATNR IS NULL)
UNION ALL
SELECT 'Consistency', 'MARA.NTGEW matches source', 'MARA',
       (SELECT COUNT(*) FROM SRC_MARA s JOIN MARA t ON s.MATNR = t.MATNR),
       (SELECT COUNT(*) FROM SRC_MARA s JOIN MARA t ON s.MATNR = t.MATNR
        WHERE CAST(s.NTGEW AS REAL) <> t.NTGEW);

-- =====================================================================
-- Convenience queries (run after the view exists)
-- =====================================================================

-- Per-check detail with pass-rate
SELECT dimension, check_name, table_name,
       total_records, failed_records,
       ROUND(100.0 * (total_records - failed_records)
             / NULLIF(total_records, 0), 1) AS pass_rate_pct
FROM DQ_SCORECARD
ORDER BY dimension, check_name;

-- Rollup by dimension
SELECT dimension,
       SUM(total_records)  AS total_records,
       SUM(failed_records) AS failed_records,
       ROUND(100.0 * (SUM(total_records) - SUM(failed_records))
             / NULLIF(SUM(total_records), 0), 1) AS pass_rate_pct
FROM DQ_SCORECARD
GROUP BY dimension
ORDER BY pass_rate_pct ASC;

-- Single overall data-quality score
SELECT ROUND(100.0 * (SUM(total_records) - SUM(failed_records))
             / NULLIF(SUM(total_records), 0), 1) AS overall_quality_pct
FROM DQ_SCORECARD;
