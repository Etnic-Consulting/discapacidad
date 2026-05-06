# LOAD_VICTIMAS_UARIV · Pipeline de carga de víctimas indígenas UARIV

**Versión:** 1.0 · 2026-05-06  
**Script canónico:** `backend/scripts/load_victimas_xlsx.py`  
**Fixes aplicados:** B1 · B2 · B3 · M1 · M2 · M3 · M5  
**Tablas pobladas:** `victimas.universo` · `victimas.resumen_pueblo_hecho`

---

## 1. Resumen ejecutivo

Este documento describe el pipeline de carga del módulo `/conflicto` del sistema SMT-ONIC. El script `load_victimas_xlsx.py` lee el archivo `LB_UNIV_VICT_INDIGENA.xlsx` (línea base UARIV de víctimas indígenas, 128 MB, 787.332 filas) y lo carga en dos tablas del esquema `victimas` de la base de datos PostgreSQL `smt_onic`.

**Cifras canónicas tras una carga exitosa:**

| Métrica | Valor |
|---|---|
| Filas totales en `victimas.universo` | 787.332 |
| Filas con `discapacidad = '1'` | 37.562 |
| Con pueblo imputado (discapacidad=1) | 37.191 (98,9 %) |
| Filas en `victimas.resumen_pueblo_hecho` | 6.329 |
| Tiempo estimado de carga | ~98 segundos |
| Composición por pertenencia étnica | 426.122 INDIGENA ACREDITADO RA + 361.210 INDIGENA |

**Pre-requisitos para ejecutar la carga:**

1. El contenedor Docker `smt-onic-db` corriendo y expuesto en `localhost:5450`.
2. El catálogo `pueblo.pueblo_dominante_mpio` poblado (969 filas, período 2018).
3. El catálogo `cat.pueblos_indigenas` poblado (120 filas).
4. Python 3.10+ con `openpyxl` y `psycopg2` instalados en el entorno.
5. El XLSX en su ruta canónica (ver sección 2).

El loader es idempotente: trunca las tablas antes de cargar, por lo que puede re-ejecutarse desde cero sin efectos acumulativos.

---

## 2. Fuentes de datos UARIV

### 2.1 Fuente canónica

**Archivo:** `LB-Victimas -Unica\LB_UNIV_VICT_INDIGENA.xlsx`  
**Ruta completa:** `C:\Users\wilso\Desktop\discapacidad\Bases Uariv-20260506T040813Z-3-001\Bases Uariv\LB-Victimas -Unica\LB_UNIV_VICT_INDIGENA.xlsx`  
**Tamaño:** 128 MB (133.616.262 bytes en disco)  
**Sheet:** `LB_UNIV_VICT_INDIGENA`  
**Filas de datos:** 787.332  
**Columnas:** 35 (header en fila 1, datos desde fila 2)

Este XLSX contiene el universo de víctimas con pertenencia étnica indígena reconocidas por la UARIV al corte de la línea base. Fue entregado directamente por la UARIV a la ONIC como parte del proceso de implementación del Decreto Ley 4633 de 2011.

### 2.2 Diccionario oficial

**Archivo:** `VARIABLES UNIVERSO VICTIMAS LB.xlsx`  
**Tamaño:** 24 KB  
**Ruta:** `C:\Users\wilso\Desktop\discapacidad\Bases Uariv-20260506T040813Z-3-001\Bases Uariv\VARIABLES UNIVERSO VICTIMAS LB.xlsx`

Contiene la descripción formal de cada columna del XLSX canónico. La sheet activa tiene dos secciones: `universo_victimas_pers_LB` (tabla de personas, columnas de identificación) y `universo_victimas_LB` (histórico de hechos victimizantes). Este diccionario es la fuente autoritativa para interpretación de columnas y es el que define que `CONSPERSONA` (no `IDPERSONA`) es el identificador de persona en el XLSX indígena (ver decisión B2 en sección 6).

