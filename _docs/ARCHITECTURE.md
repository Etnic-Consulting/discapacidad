# Arquitectura · SMT-ONIC v1.4.1

**Audiencia**: ingeniería ONIC + cualquier desarrollador que necesite operar, debuggear o extender el sistema.
**Última actualización**: 2026-05-10 · post sprint S9_render_multinivel.

---

## §1 · Topología de 3 capas

```text
┌─────────────────────────────────────────────────────────────────┐
│  Internet → smt-onic.com (DNS A record → IP servidor)          │
└─────────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│  Capa 1 · Nginx (puerto 80 → 443 TLS via Let's Encrypt)         │
│  - Sirve frontend estático /var/www/smt-onic-frontend           │
│  - Reverse proxy a backend → http://localhost:8095              │
│  - Rate limit /auth/login (5 req/min/IP)                        │
│  - Config: /etc/nginx/sites-available/smt-onic                  │
└─────────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│  Capa 2 · FastAPI (Uvicorn · contenedor smt-onic-api · 8095)    │
│  - Routers en backend/app/routers/                              │
│  - Auth JWT (HTTPBearer · 24h expiry)                           │
│  - Sirve también /_static/informes/ (HTMLs + JSON pre-rendered) │
│  - Logs estructurados JSON a stdout                             │
└─────────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│  Capa 3 · PostGIS (contenedor smt-onic-db · 5432 interno)       │
│  - PostgreSQL 16 + extensión PostGIS                            │
│  - Datos crudos CNPV 2018 + agregaciones + geometrías           │
│  - Volumen Docker persistente: pgdata                           │
│  - Solo accesible desde smt-onic-api (no expuesto a Internet)   │
└─────────────────────────────────────────────────────────────────┘
```

**Stack canónico**:

