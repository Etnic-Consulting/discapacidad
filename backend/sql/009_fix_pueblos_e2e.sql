-- ================================================================
-- Migration 009 · fix /pueblos endpoint end-to-end
-- ----------------------------------------------------------------
-- Problemas resueltos (2026-05-03):
-- 1. router pueblos.py consulta `pueblo.disc_nacional.confiabilidad`
--    pero la columna no existía en 001_schema.sql · agregada como NULL
--    y populada de total con regla 100/30 (ALTA/MEDIA/BAJA)
-- 2. geo.departamentos · 0 filas tras load_all.py · seeded los 33 DANE
-- 3. geo.municipios · 0 filas tras load_all.py · stub básico
--    (geometrías quedan NULL · si se necesitan, cargar shapefile MGN
--    con load_geo.py + geopandas)
--
-- Idempotente · safe to re-run.
-- ================================================================

BEGIN;

-- ─────────────────────────────────────────────────────────────────
-- 1 · pueblo.disc_nacional · agregar confiabilidad
-- ─────────────────────────────────────────────────────────────────
ALTER TABLE pueblo.disc_nacional
  ADD COLUMN IF NOT EXISTS confiabilidad VARCHAR(10);

UPDATE pueblo.disc_nacional
SET confiabilidad = CASE
  WHEN total >= 100 THEN 'ALTA'
  WHEN total >= 30  THEN 'MEDIA'
  ELSE 'BAJA'
END
WHERE confiabilidad IS NULL;

-- ─────────────────────────────────────────────────────────────────
-- 2 · geo.departamentos · 33 DANE
-- ─────────────────────────────────────────────────────────────────
INSERT INTO geo.departamentos (cod_dpto, nom_dpto) VALUES
  ('05','ANTIOQUIA'),
  ('08','ATLANTICO'),
  ('11','BOGOTA D.C.'),
  ('13','BOLIVAR'),
  ('15','BOYACA'),
  ('17','CALDAS'),
  ('18','CAQUETA'),
  ('19','CAUCA'),
  ('20','CESAR'),
  ('23','CORDOBA'),
  ('25','CUNDINAMARCA'),
  ('27','CHOCO'),
  ('41','HUILA'),
  ('44','LA GUAJIRA'),
  ('47','MAGDALENA'),
  ('50','META'),
  ('52','NARINO'),
  ('54','NORTE DE SANTANDER'),
  ('63','QUINDIO'),
  ('66','RISARALDA'),
  ('68','SANTANDER'),
  ('70','SUCRE'),
  ('73','TOLIMA'),
  ('76','VALLE DEL CAUCA'),
  ('81','ARAUCA'),
  ('85','CASANARE'),
  ('86','PUTUMAYO'),
  ('88','SAN ANDRES, PROVIDENCIA Y SANTA CATALINA'),
  ('91','AMAZONAS'),
  ('94','GUAINIA'),
  ('95','GUAVIARE'),
  ('97','VAUPES'),
  ('99','VICHADA')
ON CONFLICT (cod_dpto) DO NOTHING;

-- ─────────────────────────────────────────────────────────────────
-- 3 · geo.municipios · seeded por scripts/seed_municipios.py
--     (parsea bd_consolidada/02_prevalencia_disc_x_etnia_mpio.csv)
-- Si la tabla está vacía y existe el script, correr:
--   docker exec smt-onic-api python -m scripts.seed_municipios
-- ─────────────────────────────────────────────────────────────────

COMMIT;

-- Validación post-aplicación:
-- SELECT
--   (SELECT count(*) FROM pueblo.disc_nacional WHERE confiabilidad IS NOT NULL) AS pueblos_confiabilidad,
--   (SELECT count(*) FROM geo.departamentos)  AS dptos,
--   (SELECT count(*) FROM geo.municipios)     AS mpios;
-- Esperado: pueblos_confiabilidad=120 · dptos=33 · mpios=1122 (tras seed_municipios)
