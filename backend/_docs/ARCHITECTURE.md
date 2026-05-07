# Arquitectura · SMT-ONIC v1.0

## Visión general

Sistema de tres capas con base PostGIS, API REST en FastAPI y SPA en React, todo orquestado con Docker Compose. Diseñado para correr en una sola VM de 4 vCPU / 8 GB RAM.

```
┌──────────────────────────────────────────────────────┐
│  Navegador (HTTPS)                                   │
│  └─→ nginx (TLS · 80/443)                            │
│        ├─→ /api/  → FastAPI :8095                    │
│        └─→ /     → frontend dist (SPA)               │
└──────────────────────────────────────────────────────┘
                        │
       ┌────────────────┴───────────────────┐
       ▼                                    ▼
┌──────────────┐                    ┌──────────────────┐
│ FastAPI      │  asyncpg           │ PostgreSQL 16    │
│ (uvicorn)    │ ────────────────→  │ + PostGIS 3.4    │
│ - 11 routers │                    │ - 16 schemas     │
│ - JWT auth   │                    │ - 438K filas     │
└──────────────┘                    └──────────────────┘
```

## Capas

| Capa | Tecnología | Puerto | Responsabilidad |
|---|---|---|---|
| Frontend | React 18 + Vite + Recharts + Leaflet + Tailwind | 5174 (dev) / 80 (prod) | Dashboard institucional, 12 páginas, mapas interactivos |
| Backend | FastAPI 0.110 + SQLAlchemy 2.x async + Python 3.12 | 8095 | API REST, autenticación JWT, generación de informes |
| Base | PostgreSQL 16 + PostGIS 3.4 | 5450 | Persistencia analítica + geometrías oficiales |
| Reverse proxy | nginx + Let's Encrypt | 80/443 | TLS, routing, frontend estático |

## Esquemas de base de datos

| Schema | Contenido |
|---|---|
| `cnpv` | Microdatos consolidados CNPV 2018 (438 K filas) |
| `pueblo` | Catálogo de 115 pueblos indígenas + perfiles |
| `geo` | Geometrías DANE (33 dptos · 1.122 mpios) |
| `smt_geo` | Geodatabase ONIC (5 macrorregiones · 830 resguardos · 13.868 comunidades) |
| `visor_dane` | Pirámides poblacionales (CNPV + CG 2005) |
| `proyecciones` | FAC intercensal + 832 escenarios Lee-Carter |
| `indicadores` | 25 definiciones canónicas + ICV ponderado |
| `victimas` | RUV anonimizado cruzado con capacidades diversas |
| `smt` | Usuarios, sesiones, formulario de captura |
| `ext` | Datos auxiliares externos |
| `imp` | Tablas de importación |
| `cat` | Catálogos compartidos |
| `tiger`, `tiger_data`, `topology` | Extensiones PostGIS |
| `public` | spatial_ref_sys |

## Routers de la API (`/api/v1/...`)

1. `auth` — login, refresh, gestión de sesión JWT
2. `dashboard` — resumen nacional, prevalencia, proyecciones, brecha
3. `pueblos` — catálogo, perfiles, pirámides
4. `demografia` — pirámides nacionales, NBI, lengua
5. `geo` — departamentos, municipios, resguardos, comunidades
6. `indicadores` — definiciones e ICV territorial
7. `conflicto` — víctimas RUV cruzadas con capacidades diversas
8. `informes` — 5 niveles · HTML / DOCX / PDF
9. `formulario` — captura primaria desde territorios

## Autenticación

- Esquema: JWT Bearer (`Authorization: Bearer <token>`).
- Tokens: 64 chars URL-safe, vida útil 12 h (configurable en `auth.py`).
- Hash de password: SHA-256 con salt aleatorio de 16 bytes.
- Almacenamiento: `smt.usuarios` (3 roles: `admin`, `coordinador`, `dinamizador`).
- Detalle: `_docs/MATRIZ_AUTH_v1.md`.

## Volumen de datos en producción

| Tabla | Filas | Función |
|---|---|---|
| `cnpv.resumen_nacional_etnico` | 8 | Resumen por grupo étnico |
| `pueblo.disc_nacional` | 120+ | Pueblos con capacidades diversas |
| `pueblo.piramide_disc` | 2.406 | Pirámide nacional capacidades diversas |
| `visor_dane.piramide_pueblo` | 7.802 | Pirámides por pueblo |
| `smt_geo.resguardos` | 830 | Resguardos titulados |
| `smt_geo.macrorregiones` | 5 | Macrorregiones ONIC |
| `proyecciones.escenarios` | 832 | 8 grupos × 4 esc × 26 años |
| `proyecciones.fac` | 8 | Factores de ajuste intercensal |
| `indicadores.definiciones` | 25 | Indicadores canónicos |
| `smt.resumen` | 40 | Resumen SMT consolidado |

## Flujo de informes territoriales

```
[Selector frontend]
   │  ↓ tipo + id
[GET /api/v1/informes/<tipo>/<id>]
   │  ↓
[backend/_static/informes/<tipo>/<id>.html] ← HTML pre-renderizado
        │              .json                ← JSON canónico extraído
        │              .llm.json            ← Análisis textual
        ↓
[Frontend muestra HTML]
   │
   ↓ usuario solicita Word/PDF
[GET .../docx | .../pdf]
   │  ↓
[Lazy gen: build_docx() o WeasyPrint]
   │  ↓
[Cache en backend/_static/informes/<tipo>/<id>.docx | .pdf]
```

## Despliegue

- Orquestación: `docker compose --env-file .env.prod up -d`
- Script automatizado: `infra/deploy_servidor_onic.sh`
- Verificación: `infra/smoke_tests.sh`
- Backup diario: `infra/backup_db.sh` (cron 03:00 hora Bogotá)

## Decisiones canónicas

- **D1 · 115 pueblos** (DANE CNPV 2018) · ver `_docs/DECISION_PUEBLOS_CANONICOS.md`
- **FAC** · `_docs/METODO_FAC_v1.md`
- **Proyecciones Lee-Carter** · `_docs/METODO_PROYECCIONES_v1.md`
- **ICV ponderado** · `_docs/METODO_ICV_v1.md`
- **Triangulación CNPV/RLCPD/SMT** · `_docs/METODO_TRIANGULACION_v1.md`

---

© EtniConsulting SAS — 2026
