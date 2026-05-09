-- ============================================================================
-- Fix critico v2 · seed CNPV 2018 con agregado nacional indigena mal asignado
-- al cod_dpto='99' (Vichada) en tablas departamentales.
--
-- DETECTADO: 2026-05-09 (continuacion del fix 010 que solo limpio mpio)
-- IMPACTO: filtros por dpto='99' o agregaciones a nivel dpto retornaban toda
--          la poblacion indigena nacional concentrada en Vichada.
--
-- Cifras de evidencia (Vichada Indigena pre-fix vs Caldas Indigena referencia):
--   prevalencia_etnia_dpto:     pob_total = 1.918.671 (vs ~30K real Vichada)
--   dificultades_etnia_dpto:    pob_total = 227.072 por cada dificultad
--   limitacion_ppal_etnia_dpto: Total = 113.536 (= toda la CD indigena nacional)
--   salud_etnia_dpto:           enfermo Total = 1.918.671
--
-- AFECTADAS (4 tablas con grupo_etnico='Indigena' para dpto='99'):
--   1. cnpv.prevalencia_etnia_dpto
--   2. cnpv.dificultades_etnia_dpto (9 filas, una por dificultad WG)
--   3. cnpv.limitacion_ppal_etnia_dpto (10 filas)
--   4. cnpv.salud_etnia_dpto (multiples filas por variable/categoria)
--
-- NO AFECTADAS (verificadas OK · no segmentan por grupo_etnico):
--   - cnpv.disc_edad_dpto Vichada Total = 71.405 (proporcional)
--   - cnpv.disc_sexo_dpto Vichada Total = 71.405 (proporcional)
--
-- POST-FIX:
--   prevalencia_etnia_dpto Indigena SUM ≈ 1.876.664 (era 3.795.335)
--   filtros por cod_dpto=99 retornaran 0 indigenas hasta re-extraccion REDATAM
--   real desde DANE (tarea v1.1)
--
-- IDEMPOTENTE: usa WHERE explicitos · re-ejecutar es seguro
-- ============================================================================

BEGIN;

-- 1. prevalencia_etnia_dpto · 1 fila inflada (1.918.671 indigenas Vichada)
DELETE FROM cnpv.prevalencia_etnia_dpto
WHERE cod_dpto = '99'
  AND grupo_etnico = 'Indigena'
  AND periodo = '2018'
  AND pob_total > 50000;  -- threshold seguro · Vichada real <30K

-- 2. dificultades_etnia_dpto · 9 filas inflada (pob_total 227.072 cada una)
DELETE FROM cnpv.dificultades_etnia_dpto
WHERE cod_dpto = '99'
  AND grupo_etnico = 'Indigena'
  AND periodo = '2018'
  AND pob_total > 50000;

-- 3. limitacion_ppal_etnia_dpto · 10 filas inflada (Total = 113.536)
DELETE FROM cnpv.limitacion_ppal_etnia_dpto
WHERE cod_dpto = '99'
  AND grupo_etnico = 'Indigena'
  AND periodo = '2018'
  AND valor > 4000;  -- Caldas (referencia ~5K total) corta antes; Vichada real <2K

-- 4. salud_etnia_dpto · multiples filas inflada (enfermo Total = 1.918.671)
DELETE FROM cnpv.salud_etnia_dpto
WHERE cod_dpto = '99'
  AND grupo_etnico = 'Indigena'
  AND periodo = '2018'
  AND valor > 60000;  -- Caldas (referencia ~55K enfermo Total) corta antes

-- 5. Validacion post-fix
DO $$
DECLARE
  v_prev_sum bigint;
  v_dpto_indigena_count int;
BEGIN
  SELECT COALESCE(SUM(pob_total), 0) INTO v_prev_sum
  FROM cnpv.prevalencia_etnia_dpto
  WHERE grupo_etnico = 'Indigena' AND periodo = '2018';

  SELECT COUNT(*) INTO v_dpto_indigena_count
  FROM cnpv.prevalencia_etnia_dpto
  WHERE grupo_etnico = 'Indigena' AND periodo = '2018';

  RAISE NOTICE 'Post-fix dpto: prevalencia_etnia_dpto Indigena SUM = % (% dptos)',
    v_prev_sum, v_dpto_indigena_count;

  IF v_prev_sum > 2500000 THEN
    RAISE EXCEPTION 'Fix no aplicado · suma sigue inflada: %', v_prev_sum;
  END IF;
  IF v_prev_sum < 1500000 THEN
    RAISE EXCEPTION 'Fix elimino demasiado · suma muy baja: %', v_prev_sum;
  END IF;
  RAISE NOTICE 'OK · suma esta dentro de rango esperado (1.5M - 2.5M)';
END $$;

COMMIT;