### 2.3 Copias redundantes — NO usar

En la misma carpeta `Bases Uariv` existen cuatro archivos `.xls` con nombres similares. Ninguno debe usarse como fuente de carga:

| Archivo | Tamaño | Problema |
|---|---|---|
| `LB_UNIV_VICT_INDIGENA-4.xls` | 33 MB | Formato `.xls` antiguo (Excel 97-2003); truncado a ~65.000 filas por límite del formato |
| `LB_UNIV_VICT_INDIGENA-copia II.xls` | 29 MB | Mismo problema de truncamiento; parece ser una exportación parcial |
| `LB_UNIV_VICT_INDIGENA-COPIA III.xls` | 90 MB | Archivo más grande pero sigue siendo `.xls`; puede tener cálculos adicionales o columnas derivadas |
| `LB_UNIV_VICT_INDIGENA-COPIA.xls` | 70 MB | Otra copia redundante; schema no verificado |

El formato `.xls` de Excel 97-2003 tiene un límite de 65.536 filas por hoja, lo que hace imposible que contenga las 787.332 filas del universo indígena. Usar cualquiera de estos archivos como fuente produciría una carga incompleta sin error visible (el script cargaría lo que encuentra sin saber que está truncado).

### 2.4 Archivos relacionados — referencia o módulos futuros

| Archivo / Carpeta | Uso |
|---|---|
| `LB_Caracterizacion_Hogar_Anonimizada/` | Caracterización de hogar; alimentará módulo de hogar en sprints futuros |
| `Hecho victimizante por año-nacional.xls` | Agregados nacionales por año; referencia estadística externa, no se carga a BD |
| `Hecho victimizante por etnia.xls` | Agregados por etnia; referencia cruzada para validación N2 |
| `Hechos Victimizantes Nacional.xlsx` | Resumen nacional; solo referencia |
| `hECHOS VICTIMIZANTES POR MUNICIPIO PARA MAPA-*.xls` | Datos municipales por tipo de hecho; potencialmente útiles para capas GIS futuras |
| `Mapa Victimas indígenas-*.jpg` / `.mxd` | Cartografía del proceso UARIV; referencia visual, no se procesa |
| `Listados_DIVIPOLA-2020.xlsx` | Códigos DIVIPOLA 2020; usado para validación de municipios |
| `VARIABLES UNIVERSO VICTIMAS LB.xlsx` | Diccionario oficial (ver 2.2) |

### 2.5 Archivo crudo universo Colombia — NO disponible

La UARIV mantiene un archivo `UNIVERSO_VICTIMAS_LB_ANONIMO.txt` de ~4,3 GB que contiene el universo completo de víctimas de Colombia (no solo indígenas). Este archivo **no está disponible en disco** en el entorno de trabajo y **no se necesita** para poblar el SMT-ONIC: el XLSX ya viene pre-filtrado por pertenencia étnica indígena, que es el subconjunto relevante para el sistema.

La subcarpeta `0001_UNIVERSO_VICTIMAS_LB_ANONIMO/` existe en el directorio de bases pero está vacía — el archivo TXT nunca fue descargado a este equipo.

---

## 3. Schema de BD destino

### 3.1 Tabla `victimas.universo`

Almacena una fila por registro de hecho victimizante (una persona puede tener múltiples hechos, por lo que el conteo de filas es mayor que el de personas únicas).

