-- Reconciliation 1: materials in SOURCE but missing from TARGET
SELECT s.MATNR, s.MTART
FROM SRC_MARA s
LEFT JOIN MARA t ON s.MATNR = t.MATNR
WHERE t.MATNR IS NULL;

-- Reconciliation 2: materials whose net weight differs between source and target
SELECT s.MATNR, s.NTGEW AS source_weight, t.NTGEW AS target_weight
FROM SRC_MARA s
JOIN MARA t ON s.MATNR = t.MATNR
WHERE CAST(s.NTGEW AS REAL) <> t.NTGEW;

-- Reconciliation 3: row count comparison, source vs target
SELECT 'MARA' AS table_name,
       (SELECT COUNT(*) FROM SRC_MARA) AS source_count,
       (SELECT COUNT(*) FROM MARA)     AS target_count;