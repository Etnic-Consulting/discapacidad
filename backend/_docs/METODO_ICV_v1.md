# Metodología · Índice de Calidad de Vida (ICV) ponderado

## Definición

El **ICV ponderado** es un indicador sintético entre 0 y 100 que resume las condiciones de vida de un territorio (resguardo, municipio o departamento) a partir de doce dimensiones definidas en `indicadores.definiciones`.

## Las doce dimensiones

| # | Indicador | Schema |
|---|---|---|
| 1 | Necesidades Básicas Insatisfechas (NBI) | `pct_nbi` |
| 2 | Hacinamiento crítico | `pct_hacinamiento` |
| 3 | Analfabetismo (15+ años) | `pct_analfabetismo` |
| 4 | Asistencia escolar (5-17 años) | `pct_asistencia_escolar` |
| 5 | Jefatura femenina | `pct_jefatura_fem` |
| 6 | Acceso a agua mejorada | `pct_agua` |
| 7 | Acceso a alcantarillado | `pct_alcantarillado` |
| 8 | Acceso a energía eléctrica | `pct_energia` |
| 9 | Acceso a Internet | `pct_internet` |
| 10 | Dependencia demográfica | `pct_dependencia` |
| 11 | Vivienda con piso de tierra | `pct_piso_tierra` |
| 12 | Cobertura de salud (régimen subsidiado o contributivo) | `pct_salud` |

## Cálculo

```
ICV = Σ ponderacion[i] × normalizado[i]
```

donde:
- `normalizado[i]` es el valor del indicador i transformado a escala 0-100, con 100 siendo la mejor situación.
- `ponderacion[i]` es el peso definido en `indicadores.definiciones.peso_icv`, que suma 1 sobre los 12 indicadores.

Los pesos actuales privilegian saneamiento (agua + alcantarillado · 18 %), educación (analfabetismo + asistencia · 16 %) y vivienda (NBI + hacinamiento + piso · 22 %).

## Niveles geográficos disponibles

- `nacional` — un único valor de referencia
- `dpto` — uno por cada uno de los 33 departamentos
- `mpio` — uno por cada uno de los 1.122 municipios
- `resguardo` — uno por cada uno de los 830 resguardos titulados

## Endpoint

`GET /api/v1/indicadores/valores?periodo=2018&nivel_geo=mpio` (requiere token)

Retorna lista con `cod_territorio`, `nombre`, `icv`, y los 12 indicadores subyacentes.

## Brecha étnica

`GET /api/v1/dashboard/brecha` calcula la diferencia entre el ICV indígena y el ICV de la población sin pertenencia étnica del mismo territorio. Cada paso del cálculo incluye `source_detalle` con cita, marco normativo y URL de fuente para auditoría.

## Limitaciones

1. El ICV no captura dimensiones culturales (vitalidad de la lengua, prácticas tradicionales).
2. El peso del componente saneamiento es alto y puede sobreestimar la brecha en territorios remotos donde el agua entubada no es la norma cultural.
3. Para análisis sensibles a la cosmovisión indígena, complementar con la página *Voz Propia*.

## Referencias

- DANE · Indicadores socioeconómicos por territorio · MGN 2018.
- DNP · Metodología NBI ajustada.

---

© EtniConsulting SAS — 2026