```sql
CREATE TABLE victimas.universo (
    id                      SERIAL PRIMARY KEY,
    idpersona               VARCHAR(20),       -- ← CONSPERSONA del XLSX
    idhogar                 VARCHAR(20),       -- ← IDHOGAR del XLSX
    pertenencia_etnica      VARCHAR(60),       -- ← PERTENENCIAETNICA normalizada
    genero                  VARCHAR(20),       -- ← GENERO del XLSX
    fecha_nacimiento        DATE,              -- ← FECHANACIMIENTO parseada
    hecho                   VARCHAR(200),      -- ← HECHO del XLSX
    fecha_ocurrencia        DATE,              -- ← FECHAOCURRENCIA parseada
    cod_mpio_ocurrencia     VARCHAR(5),        -- ← CODDANEMUNICIPIOOCURRENCIA padded a 5 dígitos
    cod_mpio_residencia     VARCHAR(5),        -- ← CODDANELLEGADA padded a 5 dígitos
    zona_ocurrencia         VARCHAR(30),       -- siempre NULL (no existe en XLSX indígena)
    presunto_actor          VARCHAR(100),      -- ← PRESUNTOACTOR del XLSX
    tipo_victima            VARCHAR(20),       -- ← TIPOVICTIMA del XLSX
    estado_victima          VARCHAR(30),       -- ← ESTADOVICTIMA del XLSX
    discapacidad            VARCHAR(5),        -- ← DISCAPACIDAD: '1' o '0'
    descripcion_discapacidad TEXT,             -- ← DESCRIPCIONDISCAPACIDAD (máx 500 chars)
    tipo_discapacidad_limpia VARCHAR(30),      -- clasificación canónica derivada en Python
    cod_pueblo_imputado     VARCHAR(3),        -- imputado desde pueblo.pueblo_dominante_mpio
    pueblo_imputado         VARCHAR(100),      -- imputado desde pueblo.pueblo_dominante_mpio
    confianza_imputacion    VARCHAR(10),       -- confianza del lookup (valor numérico como string)
    created_at              TIMESTAMPTZ DEFAULT NOW()
);
```

**Columnas del XLSX que no se cargan a BD y razón:**

| Columna XLSX | Razón de exclusión |
|---|---|
| `ZONAOCURRENCIA` | No existe en el XLSX línea base indígena (sí está en el TXT universo Colombia). La UI de `/conflicto` no la consume actualmente. Queda como NULL. |
| `CODDANEMUNIRESIDENCIA` | Ídem anterior: ausente en el XLSX indígena. El loader usa `CODDANELLEGADA` (municipio de llegada para desplazados) como proxy de residencia. |
| `PARAM_HECHO` | Código numérico del hecho según Ley 1448; redundante con la columna textual `HECHO`. No está en el schema BD porque el sistema trabaja con la descripción. |

Adicionalmente, columnas de identificación nominal (`PRIMERNOMBRE`, `SEGUNDONOMBRE`, `PRIMERAPELLIDO`, `SEGUNDOAPELLIDO`, `DOCUMENTO`, `TIPODOCUMENTO`) no se cargan por razones de privacidad y anonimización del set de datos entregado.

### 3.2 Tabla `victimas.resumen_pueblo_hecho`

Tabla de agregados pre-calculados para acelerar los endpoints de `/conflicto`. Se puebla con un `INSERT ... SELECT ... GROUP BY` al final de la carga principal, sin leer el XLSX de nuevo.

```sql
CREATE TABLE victimas.resumen_pueblo_hecho (
    id                  SERIAL PRIMARY KEY,
    cod_pueblo_imputado VARCHAR(3),
    pueblo_imputado     VARCHAR(100),
    hecho               VARCHAR(200),
    tipo_disc_limpia    VARCHAR(30),
    cod_dpto            VARCHAR(2),   -- primeros 2 dígitos de cod_mpio_ocurrencia
    cod_mpio            VARCHAR(5),   -- cod_mpio_ocurrencia de universo
    cantidad            INTEGER NOT NULL DEFAULT 0,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);
```

Solo incluye registros donde `pertenencia_etnica IN ('INDIGENA', 'INDIGENA ACREDITADO RA')` y `discapacidad = '1'` y `cod_pueblo_imputado IS NOT NULL`. Por eso la cifra es 6.329 filas (combinaciones pueblo × hecho × tipo_disc × municipio) aunque hay 37.191 víctimas con pueblo imputado.

---

