# Decisión D1 · 115 pueblos canónicos

## Cifra canónica

**El número de pueblos indígenas reconocidos por el sistema es 115**, conforme al Censo Nacional de Población y Vivienda 2018 del DANE.

## Por qué 115 y no 121 ni 102

Existen tres cifras circulando en documentos institucionales:

| Cifra | Fuente | Unidad de registro |
|---|---|---|
| **115** | DANE — CNPV 2018 | Pueblo autorreconocido con respuesta válida en el censo |
| 121 | ONIC | Pueblos reconocidos por la organización indígena (incluye autorreconocimientos no captados en CNPV) |
| 102 | Mininterior — Decreto 1953/2014 | Pueblos con resguardo titulado y representación formal en mesas de concertación |

La cifra **115 es la única que mantiene coherencia con el universo censal completo** (1,9 millones de personas autorreconocidas como indígenas). Los pueblos adicionales reportados por ONIC (6) o reducidos por Mininterior (13) corresponden a unidades de registro distintas y no son comparables.

## Implicación operativa

- **Toda visualización agregada usa 115 como denominador.**
- **Los catálogos del frontend muestran 115 entradas.**
- **Las consultas a `pueblo.disc_nacional` retornan 115 filas como máximo.**
- **Los informes territoriales de tipo `pueblo` se generan para los 115 pueblos del CNPV 2018.**

## Decisiones derivadas

- Pueblos con población muy pequeña (<200 personas en CNPV) se incluyen en agregados nacionales pero no se publican individualmente sin filtro de privacidad (k-anonimato ≥ 5).
- Para análisis comparativos con cifras ONIC históricas, se aplica una nota metodológica explícita.

## Referencias

- DANE · Censo Nacional de Población y Vivienda 2018 · resultados por pueblo indígena.
- ONIC · Plataforma de pueblos indígenas de Colombia.
- Mininterior · Decreto 1953 de 2014.

---

© EtniConsulting SAS — 2026