| Capa | Tecnología | Puerto interno | Puerto público |
|---|---|---|---|
| Frontend | Vite + React 18 + Recharts | (estático) | 443 (via nginx) |
| API | FastAPI + Pydantic v2 + SQLAlchemy 2 | 8095 | 443 (via nginx /api) |
| DB | PostgreSQL 16 + PostGIS 3 | 5432 | (no expuesto) |
| Proxy | Nginx 1.24 + certbot (Let's Encrypt) | 80, 443 | 80, 443 |

---

## §2 · Volúmenes Docker

Definidos en `docker-compose.prod.yml`:

| Volumen | Mount point | Propósito | Tamaño aprox |
|---|---|---|---|
| `pgdata` | `/var/lib/postgresql/data` (db) | Datos persistentes Postgres | ~2 GB con índices |
| `_static_informes` | `/app/backend/_static/informes` (api) | 2.127 informes JSON+HTML pre-rendered | ~80 MB |
| `bd_consolidada` | `/data/discapacidad/bd_consolidada` (api, read-only) | CSVs corpus inicial · solo lectura | ~500 MB |
| `logs` | `/var/log/smt-onic` (api) | Logs estructurados | rotación logrotate |
| `backups` | `/opt/smt-onic/backups` (host) | pg_dump diarios rotación 7d | ~1.5 GB |

---

## §3 · Schemas PostgreSQL (10 schemas activos)

Listar con `\dn` en psql:

| Schema | Propósito | Tablas clave |
|---|---|---|
| `cnpv` | Censo Nacional de Población y Vivienda 2018 (oficial DANE) | `prevalencia_etnia_dpto` · `disc_indigena_mpio` · `disc_edad_dpto` · `disc_sexo_dpto` · `causa_disc_etnia_dpto` · `resumen_nacional_etnico` |
| `pueblo` | Agregaciones por pueblo indígena | `disc_nacional` · `disc_dpto` · `pueblo_municipio` · `piramide_disc` · `piramide_disc_tipo` |
| `geo` | Geometrías administrativas (DANE) | `departamentos` · `municipios` (1.122) · `macro_dptos` · `resguardos` · `resguardo_municipio` |
| `smt_geo` | Geometrías macrorregionales y resguardos ONIC | `macrorregiones` (5) · `resguardos` (830 ONIC) |
| `indicadores` | Definiciones + datos derivados | `definiciones` (12) · `icv_municipal` · `triangulacion_registro` |
| `proyecciones` | Cohortes poblacionales proyectadas (Lee-Carter aprox) | `fac` (8) · `escenarios` (832) |
| `victimas` | Conflicto armado (registro RUV cruzado) | tablas por hecho victimizante |
| `visor_dane` | Cruce visor étnico DANE | `resguardo_pueblo` (mapping pueblo-territorio) |
| `smt` | Sistema de Monitoreo Territorial (formularios ONIC) | `respuestas_formulario` · `caracterizacion` · `smt_resumen` (vista materializada · seed 012) |
| `ext` | Tablas externas auxiliares | varias |

**Schema base**: `backend/sql/001_schema.sql` (33 KB · crea todos los schemas y tablas).

---

## §4 · Flujo de datos · de REDATAM a la UI

```text
REDATAM CNPV 2018 (DANE)
        ↓ [extracción manual offline · acceso DANE requerido]
bd_consolidada/*.csv (corpus entregado por Wilson · tar.gz checksum SHA256)
        ↓ [./infra/init_db.sh + scripts.load_all.py]
PostgreSQL · schemas cnpv, pueblo, geo, smt_geo
        ↓ [seeds 002-013 idempotentes · backend/sql/]
PostgreSQL hidratado (~1.83M indígenas nacional · validado por sanity 7b)
        ↓ [python -m backend.scripts.render_informes --nivel todos]
backend/_static/informes/{tipo}/{id}.{json,html}
2.127 informes pre-renderizados (5 macro · 33 dpto · 1.122 mpio · 137 pueblo · 830 resguardo)
        ↓ [FastAPI router informes.py sirve /_catalog y /{id}]
HTTP GET /api/v1/informes/{tipo}/{id} → JSON canonical o HTML
        ↓ [Vite frontend InformesPageV2.jsx consume catálogo y muestra iframe]
Usuario final ve informe en https://smt-onic.com/informes
```

**Punto de quiebre del flujo**: si los seeds 010-013 no se aplican, las agregaciones nacionales quedan mal asignadas (~3.7M en vez de ~1.83M). El sanity check 7b en `init_db.sh` detecta esto y falla rápido.

**Punto de drift heredado**: tabla `pueblo.disc_dpto` mezcla pertenencias étnicas (afros + sin-pertenencia + indígenas) sin columna `grupo_etnico` filtrable. La suma nacional vía dpto da ~2.78M (vs ~1.83M canónico). Documentado en `_doctrina/LECCIONES.md` Caso 11 (Visual_Agentes) · hook `verificar_universo_poblacional.py` lo dispara si flota a UI con umbral >2M. Sprint S10 futuro · requiere re-extracción REDATAM.

---

## §5 · Flujo auth JWT

```text
1. Frontend POST /auth/login con {username, password}
   ↓
2. Backend verifica bcrypt hash en tabla smt.users · si OK firma JWT
   ↓
3. Backend retorna {access_token, token_type:"bearer", expires_in:86400}
   ↓
4. Frontend guarda token en localStorage · agrega header Authorization en cada request
   ↓
5. Endpoints con Depends(get_current_user) verifican firma + expiry
   ↓
6. Token expira en 24h · frontend hace re-login (no hay refresh tokens v1)
```

**Endpoints públicos vs auth**: ver `_docs/MATRIZ_AUTH_v1.md`.

**Smoke test**: `./infra/smoke_tests.sh` test 6 valida que `/pueblos/` sin token retorna 401 (auth cerrada correctamente).

---

## §6 · Pipeline de informes pre-renderizados

El sistema **NO** genera informes en runtime. Todos los informes (`backend/_static/informes/{tipo}/{id}.{json,html}`) se generan **offline** y se sirven estáticamente. Esto:

- Hace la API trivialmente rápida (lectura archivo · no query DB por request)
- Permite distribución offline (los HTMLs no tienen links absolutos a localhost)
- Garantiza determinismo · misma cifra cada visita (no cambia hasta siguiente render)

**Para regenerar**: corre `python -m backend.scripts.render_informes --nivel todos` (toma ~5 min · query DB + Python puro · cero LLM). Audit post con `python -m backend.scripts.audit_informes` valida cells_dash_pct < 5%.

**Después de regenerar**: ejecutar `python -m backend.scripts.manifest_informes` para reconstruir `MANIFEST.json` (catálogo global que consume el frontend).

**Generador**:

```python
RENDERERS = {
    "macro": render_macro,        # 5 informes · pueblo.disc_dpto agregado por macrorregión
    "dpto": render_dpto,          # 33 informes · pueblo.disc_dpto por dpto
    "mpio": render_mpio,          # 1.122 informes · cnpv.disc_indigena_mpio + smt_geo.resguardos
    "pueblo": render_pueblo,      # 137 informes · pueblo.disc_nacional + pueblo.piramide_disc
    "resguardo": render_resguardo, # 830 informes · smt_geo.resguardos + visor_dane.resguardo_pueblo
}
```

Cada renderer produce:
- `{id}.json` · estructura canonical con `_meta` trazable, `_input_hash` SHA256[:16], k-anonimato HONESTO
- `{id}.html` · render visual con CSS verde institucional `#02432D`

**Sin LLM en pipeline**: el render es Python puro determinístico. La prosa institucional opcional (`{id}.llm.json`) la genera por separado `rerender_flagged_informes.py` con plantillas template-Python (sin LLM externo). Esto cumple regla #1 (cero `import anthropic`/`openai`/`google.generativeai`).

---

## §7 · Observabilidad

**v1.4.x · observabilidad básica**:

- **Logs estructurados JSON** a stdout · captados por `docker logs` y `journald`
- **Logrotate** diario · retención 14d
- **Backup cron** diario 03:00 hora Bogotá · `infra/backup_db.sh` pg_dump → `/opt/smt-onic/backups/` + S3/GCS opcional
- **Healthcheck Docker** · `/api/v1/health` debe retornar 200
- **Smoke tests** · `./infra/smoke_tests.sh` corre 7 tests + 3 smoke informes nuevos · debe retornar 7/7 + 3/3

**v1.5+ · diferido a sprint observabilidad** (no requerido go-live v1.4):

- Sentry/Datadog/New Relic para errors + traces
- Glitchtip auto-hosted como alternativa libre
- Grafana + Prometheus para métricas
- Alertmanager para PagerDuty/Slack

---

## §8 · Decisiones arquitectónicas notables

1. **Pre-renderizado offline vs runtime**: elegido por simplicidad operativa + determinismo + zero-cost serving. Trade-off: cada vez que cambia la DB hay que re-correr `render_informes --nivel todos`.
2. **k-anonimato HONESTO**: badge `n<30` solo si la cifra agregada es realmente <30 (no badge falso). Decisión doctrinal · evita engañar al lector.
3. **Cero LLM en pipeline de datos**: regla #1 estricta. La prosa institucional usa plantillas template-Python deterministas.
4. **JWT 24h sin refresh tokens**: simplicidad v1 · acepta re-login diario. v1.5+ evaluar refresh.
5. **Volumen Docker para `_static/informes`**: permite que el render offline (host) y la API (contenedor) compartan el mismo directorio sin copias.
6. **PostGIS en mismo contenedor que Postgres**: simplifica deploy · ONIC puede separar a managed PostgreSQL en v1.5+ si necesita escalar.
7. **Informes huérfanos con `_sin_datos:true`**: en lugar de omitir IDs sin datos CNPV, generamos informe explícito con flag honesto. Frontend renderiza nota "sin datos disponibles" en lugar de 404.

---

## §9 · Cross-references

| Documento | Propósito |
|---|---|
| `INSTRUCCIONES_INGENIERIA_ONIC.md` | Guía de deploy paso a paso (este doc es referencia de arquitectura) |
| `DEPLOY_PRODUCCION.md` | Detalle profundo de deploy + troubleshooting |
| `_docs/MATRIZ_AUTH_v1.md` | Endpoints públicos vs auth vs admin |
| `_docs/RUNBOOK_INCIDENTES.md` | 10 incidentes típicos con diagnóstico + acción |
| `_docs/CHECKLIST_GO_LIVE.md` | 40 items binarios pre-go-live |
| `_docs/METODO_FAC_v1.md` | Metodología FAC (cómo se calcula 0.939) |
| `_docs/METODO_PROYECCIONES_v1.md` | Lee-Carter aproximada (bandas IC ±15%) |
| `_docs/DECISION_PUEBLOS_CANONICOS.md` | D1 = 115 pueblos (por qué no 121 ni 102) |
| `_doctrina/LECCIONES.md` (Visual_Agentes) | Lecciones técnicas del motor · Caso 11 = drift universo |

---

## §10 · Contactos

- **Director del proyecto**: Wilson Herrera Quiroga · `poblacion@onic.org.co`
- **Repositorio**: https://github.com/Etnic-Consulting/discapacidad · rama `restore/v2-styling`
- **Tag estable**: `v1.4.1` (este doc) · `v1.4.0` (sprint S9 base)