## 4. Procedimiento de carga paso a paso

Ejecutar desde una terminal PowerShell con el entorno Python activo.

```powershell
# PASO 0 · Activar entorno virtual si aplica
# cd "C:\Users\wilso\Desktop\discapacidad\copia github"
# .venv\Scripts\Activate.ps1

# PASO 1 · Verificar que el XLSX canónico existe en su ruta
Test-Path "C:\Users\wilso\Desktop\discapacidad\Bases Uariv-20260506T040813Z-3-001\Bases Uariv\LB-Victimas -Unica\LB_UNIV_VICT_INDIGENA.xlsx"
# Debe retornar: True
# Si retorna False → el archivo fue movido; actualizar DEFAULT_FILE en load_victimas_xlsx.py

# PASO 2 · Verificar que el contenedor BD está corriendo
docker ps --filter name=smt-onic-db
# Debe mostrar la columna STATUS con "Up X hours/minutes"
# Si no aparece → docker compose up -d (desde la carpeta del repo)

# PASO 3 · Verificar que los catálogos pre-requisito están poblados
docker exec smt-onic-db psql -U smt_admin -d smt_onic -c "
SELECT 'pueblo.pueblo_dominante_mpio' AS tabla, COUNT(*) AS filas
FROM pueblo.pueblo_dominante_mpio
WHERE periodo = '2018'
UNION ALL
SELECT 'cat.pueblos_indigenas', COUNT(*)
FROM cat.pueblos_indigenas;
"
# Esperado: 969 + 120
# Si alguno tiene 0 → cargar primero esos catálogos antes de continuar

# PASO 4 · Ejecutar el loader
# Desde la raíz del repo (copia github/)
python backend/scripts/load_victimas_xlsx.py

# Salida esperada durante la carga:
#   Connected: localhost:5450/smt_onic
#   Tables ready · TRUNCATEd
#   Pueblo lookup: 969 municipios
#   Reading: C:\Users\wilso\Desktop\discapacidad\Bases Uariv-20260506T040813Z-3-001\...
#   Sheet: LB_UNIV_VICT_INDIGENA · Chunk: 200,000
#   Header: 35 cols (o el número que tenga la versión del XLSX)
#       200,000 rows (XXXX/s)
#       400,000 rows (XXXX/s)
#       600,000 rows (XXXX/s)
#       787,332 rows (XXXX/s)
#   Loaded: 787,332 rows in ~98.Xs
#   Building victimas.resumen_pueblo_hecho...
#   resumen_pueblo_hecho: 6,329 rows
#   Indígenas con discapacidad cargados: 37,562
#   Indígenas con disc Y pueblo imputado: 37,191
#   Total: ~98.Xs

# PASO 5 · Validación rápida post-carga
docker exec smt-onic-db psql -U smt_admin -d smt_onic -c "
SELECT COUNT(*) AS total_universo FROM victimas.universo;
"
# Esperado: 787332

docker exec smt-onic-db psql -U smt_admin -d smt_onic -c "
SELECT COUNT(*) AS con_discapacidad
FROM victimas.universo
WHERE discapacidad = '1';
"
# Esperado: 37562

docker exec smt-onic-db psql -U smt_admin -d smt_onic -c "
SELECT COUNT(*) AS resumen_rows FROM victimas.resumen_pueblo_hecho;
"
# Esperado: 6329
```

### 4.1 Opción con ruta alternativa al XLSX

Si el XLSX fue copiado a otra ubicación o se trabaja en un equipo diferente, pasar la ruta explícita:

```powershell
python backend/scripts/load_victimas_xlsx.py --file "D:\datos\LB_UNIV_VICT_INDIGENA.xlsx"
```

### 4.2 Opción con chunk size diferente

El chunk por defecto es 200.000 filas. En equipos con poca RAM puede reducirse; en equipos con mucha RAM puede aumentarse para acelerar:

