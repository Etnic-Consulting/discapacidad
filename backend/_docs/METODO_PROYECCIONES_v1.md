# Metodología · Proyecciones poblacionales (aproximación Lee-Carter)

## Problema

Necesitamos proyectar la población indígena con capacidades diversas hasta 2030 para apoyar la planeación de programas y la formulación de presupuestos plurianuales en la ONIC.

## Aproximación Lee-Carter

El método Lee-Carter (1992) modela mortalidad y natalidad por edad y año mediante:

```
log(m_x,t) = a_x + b_x · k_t + e_x,t
```

donde:
- `a_x` representa el patrón promedio de mortalidad por edad
- `b_x` representa la sensibilidad al cambio temporal
- `k_t` representa la tendencia temporal global

Por simplicidad y por la disponibilidad limitada de series históricas para pueblos indígenas, en SMT-ONIC implementamos una **aproximación Lee-Carter** que:

1. Usa solo dos puntos temporales (CG 2005 y CNPV 2018, con FAC aplicado).
2. Proyecta mediante crecimiento geométrico por grupo etario y sexo.
3. Genera **bandas de confianza ±15 %** sobre la proyección central, derivadas empíricamente de la varianza observada en pueblos pequeños.

## Escenarios

Se generan **4 escenarios por grupo étnico**:

| Escenario | Supuesto |
|---|---|
| `optimista` | Mantenimiento cultural fuerte + aumento del autorreconocimiento |
| `central` | Tendencia 2005-2018 extrapolada |
| `pesimista` | Asimilación cultural + pérdida de identidad |
| `tendencial` | Solo demografía pura, sin componente identitaria |

## Almacenamiento

`proyecciones.escenarios`:

- 8 grupos étnicos × 4 escenarios × 26 años (2005-2030) = **832 filas**
- Para indígenas: 4 escenarios × 26 años = **104 filas** (verificable con smoke test 3)

## Endpoint

`GET /api/v1/dashboard/proyecciones?grupo_etnico=Indigena`

Retorna 104 filas con campos:
- `año`
- `escenario`
- `poblacion_total`
- `poblacion_disc`
- `prevalencia_pct`
- `ic_inferior`, `ic_superior` (bandas ±15 %)

## Limitaciones

1. La proyección no incorpora migración inter-pueblos.
2. Las bandas IC ±15 % son empíricas, no derivadas de un modelo bayesiano formal.
3. Para horizontes >2030 la incertidumbre crece exponencialmente · no se publican.

## Cuándo no usar las proyecciones

- Para análisis a nivel pueblo con población <500 (la base es estadísticamente inestable).
- Para diseño de cupos en políticas concretas (usar líneas base 2018, no proyectadas).

## Referencias

- Lee, R. D., & Carter, L. R. (1992). *Modeling and forecasting U.S. mortality*. JASA.
- DANE · Proyecciones de población 2018-2050.

---

© EtniConsulting SAS — 2026
