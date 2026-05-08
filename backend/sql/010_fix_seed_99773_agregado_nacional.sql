-- ============================================================================
-- Fix critico · seed CNPV 2018 con agregado nacional indigena mal asignado
-- al cod_mpio 99773 (Cumaribo, Vichada).
--
-- DETECTADO: 2026-05-08
-- IMPACTO: cifra "total indigenas" duplicada (3.7M en vez de 1.9M correcto)
--          porque el script de carga puso el agregado nacional (1.910.476)
--          como una fila adicional en cod_mpio=99773.
--
-- AFECTADAS:
--   - cnpv.prevalencia_etnia_mpio: 1 fila inflada (Indigena 99773)
--   - pueblo.pueblo_municipio: ~50 filas inflada (toda la poblacion nacional
--     de cada pueblo asignada a Cumaribo)
--   - cnpv.resumen_nacional_etnico: tiene Indigena pob_total = 3.753.504 que
--     es el doble del valor correcto (no se modifica · ya no se consume desde
--     el endpoint nacional)
--
-- POST-FIX:
--   - cnpv.prevalencia_etnia_mpio Indigena SUM = ~1.843.028 (era 3.753.504)
--   - pueblo.pueblo_municipio para 99773 queda solo con valores razonables
--   - Cumaribo aparecera con 0 o cifras minimas hasta re-extraccion REDATAM
--     real desde DANE (tarea v1.1)
--
-- IDEMPOTENTE: usa WHERE explicitos · re-ejecutar es seguro
-- ============================================================================

BEGIN;

-- 1. Eliminar fila inflada en cnpv.prevalencia_etnia_mpio
DELETE FROM cnpv.prevalencia_etnia_mpio
WHERE cod_mpio = '99773'
  AND grupo_etnico = 'Indigena'
  AND periodo = '2018'
  AND pob_total > 100000;  -- threshold de seguridad · Cumaribo real <30K

-- 2. Eliminar filas inflada en pueblo.pueblo_municipio
-- Cualquier fila con cod_mpio=99773 y poblacion > 5000 es fantasma del agregado nacional
-- (Cumaribo total ~30K · ningun pueblo individual supera 5K dentro de Cumaribo)
DELETE FROM pueblo.pueblo_municipio
WHERE cod_mpio = '99773'
  AND periodo = '2018'
  AND poblacion > 5000;

-- 3. Marcar la fila Indigena de cnpv.resumen_nacional_etnico como obsoleta
-- (ya no se usa desde endpoint, pero documentamos)
COMMENT ON TABLE cnpv.resumen_nacional_etnico IS
  'Tabla con bug del seed: grupo_etnico=Indigena tiene valores duplicados x2. '
  'Para cifra nacional indigena usar pueblo.disc_nacional SUM. '
  'Pendiente re-extraccion REDATAM v1.1.';

-- 4. Validacion post-fix · debe dar ~1.8M (no 3.7M)
DO $$
DECLARE
  v_total bigint;
BEGIN
  SELECT COALESCE(SUM(pob_total), 0) INTO v_total
  FROM cnpv.prevalencia_etnia_mpio
  WHERE grupo_etnico = 'Indigena' AND periodo = '2018';

  RAISE NOTICE 'Post-fix: cnpv.prevalencia_etnia_mpio Indigena SUM = %', v_total;

  IF v_total > 2500000 THEN
    RAISE EXCEPTION 'Fix no aplicado correctamente · suma sigue inflada: %', v_total;
  END IF;
  IF v_total < 1500000 THEN
    RAISE EXCEPTION 'Fix elimino demasiado · suma muy baja: %', v_total;
  END IF;
  RAISE NOTICE 'OK · suma esta dentro de rango esperado (1.5M - 2.5M)';
END $$;

COMMIT;
