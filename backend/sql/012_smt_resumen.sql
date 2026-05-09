-- ================================================================
-- Migration 012: smt.resumen + trigger agregación con k-anonimato
-- ================================================================
-- Reusa tabla smt.resumen pre-existente (cols: dimension, categoria,
-- valor, pct, periodo, created_at). Agrega:
--   - función smt.recalcular_resumen() con k-anonimato k>=30
--   - trigger ON INSERT/UPDATE/DELETE en smt.respuestas_formulario
--   - índice complementario sobre dimension
-- Idempotente: re-aplicar no rompe (DROP TRIGGER IF EXISTS).
-- ================================================================

CREATE SCHEMA IF NOT EXISTS smt;

-- Idempotente: tabla ya existe; agregamos índice si falta
CREATE INDEX IF NOT EXISTS ix_smt_resumen_dimension ON smt.resumen (dimension);

-- ----------------------------------------------------------------
-- FUNCION: recalcular smt.resumen (k-anonimato enforced k>=30)
-- ----------------------------------------------------------------
CREATE OR REPLACE FUNCTION smt.recalcular_resumen() RETURNS VOID AS $$
DECLARE
    v_periodo VARCHAR(10) := to_char(NOW(), 'YYYY-MM');
    v_total INTEGER;
BEGIN
    -- Limpiar agregación del periodo actual antes de recalcular
    DELETE FROM smt.resumen WHERE periodo = v_periodo;

    -- Total de respuestas del periodo (CPLI=si)
    SELECT COUNT(*) INTO v_total
    FROM smt.respuestas_formulario
    WHERE cpli_consentimiento = 'si'
      AND to_char(fecha_envio, 'YYYY-MM') = v_periodo;

    IF v_total IS NULL OR v_total < 30 THEN
        RETURN;  -- k-anonimato: no exponer ninguna categoría si total < 30
    END IF;

    -- Dimension: macro (a partir de cod_dpto via lookup smt_geo.dim_dptos)
    INSERT INTO smt.resumen (dimension, categoria, valor, pct, periodo)
    SELECT
        'macro' AS dimension,
        COALESCE(d.macro, 'SIN_MACRO') AS categoria,
        COUNT(*)::numeric AS valor,
        ROUND(100.0 * COUNT(*) / v_total, 2) AS pct,
        v_periodo
    FROM smt.respuestas_formulario rf
    LEFT JOIN smt_geo.dim_dptos d ON d.cod_dpto = rf.cod_dpto
    WHERE rf.cpli_consentimiento = 'si'
      AND to_char(rf.fecha_envio, 'YYYY-MM') = v_periodo
    GROUP BY d.macro
    HAVING COUNT(*) >= 30;  -- k-anonimato

    -- Dimension: tipo_dificultad (extraído del JSONB datos.dificultades)
    INSERT INTO smt.resumen (dimension, categoria, valor, pct, periodo)
    SELECT
        'tipo_dificultad' AS dimension,
        tipo AS categoria,
        COUNT(*)::numeric AS valor,
        ROUND(100.0 * COUNT(*) / v_total, 2) AS pct,
        v_periodo
    FROM smt.respuestas_formulario rf,
         jsonb_array_elements_text(COALESCE(rf.datos->'dificultades', '[]'::jsonb)) AS tipo
    WHERE rf.cpli_consentimiento = 'si'
      AND to_char(rf.fecha_envio, 'YYYY-MM') = v_periodo
    GROUP BY tipo
    HAVING COUNT(*) >= 30;

    -- Dimension: completitud (heurística sobre datos JSONB · cuenta keys top-level)
    INSERT INTO smt.resumen (dimension, categoria, valor, pct, periodo)
    SELECT
        'completitud' AS dimension,
        bucket AS categoria,
        COUNT(*)::numeric AS valor,
        ROUND(100.0 * COUNT(*) / v_total, 2) AS pct,
        v_periodo
    FROM (
        SELECT
            CASE
                WHEN (SELECT COUNT(*) FROM jsonb_object_keys(rf.datos)) >= 8 THEN 'completo'
                WHEN (SELECT COUNT(*) FROM jsonb_object_keys(rf.datos)) >= 4 THEN 'parcial'
                ELSE 'minimo'
            END AS bucket
        FROM smt.respuestas_formulario rf
        WHERE rf.cpli_consentimiento = 'si'
          AND to_char(rf.fecha_envio, 'YYYY-MM') = v_periodo
    ) sub
    GROUP BY bucket
    HAVING COUNT(*) >= 30;
END;
$$ LANGUAGE plpgsql;

-- ----------------------------------------------------------------
-- TRIGGER: ON INSERT/UPDATE/DELETE en smt.respuestas_formulario
-- ----------------------------------------------------------------
CREATE OR REPLACE FUNCTION smt.trg_respuestas_recalcular() RETURNS TRIGGER AS $$
BEGIN
    PERFORM smt.recalcular_resumen();
    RETURN NULL;  -- AFTER trigger; resultado ignorado
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_smt_respuestas_recalcular ON smt.respuestas_formulario;
CREATE TRIGGER trg_smt_respuestas_recalcular
    AFTER INSERT OR UPDATE OR DELETE ON smt.respuestas_formulario
    FOR EACH STATEMENT
    EXECUTE FUNCTION smt.trg_respuestas_recalcular();

-- Recalcular una vez al aplicar la migración (idempotente)
SELECT smt.recalcular_resumen();