```powershell
# Chunk conservador para equipos con 8 GB RAM
python backend/scripts/load_victimas_xlsx.py --chunk-size 50000

# Chunk agresivo para equipos con 32 GB+ RAM
python backend/scripts/load_victimas_xlsx.py --chunk-size 500000
```

### 4.3 Variable de entorno alternativa

El loader también acepta la ruta via variable de entorno, útil en despliegues CI:

```powershell
$env:VICTIMAS_XLSX = "D:\datos\LB_UNIV_VICT_INDIGENA.xlsx"
python backend/scripts/load_victimas_xlsx.py
```

---

## 5. Validación N1 → N2 → N4

### N1 · Base de datos

Consultas de regresión que deben ejecutarse después de cada carga para confirmar que los datos son los esperados.

```powershell
# Conteo total y por pertenencia étnica
docker exec smt-onic-db psql -U smt_admin -d smt_onic -c "
SELECT pertenencia_etnica, COUNT(*) AS filas
FROM victimas.universo
GROUP BY pertenencia_etnica
ORDER BY filas DESC;
"
# Referencia:
#  INDIGENA ACREDITADO RA  | 426122
#  INDIGENA                | 361210

# Distribución por hecho (top 5)
docker exec smt-onic-db psql -U smt_admin -d smt_onic -c "
SELECT hecho, COUNT(*) AS n,
       ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS pct
FROM victimas.universo
GROUP BY hecho
ORDER BY n DESC
LIMIT 5;
"
# El hecho principal debe ser Desplazamiento Forzado con ~76,4%

# Conteo por tipo de discapacidad (solo registros con disc=1)
docker exec smt-onic-db psql -U smt_admin -d smt_onic -c "
SELECT tipo_discapacidad_limpia, COUNT(*) AS n
FROM victimas.universo
WHERE discapacidad = '1'
GROUP BY tipo_discapacidad_limpia
ORDER BY n DESC;
"
# Cap. diversa más frecuente: FISICA con 6.675

# Pueblos distintos con al menos una víctima con discapacidad
docker exec smt-onic-db psql -U smt_admin -d smt_onic -c "
SELECT COUNT(DISTINCT pueblo_imputado) AS pueblos_afectados
FROM victimas.universo
WHERE discapacidad = '1'
  AND pueblo_imputado IS NOT NULL;
"
# Esperado: 73
```

### N2 · API REST

Con el backend corriendo (`uvicorn app.main:app --port 8000` o el comando equivalente del proyecto):

```powershell
# KPI principal: total víctimas con discapacidad
curl -s http://localhost:8000/conflicto/victimas/kpis | python -m json.tool
# Campo esperado: total_victimas = 37562

# Distribución por tipo de discapacidad
curl -s "http://localhost:8000/conflicto/victimas/discapacidad" | python -m json.tool
# Debe listar FISICA, VISUAL, AUDITIVA, INTELECTUAL, PSICOSOCIAL, MULTIPLE, SIN_INFORMACION

# Distribución por hecho victimizante
curl -s "http://localhost:8000/conflicto/victimas/hechos" | python -m json.tool
# Desplazamiento forzado debe aparecer primero con ~76,4%

# Top pueblos por número de víctimas con discapacidad
curl -s "http://localhost:8000/conflicto/victimas/pueblos" | python -m json.tool
# Debe retornar lista de 73 pueblos con cantidades
```

### N4 · Interfaz de usuario

En el navegador, navegar a `http://localhost:5173/conflicto` con credenciales de administrador.

**KPIs visibles en el dashboard que sirven como punto de control:**

| KPI en pantalla | Valor canónico |
|---|---|
| Total víctimas con discapacidad | 37.562 |
| Pueblos afectados | 73 |
| Hecho principal | Desplazamiento forzado 76,4 % |
| Capacidad diversa más frecuente | Física · 6.675 personas |

Si alguno de estos valores difiere del canónico, la carga tuvo un problema o los catálogos de pueblo no estaban completamente poblados antes de ejecutar el loader.

