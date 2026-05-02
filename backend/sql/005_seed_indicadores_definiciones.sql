-- T10 · Seed para indicadores.definiciones
-- Generado por T10_seed_indicadores.py
-- Fecha: 2026-05-02 17:41:23
-- Fuente: outputs/fichas_indicadores/IND-*.md (Sprint S0 T04)
-- Cifra canónica de pueblos: 115 (D1 · DANE CNPV 2018)

BEGIN;

-- Idempotente: borra existentes antes de re-insertar
DELETE FROM indicadores.definiciones WHERE codigo IN ('CUL-01', 'CUL-02', 'DDH-01', 'DDH-02', 'ECO-01', 'ECO-02', 'EDU-01', 'EDU-02', 'SAL-01', 'SAL-02', 'TER-01', 'TER-02');

INSERT INTO indicadores.definiciones (codigo, nombre, grupo, formula, meta, fuente_primaria, fuente_cruce, unidad, descripcion) VALUES
  ('CUL-01', 'Hablantes de lengua materna', 'Cultura', '(pendiente · S1)', 'Frontend: `85%`. **Justificación:** ningún plan colombiano pone meta universal de hablantes — depende del estado de vitalidad de cada lengua. UNESCO Atlas marca 65 de las 68 lenguas indígenas colombianas como "amenazadas" o "en peligro". Meta del 85% solo aplica a pueblos con lengua **vital** (Wayuu', 'DANE CNPV 2018', '', '%', ''),
  ('CUL-02', 'Prácticas de partería propia', 'Cultura', '(pendiente · S1)', 'Frontend: `70%`. **Discutible.** No hay norma que indique meta universal. Decisión política: mientras más alta, más vitalidad cultural; pero también más riesgo médico si no hay sistema mixto que asegure transferencia rápida en complicaciones. **Propuesta:** redefinir la meta como **"% de partos con', 'DANE CNPV 2018', '', '%', ''),
  ('DDH-01', 'Denuncias atendidas', 'DDHH', '(pendiente · S1)', 'Frontend: `100%`. **Justificación correcta:** debido proceso → toda denuncia formal debe ser atendida. Meta = 100% no es negociable.', 'DANE CNPV 2018', '', '%', ''),
  ('DDH-02', 'Casos con certificado de víctima', 'DDHH', '(pendiente · S1)', 'Frontend: `90%`. **Justificación:** Auto 004/2009 + Decreto 4633/2011 mandan reparación integral universal a indígenas víctimas. Meta = 100% (no 90%) — toda víctima debe estar reconocida. **Recomendación:** ajustar la meta a 100% en el frontend.', 'DANE CNPV 2018', '', '%', ''),
  ('ECO-01', 'Ingresos por debajo de línea de pobreza', 'Económico', '(pendiente · S1)', 'Frontend: `15%`. **Justificación:** ODS 1.2 plantea reducir pobreza al 50% del nivel actual al 2030; PND propone bajar pobreza monetaria nacional al 25% al 2026. Meta del 15% para indígenas con disc es coherente con cierre de brecha étnica + discapacidad. **Aceptable.**', 'DANE CNPV 2018', '', '%', ''),
  ('ECO-02', 'Proyectos productivos activos', 'Económico', '(pendiente · S1)', 'Frontend: `60%`. **Justificación débil** — no hay norma que mande "60% de comunidades con proyecto productivo". Es meta política. **Recomendación:** discutir con dirigencia ONIC y proponer meta como % de pueblos (115) con plan de vida con componente económico documentado.', 'DANE CNPV 2018', '', '%', ''),
  ('EDU-01', 'Tasa de analfabetismo (≥15 años)', 'Educación', '(pendiente · S1)', 'Meta vigente del frontend: `5%` (alfabetismo total ≈ 95%). **Justificación:** ODS 4.6 plantea alfabetización universal antes de 2030. Para población indígena con discapacidad, 5% es ambicioso pero alineado con la meta nacional CONPES 4040 (2021).', 'DANE CNPV 2018', '', '%', ''),
  ('EDU-02', 'Permanencia en educación secundaria', 'Educación', '(pendiente · S1)', 'Frontend: `90%`. **Justificación:** Plan Decenal de Educación 2016-2026 plantea cobertura universal en secundaria; CONPES 4040/2021 establece 95% en zonas urbanas y 80% en rurales para 2030. Meta del 90% es razonable como promedio.', 'DANE CNPV 2018', '', '%', ''),
  ('SAL-01', 'Cobertura de salud efectiva', 'Salud', '(pendiente · S1)', '**Meta vigente del frontend `90%` no tiene fuente.** Propuesta: meta canónica = **100% (Pacto por la Equidad PND 2022-2026 · Art. 31 CDPD ONU)**. Wilson: la meta del 90% se mantiene como banda inferior si se quiere "umbral de alarma".', 'DANE CNPV 2018', '', '%', ''),
  ('SAL-02', 'Acceso a medicina propia', 'Salud', '(pendiente · S1)', '**Meta vigente del frontend `100%`.** Discutible: 100% no es deseable — implica reemplazar SGSSS por medicina propia. La meta razonable es **complementariedad efectiva** (paciente accede a ambas según lo que la afección requiera). Propuesta: redefinir como "tasa de uso conjunto medicina propia + occ', 'DANE CNPV 2018', '', '%', ''),
  ('TER-01', 'Tenencia de resguardo titulado', 'Territorio', '(pendiente · S1)', 'Frontend: `100%`. **Justificación correcta:** Decreto 1953/2014 implica que todos los pueblos reconocidos tengan al menos un territorio titulado. Es derecho colectivo no negociable. Meta = 100%.', 'DANE CNPV 2018', '', '%', ''),
  ('TER-02', 'Acceso a agua potable', 'Territorio', '(pendiente · S1)', 'Frontend: `95%`. **Justificación:** ODS 6.1 establece "agua segura universalmente accesible" (= 100%); Colombia comprometida con 95% en zona rural y 100% urbana al 2030. Meta razonable pero ambiciosa para zonas indígenas remotas.', 'DANE CNPV 2018', '', '%', '');

COMMIT;