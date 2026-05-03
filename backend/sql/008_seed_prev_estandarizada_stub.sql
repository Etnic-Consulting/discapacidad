-- T_BD02 · Stub schema · prev_estandarizada
-- Datos pendientes · requiere completar 05_disc_x_edad_dpto.csv con cols normalizadas
-- Ver: proyectos/discapacidad/_scripts/T_BD02_prevalencia_estandarizada.py

CREATE SCHEMA IF NOT EXISTS indicadores;
CREATE TABLE IF NOT EXISTS indicadores.prev_estandarizada (
    grupo_etnico             VARCHAR(40) PRIMARY KEY,
    pob_observada            BIGINT,
    pob_disc_observada       BIGINT,
    prev_observada_pct       NUMERIC(8,4),
    prev_estandarizada_pct   NUMERIC(8,4),
    razon_estd_obs           NUMERIC(8,4),
    interpretacion           VARCHAR(50),
    actualizado_en           TIMESTAMPTZ DEFAULT NOW()
);