---

## 6. Decisiones de diseño justificadas

### B1 · Normalización defensiva de pertenencia étnica

El campo `PERTENENCIAETNICA` del XLSX puede venir con tildes (`'Indígena'`), con sufijos adicionales (`'INDIGENA-DESPLAZADO'`), o con formas no contempladas en el loader original. La función `normalize_etnia()` aplica dos reglas canónicas:

1. Si el string contiene `"ACREDITADO RA"` → `"INDIGENA ACREDITADO RA"`
2. Si el string es exactamente `"INDIGENA"` (normalizado sin tildes) → `"INDIGENA"`
3. Catch-all: si contiene `"INDIGENA"` pero no matchea las formas anteriores → `"INDIGENA"` (para evitar valores raros en BD)

Esto garantiza que la columna `pertenencia_etnica` en BD nunca acumule variantes ortográficas que rompan los filtros del backend.

### B2 · Mapping CONSPERSONA → idpersona

El TXT crudo del universo Colombia usa la columna `IDPERSONA` como identificador de persona. El XLSX línea base indígena usa `CONSPERSONA` según el diccionario oficial `VARIABLES UNIVERSO VICTIMAS LB.xlsx` (sección `universo_victimas_LB`, campo `CONSPERSONA: "Número Único del registro persona generado, que enlaza la BD con la tabla de personas"`).

Por esta razón, la columna `victimas.universo.idpersona` almacena el valor de `CONSPERSONA`. Cualquier JOIN futuro entre este dataset y el TXT universo completo debe hacerse con precaución: `CONSPERSONA` e `IDPERSONA` son semánticamente equivalentes pero pueden no coincidir en su espacio de valores para todos los registros. El diccionario UARIV es la fuente autoritativa.

### B3 · Validación de columnas críticas al inicio

Antes de procesar una sola fila de datos, el loader verifica que las siguientes columnas existan en el header del XLSX: `CONSPERSONA`, `PERTENENCIAETNICA`, `HECHO`, `FECHAOCURRENCIA`, `CODDANEMUNICIPIOOCURRENCIA`, `DISCAPACIDAD`, `DESCRIPCIONDISCAPACIDAD`. Si alguna falta, el script lanza `ValueError` con el detalle de qué columnas faltan y cuáles se encontraron. Esto protege contra cambios de schema en versiones futuras del XLSX UARIV.

### M1 · Criterio de clasificación MULTIPLE más permisivo

El loader original clasificaba `tipo_discapacidad_limpia` con criterios estrictos que dejaban sin clasificar combinaciones frecuentes como `'MULTIPLE (-Física-Intelectual)'`. La función `clean_tipo_discapacidad()` implementa una regla más permisiva: si el string contiene ≥ 2 indicadores de tipo distintos (de un vocabulario controlado de 14 keywords) o si contiene la palabra `"MULTIPLE"` explícitamente, se clasifica como `"MULTIPLE"`. Para strings con un solo tipo, aplica la jerarquía FISICA → VISUAL → AUDITIVA → INTELECTUAL → PSICOSOCIAL → SIN_INFORMACION.

### M2 · Filtro de fechas fantasma Excel

Las celdas de tipo fecha vacías en Excel se serializan como `1899-12-30` o `1900-01-01` por el motor de openpyxl. La función `to_date()` detecta y descarta estas fechas fantasma retornando `None`. Sin este fix, la BD acumularía miles de filas con fechas del siglo XIX que distorsionarían filtros y rangos temporales.

### M3 · Cast de confianza_imputacion a string

El campo de confianza del lookup de pueblo es numérico en la tabla `pueblo.pueblo_dominante_mpio` pero la columna destino en `victimas.universo` es `VARCHAR(10)`. Sin el cast explícito a string con formato `f"{valor:.4f}"[:10]`, psycopg2 podría fallar en la serialización o almacenar valores en notación científica. El cast garantiza formato consistente (`"0.8500"`, `"1.0000"`) independientemente del valor original.

