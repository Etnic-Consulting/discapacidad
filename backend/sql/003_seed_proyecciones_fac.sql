-- T11 · Seed para proyecciones.fac
-- Generado por T11_calcular_fac.py
-- Fecha: 2026-05-02 17:49:36
-- Fuente: bd_consolidada/CG2005_*.csv + 08_resumen_nacional_etnico.csv
-- Consumido por: dashboard.py /intercensal?aplicar_fac=true (T02)

CREATE SCHEMA IF NOT EXISTS proyecciones;

CREATE TABLE IF NOT EXISTS proyecciones.fac (
    grupo_etnico            VARCHAR(40) PRIMARY KEY,
    prev_cg2005_pct         NUMERIC(8,4),
    prev_cnpv2018_pct       NUMERIC(8,4),
    ajuste_envejecimiento   NUMERIC(6,4),
    fac                     NUMERIC(8,4),
    fac_ic_inferior         NUMERIC(8,4),
    fac_ic_superior         NUMERIC(8,4),
    nota                    TEXT,
    actualizado_en          TIMESTAMPTZ DEFAULT NOW()
);

BEGIN;
TRUNCATE proyecciones.fac;

INSERT INTO proyecciones.fac (grupo_etnico, prev_cg2005_pct, prev_cnpv2018_pct, ajuste_envejecimiento, fac, fac_ic_inferior, fac_ic_superior, nota) VALUES
  ('Afrodescendiente', 7.1347, 6.58, 1.1, 0.8384, 0.7127, 0.9642, 'FAC proxy · validar contra panel-cohorte cuando esté disponible'),
  ('Gitano_Rrom', 4.9415, 7.18, 1.09, 1.333, 1.1331, 1.533, 'FAC proxy · validar contra panel-cohorte cuando esté disponible'),
  ('Indigena', 5.9155, 6.0, 1.08, 0.9392, 0.7983, 1.08, 'FAC proxy · validar contra panel-cohorte cuando esté disponible'),
  ('Ningun_grupo', 8.4096, 7.33, 1.18, 0.7387, 0.6279, 0.8495, 'FAC proxy · validar contra panel-cohorte cuando esté disponible'),
  ('No_informa', 1.6568, 1.43, 1.1, 0.7846, 0.6669, 0.9023, 'FAC proxy · validar contra panel-cohorte cuando esté disponible'),
  ('Palenquero', 5.6241, 4.43, 1.1, 0.7161, 0.6087, 0.8235, 'FAC proxy · validar contra panel-cohorte cuando esté disponible'),
  ('Raizal', 10.0205, 2.34, 1.12, 0.2085, 0.1772, 0.2398, 'FAC proxy · validar contra panel-cohorte cuando esté disponible'),
  ('Total', 7.7612, 7.15, 1.15, 0.8011, 0.6809, 0.9212, 'FAC proxy · validar contra panel-cohorte cuando esté disponible');

COMMIT;