# SMT-ONIC · wilson-version · Contexto de despliegue

## Qué es este proyecto

Sistema de Monitoreo Territorial (SMT) de la ONIC (Organización Nacional Indígena de Colombia).
Módulo: Capacidades Diversas (término preferido por ONIC en lugar de "discapacidad").
Versión: **v1.4.1** — rama `restore/v2-styling` — autor Wilson Herrera (Etnic Consulting).

Este repositorio es la versión de producción entregada por Wilson. Es independiente del proyecto
original en `../discapacidad/` (rama main), que es una versión anterior e incompleta.

## Stack técnico

- **DB**: PostgreSQL 16 + PostGIS 3.4 (Docker, puerto 5450)
- **API**: FastAPI + SQLAlchemy async + asyncpg (Python 3.12, puerto 8095 externo → 8000 interno)
- **Frontend**: React 18 + Vite + Recharts + Leaflet (puerto 5173/5174)
- **Auth**: JWT con sha256(salt+password), tabla `smt.usuarios`

## Estado local actual (validado 2026-05-14)

- ✅ Smoke tests: 7/7 passing (`infra/smoke_tests.sh http://localhost:8095`)
- ✅ DB cargada: 1,834,833 personas indígenas (CNPV 2018), 111 pueblos, seeds 001–013
- ✅ Login JWT funcionando
- ✅ Fix Cumaribo/Vichada aplicado (seeds 010-011 post load_all.py)
- ✅ `cnpv.comparacion_intercensal` creada y cargada (16 filas)
- ✅ `pueblo.piramide_disc`, `pueblo.piramide_disc_tipo`, `smt.resumen` creadas (estructuras vacías)
- ✅ `smt.usuarios` poblada con 3 usuarios seed

## Cómo levantar en local

```bash
# Desde esta carpeta
docker compose up -d

# El volumen wilson-version_pgdata ya tiene todos los datos cargados
# No se necesita re-ejecutar init_db.sh ni load_all.py

# Frontend (terminal separada)
cd frontend
npm run dev
# → http://localhost:5173 (o 5174 si 5173 está ocupado)
```

## Credenciales locales de prueba

| Usuario | Contraseña | Rol |
|---|---|---|
| wilson | wilson2026 | coordinador |
| admin | admin123 | admin |
| dinamizador1 | smt2026 | dinamizador |

El archivo `backend/.seed_credentials.txt` contiene estas mismas credenciales para los smoke tests.

## Fixes aplicados durante el setup local

### 1. `seed_auth.py` — contraseña hardcodeada
**Archivo**: `backend/scripts/seed_auth.py` línea 12
**Problema**: Tenía `smt_onic_2026` hardcodeado en lugar de leer la env var.
**Fix**: Lee `DATABASE_URL_SYNC` desde `os.environ.get(...)`.

### 2. `main.py` — health check cascade + tablas opcionales
**Archivo**: `backend/app/main.py` función `health()`
**Problema**: Un `UndefinedTableError` en asyncpg ponía toda la transacción en estado fallido
(InFailedSqlTransaction), haciendo que todos los checks siguientes fallaran en cascada.
**Fix**:
- `await db.rollback()` en el bloque `except` de cada check.
- Tablas separadas en `critica=True/False`: las opcionales (REDATAM, shapefiles, SMT forms)
  no degradan el `status` global.

### 3. `docker-compose.yml` — rutas hardcodeadas de Wilson
**Problema**: Los volúmenes de datos apuntaban a `D:\1.Programacion\...` (máquina de Wilson).
**Fix**: Cambiado a `${DISCAPACIDAD_DIR:-./data/discapacidad}` con `.env` local.

### 4. `backend/.seed_credentials.txt`
Copiado desde `../anexos_discapacidad/seed_credentials.txt` y actualizado con password dev.

## Tablas faltantes (creadas manualmente, sin datos REDATAM)

Estas tablas existen en el schema pero están **vacías** — no bloquean el sistema:
- `pueblo.piramide_disc` — requiere scraper REDATAM (`scripts/extraer_piramide_disc_pueblo.py`)
- `pueblo.piramide_disc_tipo` — requiere scraper REDATAM
- `smt.resumen` — se llena automáticamente con datos del formulario SMT (trigger)
- `smt_geo.resguardos` — requiere shapefiles GDB/Shapefile (no incluidos en corpus)
- `smt_geo.macrorregiones` — requiere shapefiles

## Corpus de datos

Ubicación: `C:\Proyectos\ONIC\SMT\2026\Avances SMT\anexos_discapacidad\`

Archivos clave:
- `bd_consolidada.tar.gz` — datos CNPV 2018 (SHA256: `3db8c000b12648d74046eb16099ddff393fca28da3d9af4c3994ee59ff8ef9ea`)
- `bd_consolidada/` — ya extraído, 40+ CSVs
- `seed_credentials.txt` — credenciales originales de Wilson (producción)

## Próximo paso: Digital Ocean

Ver `DEPLOY_PRODUCCION.md` en esta misma carpeta.
Pasos pendientes:
1. Provisionar Droplet (Ubuntu 22.04, 4GB RAM mínimo)
2. Configurar DNS para dominio ONIC
3. Ejecutar `infra/deploy_servidor_onic.sh` en el servidor
4. Configurar nginx + TLS (Let's Encrypt)
5. Generar secretos de producción: `openssl rand -hex 32` para JWT_SECRET
6. Ejecutar `infra/init_db.sh` en producción con URL_DATA del corpus
7. Configurar backup cron

## Bug crítico conocido: Cumaribo/Vichada

Al cargar datos CNPV con `load_all.py`, el total nacional indígena queda en ~3.7M en lugar
de ~1.83M porque Cumaribo (municipio 99773) concentra todos los registros nacionales.

**Solución**: Después de `load_all.py`, re-aplicar en orden:
```bash
docker exec -i smt-onic-db psql -U smt_admin -d smt_onic < backend/sql/010_fix_seed_99773_agregado_nacional.sql
docker exec -i smt-onic-db psql -U smt_admin -d smt_onic < backend/sql/011_fix_dpto_99_agregados_nacionales.sql
```
Verificación: `SELECT SUM(pob_total) FROM cnpv.prevalencia_etnia_dpto WHERE grupo_etnico='Indigena' AND periodo='2018';`
Debe retornar ~1,834,833.