### M5 · Cierre garantizado del workbook

`openpyxl.load_workbook()` en modo `read_only=True` abre un file handle al XLSX. Si el proceso falla en medio de la carga, ese handle queda abierto en Windows (que no permite borrar o mover el archivo mientras está bloqueado). El bloque `try/finally` garantiza que `wb.close()` se llame siempre, incluso si hay excepción durante la carga.

### Por qué imputación pueblo en memoria (no en query post-load)

Al cargar cada fila, se consulta un diccionario Python en memoria `{cod_mpio → (pueblo, cod_pueblo, confianza)}` precargado desde `pueblo.pueblo_dominante_mpio`. Esto es equivalente al comportamiento del loader original y evita ejecutar un `UPDATE victimas.universo SET pueblo_imputado = ...` separado después de la carga. La ventaja operativa es que la carga es atómica: cada fila entra completa (con pueblo imputado o sin él), sin estados intermedios.

### Por qué ZONAOCURRENCIA y CODDANEMUNIRESIDENCIA quedan NULL

Estas columnas existen en el schema de `victimas.universo` para mantener compatibilidad con el loader original (`load_victimas_indigenas.py`) que las leía del TXT crudo. El XLSX línea base indígena no incluye `ZONAOCURRENCIA` (el campo `ZONARESIDENCIA` está en la sección de personas, no de hechos) ni `CODDANEMUNICIPIORESIDENCIA` como tal (usa `CODDANELLEGADA` para desplazados). La UI del módulo `/conflicto` no consume estas columnas actualmente, por lo que su ausencia no afecta la funcionalidad.

---

## 7. Troubleshooting

### Error: `relation "victimas.universo" does not exist`

Las migraciones de schema no se han aplicado a la BD. Ejecutar:

```powershell
Get-Content "backend\sql\001_schema.sql" | docker exec -i smt-onic-db psql -U smt_admin -d smt_onic
```

Si hay múltiples archivos SQL de migración, aplicarlos en orden numérico. El loader también crea las tablas con `CREATE TABLE IF NOT EXISTS` si no existen, pero depende del schema `victimas` existiendo.

### Error: `connection refused` / `could not connect to server`

El contenedor Docker no está corriendo. Desde la carpeta del repositorio:

```powershell
docker compose up -d
# Esperar ~10 segundos y verificar
docker ps --filter name=smt-onic-db
```

Si el contenedor existe pero no inicia, revisar logs:

```powershell
docker logs smt-onic-db --tail 50
```

El puerto por defecto del contenedor es 5450 (no 5432). Verificar que `DATABASE_URL_SYNC` en el script apunta a `localhost:5450`.

### Error: `0 rows loaded` (sin error, pero conteo = 0)

El nombre del sheet en el XLSX cambió. El script busca exactamente `SHEET_NAME = "LB_UNIV_VICT_INDIGENA"`. Verificar el nombre real:

```powershell
python -c "
import openpyxl
wb = openpyxl.load_workbook(r'ruta\al\archivo.xlsx', read_only=True)
print(wb.sheetnames)
wb.close()
"
```

Si el nombre cambió en una versión nueva del XLSX, actualizar la constante `SHEET_NAME` en `load_victimas_xlsx.py`.

### Error: `pueblo_imputado todos NULL` (o muy pocos imputados)

El catálogo `pueblo.pueblo_dominante_mpio` estaba vacío o incompleto cuando se ejecutó el loader. La función `load_pueblo_lookup()` imprime `Pueblo lookup: N municipios` al inicio; si N es 0, el problema es ese catálogo.

```powershell
# Verificar
docker exec smt-onic-db psql -U smt_admin -d smt_onic -c "
SELECT COUNT(*) FROM pueblo.pueblo_dominante_mpio WHERE periodo = '2018';
"
# Si retorna 0 → cargar el catálogo primero, luego re-ejecutar el loader
```

