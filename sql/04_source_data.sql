INSERT INTO SRC_MARA (MATNR, MTART, MBRSH, MATKL, MEINS, NTGEW, ERSDA) VALUES
 ('1001', 'FERT', 'M', '1001', 'EA', '12.5', '2024-01-10'),
 ('1002', 'HALB', 'M', '1002', 'KG', '3.20', '2024-01-11'),
 ('1003', 'ROH',  'C', '2001', 'KG', '8.00', '2024-01-12'),   -- target has 8.5 (mismatch)
 ('1004', 'HAWA', 'M', '1001', 'PC', '1.00', '2024-01-13');   -- not in target (missing)

INSERT INTO SRC_MAKT (MATNR, SPRAS, MAKTX) VALUES
 ('1001', 'E', 'Pump housing assembly'),
 ('1002', 'E', 'Drive shaft component'),
 ('1003', 'E', 'Raw steel billet'),
 ('1004', 'E', 'Trading part bracket');

INSERT INTO SRC_KNA1 (KUNNR, NAME1, LAND1, ORT01) VALUES
 ('5001', 'Atlas Manufacturing', 'US', 'Chicago'),
 ('5002', 'Nord Industrie', 'FR', 'Lyon'),
 ('5003', 'Brasil Componentes', 'BR', 'Sao Paulo');