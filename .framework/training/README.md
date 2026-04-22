# Training Corrections Registry

Dataset de correcciones aplicadas por **clip** sobre código generado por **Ollama**, en formato apto para fine-tuning de LoRA (siguiente iteración: `convocav52`).

## Estructura

```
.framework/training/
  README.md                  (este archivo)
  corrections.jsonl          (índice append-only, una entrada por delegación)
  raw/<task_id>.txt          (output crudo de Ollama, sin tocar)
```

## Schema de cada entrada en `corrections.jsonl`

```json
{
  "ts": "2026-04-21T17:32:00Z",
  "task_id": "F2.2-CONTRACTS-ENDPOINT",
  "task_type": "standard_code",
  "model": "devstral:latest",
  "spec_path": "raw/F2.2-CONTRACTS-ENDPOINT.spec.txt",
  "ollama_raw_path": "raw/F2.2-CONTRACTS-ENDPOINT.raw.txt",
  "clip_final_path": "raw/F2.2-CONTRACTS-ENDPOINT.final.txt",
  "duration_s": 24.76,
  "tokens": 386,
  "fixes": [
    {"type": "missing_import", "what": "ceil", "fix": "div entera (total + page_size - 1) // page_size"}
  ],
  "verdict": "merged_with_fixes",
  "lessons": [
    "Para endpoints nuevos, siempre proveer un endpoint exemplar a copiar (--context-files)"
  ]
}
```

## Tipos de fix (taxonomía)

- `missing_import` — librería usada sin importar
- `wrong_schema_field` — nombre de campo Pydantic equivocado
- `missing_field` — campo Pydantic obligatorio faltante
- `missing_error_handler` — sin try/except cuando el patrón del archivo lo exige
- `style_inconsistency` — desviación del estilo del archivo
- `wrong_signature` — argumentos/tipos incorrectos
- `routing_conflict` — orden de rutas FastAPI rompe matching
- `untested_path` — código que nunca alcanza producción
- `over_fetch` — query sin paginación o sin LIMIT
- `unsafe_sql` — concatenación en vez de bind params
- `mock_or_stub` — placeholder en vez de implementación real

## Verdictos posibles

- `accepted_as_is` — código mergeado sin fixes (Ollama ganó el round)
- `merged_with_fixes` — código mergeado con fixes (caso normal)
- `regenerated` — clip pidió a Ollama re-intentar
- `rejected` — clip lo desechó y reescribió desde cero
- `pending_audit` — entrada inicial, clip aún no cerró

## Cuándo se escribe

- **Auto** — `delegate_to_ollama.py` escribe `raw/<task_id>.raw.txt` y entrada `pending_audit`
- **Manual** — clip cierra con `clip_final_path`, `fixes`, `verdict`, `lessons`

## Para qué sirve

Cuando junte ~50–100 entradas:
1. **DPO** — pares `(spec, ollama_raw)` rejected vs `(spec, clip_final)` chosen
2. **SFT** — solo `(spec, clip_final)` como ground truth
3. **Análisis de modos de error** — `fixes[].type` revela patrones
