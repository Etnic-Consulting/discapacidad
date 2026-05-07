# Metodología · Factor de Ajuste intercensal (FAC)

## Problema

Los Censos de 2005 (CG) y 2018 (CNPV) usan cuestionarios distintos para identificar capacidades diversas. La pregunta del Washington Group introducida en 2018 amplía el reconocimiento respecto al CG 2005, lo que produce un sesgo de medición al comparar prevalencias entre años.

## Solución · FAC

El **Factor de Ajuste (FAC)** es un coeficiente multiplicativo que se aplica a las cifras de 2005 para hacerlas comparables con 2018. Se calcula por grupo etario y por sexo.

```
prevalencia_2005_ajustada = prevalencia_2005_original × FAC[grupo_etario, sexo]
```

## Almacenamiento

Los factores viven en `proyecciones.fac` con la siguiente estructura:

| Campo | Tipo | Descripción |
|---|---|---|
| grupo_etario | text | "0-14", "15-29", "30-44", "45-59", "60+" |
| sexo | text | "H", "M" |
| factor | numeric | Coeficiente multiplicativo |
| metodo | text | "WG-mapping" / "regresion" |
| fuente | text | "DANE 2024 · estudio metodológico" |

Total de filas: **8** (4 grupos etarios × 2 sexos).

## Aplicación en el endpoint

`GET /api/v1/dashboard/intercensal?aplicar_fac=true`

- Cuando `aplicar_fac=true`, las cifras de 2005 retornadas son post-multiplicación.
- La respuesta incluye `fac_aplicado: true` y un campo `advertencia` con texto metodológico explícito.

## Limitaciones documentadas

1. El FAC asume que la diferencia 2005→2018 es **solo** por instrumento de medición. Si hubo cambios reales en prevalencia (envejecimiento, conflicto), el ajuste los enmascara parcialmente.
2. El factor se calculó a nivel nacional, no por pueblo. Para territorios con dinámicas migratorias o de conflicto particulares, la advertencia metodológica es especialmente relevante.
3. Los grupos etarios menores a 15 años tienen FAC con mayor incertidumbre por menor identificación de capacidades diversas en infancia.

## Recomendación de uso

- **Comparativos rápidos:** usar FAC.
- **Investigación rigurosa:** consultar tablas crudas con advertencia metodológica.
- **Comunicación pública:** mostrar cifras 2018 puras y referirse a 2005 como punto histórico, no como serie comparable.

## Referencias

- DANE · Estudio de comparabilidad CG 2005 / CNPV 2018 (capítulo discapacidad).
- Washington Group on Disability Statistics · Short Set of questions.

---

© EtniConsulting SAS — 2026