Re-ejecutar el loader después de poblar el catálogo (el loader hace TRUNCATE al inicio, por lo que no hay riesgo de duplicados).

### Error: `ValueError: XLSX header falta columnas criticas`

El mensaje incluye la lista de columnas que faltan y las que se encontraron. Causas comunes:

- Se pasó un archivo XLSX diferente (ej. una de las copias `.xls` renombradas).
- La UARIV publicó una versión nueva del XLSX con nombres de columnas cambiados.
- El archivo está corrupto. Verificar con `Test-Path` y tamaño de archivo (`(Get-Item archivo.xlsx).Length` debe ser ~133 MB).

### Error de memoria durante la carga

```powershell
MemoryError
```

Reducir el chunk size:

```powershell
python backend/scripts/load_victimas_xlsx.py --chunk-size 50000
```

En Windows, `openpyxl` en modo `read_only=True` carga el XLSX en streaming, lo que mantiene el uso de memoria bajo; el principal consumidor es el chunk acumulado antes de cada `INSERT`. Con chunks de 50.000 el pico de RAM es aproximadamente 500 MB.

---

## 8. Próximos pasos / backlog

### K02 · Carga de `ext.ruv_hechos_municipal` (pendiente)

Script de carga pendiente para el CSV agregado de hechos municipales del RUV (~15 MB). Esta tabla alimenta los endpoints "zombie" del módulo `/conflicto` que actualmente retornan arrays vacíos. El CSV tiene schema diferente al XLSX indígena: columnas de código municipal, año, tipo de hecho y conteo. La carga es directa con `COPY` o `psycopg2.copy_from()`.

### Imputación estadística RUV × pueblo en `imp.ruv_pueblo`

La tabla `imp.ruv_pueblo` no tiene ETL implementado. El objetivo es distribuir los hechos del RUV municipal (que no tiene pertenencia étnica) a pueblos indígenas usando la probabilidad de presencia de cada pueblo en cada municipio. Esto requiere un modelo de imputación probabilística que está en el backlog del sprint S4.

### Actualización cuando UARIV publique línea base 2025

La línea base actual es de corte 2021. Cuando la UARIV publique la línea base 2025, el procedimiento de actualización es:

1. Verificar que el XLSX nuevo mantiene el schema de 35 columnas (el fix B3 detectará cualquier cambio).
2. Si el schema no cambió: re-ejecutar `load_victimas_xlsx.py` con la nueva ruta. La carga tarda ~98 segundos y es idempotente.
3. Si el schema cambió: revisar el diccionario oficial nuevo, actualizar `EXPECTED_HEADER` y `REQUIRED_COLUMNS` en el script, y probar en un entorno de staging antes de producción.
4. Comparar las cifras canónicas post-carga con los valores de la línea base 2021 para detectar variaciones significativas.

### Índices de rendimiento (recomendado antes de producción)

La tabla `victimas.universo` no tiene índices más allá del `id` serial. Para acelerar los queries del backend en entornos con carga real:

```sql
-- Índice para filtros por discapacidad y pueblo (query más frecuente)
CREATE INDEX idx_universo_disc_pueblo
    ON victimas.universo (discapacidad, pueblo_imputado)
    WHERE discapacidad = '1';

-- Índice para filtros por hecho victimizante
CREATE INDEX idx_universo_hecho ON victimas.universo (hecho);

-- Índice para filtros por municipio
CREATE INDEX idx_universo_mpio ON victimas.universo (cod_mpio_ocurrencia);
```

Estos índices no son necesarios para el desarrollo actual (la BD tiene acceso local y el volumen de queries es bajo), pero se incluyen como referencia para cuando el sistema escale a un entorno de producción real.

---

*Documento generado el 2026-05-06. Cifras verificadas contra BD en la misma fecha.*  
*Firma Wilson — pendiente.*
