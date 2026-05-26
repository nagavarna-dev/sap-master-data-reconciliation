INSERT INTO MAKT (MATNR, SPRAS, MAKTX) VALUES
 ('1001', 'E', 'Pump housing assembly'),
 ('1002', 'E', 'Drive shaft component'),
 ('1003', 'E', 'Raw steel billet');

INSERT INTO MARC (MATNR, WERKS, DISMM, BESKZ) VALUES
 ('1001', '1000', 'PD', 'E'),
 ('1002', '1000', 'PD', 'E'),
 ('1003', '1000', 'VB', 'F');

INSERT INTO KNA1 (KUNNR, NAME1, LAND1, ORT01) VALUES
 ('5001', 'Atlas Manufacturing', 'US', 'Chicago'),
 ('5002', 'Nord Industrie', 'FR', 'Lyon'),
 ('5003', 'Brasil Componentes', 'BR', 'Sao Paulo');

 INSERT INTO MARA (MATNR, MTART, MBRSH, MATKL, MEINS, NTGEW, ERSDA) VALUES
 ('1001', 'FERT', 'M', '1001', 'EA', 12.5, '2024-01-10'),
 ('1002', 'HALB', 'M', '1002', 'KG', 3.20, '2024-01-11'),
 ('1003', 'ROH',  'C', '2001', 'KG', 8.5, '2024-01-12');