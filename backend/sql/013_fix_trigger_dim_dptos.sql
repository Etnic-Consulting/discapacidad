-- ================================================================
-- Migration 013: Fix smt.recalcular_resumen() para no depender
-- de smt_geo.dim_dptos (tabla que no existe en el deploy actual).
-- Sustituye por lookup en smt_geo.comunidades (dpto_ccdgo → macro)
-- con fallback al campo datos->>'macrorregion' del JSONB.
-- Idempotente: CREATE OR REPLACE FUNCTION.
-- ================================================================

CREATE OR REPLACE FUNCTION smt.recalcular_resumen() RETURNS VOID AS $$
DECLARE
    v_periodo VARCHAR(10) := to_char(NOW(), 'YYYY-MM');
    v_total INTEGER;
BEGIN
    -- Limpiar agregacion del periodo actual antes de recalcular
    DELETE FROM smt.resumen WHERE periodo = v_periodo;

    -- Total de respuestas del periodo (CPLI=si)
    SELECT COUNT(*) INTO v_total
    FROM smt.respuestas_formulario
    WHERE cpli_consentimiento = 'si'
      AND to_char(fecha_envio, 'YYYY-MM') = v_periodo;

    IF v_total IS NULL OR v_total < 30 THEN
        RETURN;  -- k-anonimato: no exponer ninguna categoria si total < 30
    END IF;

    -- Dimension: macro
    -- Lookup: smt_geo.comunidades (dpto_ccdgo -> macro) con fallback a datos->>'macrorregion'
    INSERT INTO smt.resumen (dimension, categoria, valor, pct, periodo)
    SELECT
        'macro' AS dimension,
        COALESCE(
            (SELECT DISTINCT c.macro
             FROM smt_geo.comunidades c
             WHERE c.dpto_ccdgo = rf.cod_dpto
               AND c.macro IS NOT NULL
             LIMIT 1),
            rf.datos->>'macrorregion',
            'SIN_MACRO'
        ) AS categoria,
        COUNT(*)::numeric AS valor,
        ROUND(100.0 * COUNT(*) / v_total, 2) AS pct,
        v_periodo
    FROM smt.respuestas_formulario rf
    WHERE rf.cpli_consentimiento = 'si'
      AND to_char(rf.fecha_envio, 'YYYY-MM') = v_periodo
    GROUP BY COALESCE(
        (SELECT DISTINCT c.macro
         FROM smt_geo.comunidades c
         WHERE c.dpto_ccdgo = rf.cod_dpto
           AND c.macro IS NOT NULL
         LIMIT 1),
        rf.datos->>'macrorregion',
        'SIN_MACRO'
    )
    HAVING COUNT(*) >= 30;

    -- Dimension: tipo_dificultad (extraido del JSONB datos.dificultades)
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

    -- Dimension: completitud (heuristica sobre datos JSONB - cuenta keys top-level)
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
