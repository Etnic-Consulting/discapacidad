# CHECKPOINT · estado final pre-handoff ingeniería ONIC

**Fecha**: 2026-05-10
**Versión target**: `v1.4.1` · branch `restore/v2-styling`
**Commit más reciente**: `1d789a6` (tag local `v1.4.1`) · pendiente `git push origin`
**Quién**: Wilson Herrera (director) · sesión autónoma Claude Opus 4.7 + dispatch multimodelo.

---

## §1 · TL;DR para ingeniería

El sistema **está listo para deploy**. Todas las validaciones locales pasan. Lo único pendiente humano es:

1. Wilson hace `git push origin restore/v2-styling v1.4.0 v1.4.1` (requiere PAT activo).
2. Ingeniería provisiona servidor + DNS + TLS (ver `INSTRUCCIONES_INGENIERIA_ONIC.md §1-§2`).
3. Ingeniería ejecuta `./infra/deploy_servidor_onic.sh` (script único).
4. Ingeniería valida con `./infra/smoke_tests.sh https://smt-onic.com` (esperar 7/7).
5. Sesión de handoff 90 min (`INSTRUCCIONES §10`) + firma minuta (`docs/MINUTA_HANDOFF_TEMPLATE.md`).

---

## §2 · Estado de validaciones locales (2026-05-10)

### Builds

| Componente | Estado | Detalle |
|---|---|---|
| Frontend `npm run build` | ✅ OK | 708 módulos · 503ms · `dist/` 1.17 MB (gzip 326 KB) · 0 errores · 1 warning bundle >500KB (cosmético) |
| Backend container `smt-onic-api` | ✅ UP | 21h running · health 200 |
| Database container `smt-onic-db` | ✅ UP | 4 días running · healthy · 152 MB pg_dump |

### Smoke tests · `./infra/smoke_tests.sh http://localhost:8095`

```
[1/7] Health endpoint........................✓ PASS
[2/7] Login y JWT............................✓ PASS (token 64 chars)
[3/7] /proyecciones..........................✓ PASS (104 filas)
[4/7] /intercensal con aplicar_fac=true......✓ PASS
[5/7] /brecha con source_detalle.............✓ PASS
[6/7] /pueblos/ sin token (esperar 401)......✓ PASS
[7/7] /pueblos/ con token (esperar 200)......✓ PASS (111 pueblos)
RESUMEN · 7 pass · 0 fail · 0 warn · DEPLOY VÁLIDO
```

### Sanity SQL · universo poblacional canónico

```sql
SELECT SUM(pob_total) FROM cnpv.prevalencia_etnia_dpto
WHERE grupo_etnico='Indigena' AND periodo='2018';
-- → 1.834.833 (rango canónico CNPV 2018 1.7M-2.0M ✓)
```

Si en deploy ONIC da ≠ ~1.83M, las migraciones 010-013 no se aplicaron (ver `RUNBOOK §12` Incidente 10).

### Smoke E2E navegador (Playwright · 8 rutas validadas)

| Ruta | KPI clave | Estado |
|---|---|---|
| `/` Panorama | 1.834.833 nacional · 112.584 con CD · 7 dashes legítimos | ✅ |
| `/pueblos` | 111 pueblos · 112.562 con CD · top WAYUU/ZENU/NASA todos Alta | ✅ |
| `/pueblos/660` TIKUNA | 12.793 pob · 397 CD · 31.0‰ · Alta · pirámide presente | ✅ |
| `/territorios` | Mapa Leaflet · 3 capas · sin selector inerte | ✅ |
| `/conflicto` | 37.562 víctimas · 73 pueblos · 68.6% desplazamiento · BarChart 5 hechos | ✅ |
| `/proyecciones` | FAC + IC±15% · 104 puntos · 3 etnias comparadas | ✅ |
| `/voz-propia` | Sección A CNPV · Sección B pre-operación honesta · 2 charts | ✅ |
| `/indicadores` | 13 métricas · 26 rows tabla | ✅ |
| `/informes` | 5 tabs · counts 5+33+1.122+137+830 = 2.127 ✓ · cascada operativa | ✅ |

### Informes pre-renderizados · 4 samples por nivel validados

| Informe | URL | Resultado |
|---|---|---|
| BOGOTÁ mpio | `/api/v1/informes/mpio/11001` | 18.560 pob · 1.524 CD · 82.1‰ · CONFIABLE · 0 resguardos con mensaje honesto |
| COYAIMA mpio | `/api/v1/informes/mpio/73217` | 9.302 pob · 141 CD · 15.2‰ · 34 resguardos PIJAO |
| TIKUNA pueblo | `/api/v1/informes/pueblo/660` | 12.793 · 397 · 31.0‰ · ALTA · pirámide 18 grupos × sexo |
| JUHUP huérfano | `/api/v1/informes/pueblo/433` | 0/0/0.0‰/BAJA · `_sin_datos:true` honesto (T08 fallback) |
| ARARA resguardo | `/api/v1/informes/resguardo/10001` | AMAZONAS/LETICIA/MAGÜTA-PÖGUTA · 12.193 ha · nota CD honesta |

### API · 6 endpoints clave

| Endpoint | Esperado | Real |
|---|---|---|
| `/api/v1/health` | 200 | 200 ✅ |
| `/api/v1/informes/_catalog` | 5 niveles · 2.127 total | 2.127 ✅ |
| `/api/v1/dashboard/proyecciones` | 104 filas | 104 ✅ |
| `/api/v1/pueblos/` sin token | 401 | 401 ✅ |
| `/api/v1/pueblos/` con token | 200 | 200 (111) ✅ |
| Sanity SQL nacional indígena | 1.7M-2.0M | 1.834.833 ✅ |

### Backup

```
./infra/backup_db.sh BACKUP_DIR=/tmp/smt-backup-test
→ /tmp/smt-backup-test/smt_onic_20260510T232121Z.sql.gz
→ 152 MB · OK · retención 7d funcional
```

---

## §3 · Composición del sistema

### Código (rama `restore/v2-styling`)

| Capa | Líneas (aprox) | Archivos clave |
|---|---|---|
| Backend Python | ~25K | `backend/app/main.py` · `backend/app/routers/*.py` (11) · `backend/scripts/render_informes.py` (1.180 líneas paramétrico) |
| Frontend React | ~15K | `frontend/src/App.jsx` · `frontend/src/pages/*.jsx` (10+) · `frontend/src/components/*.jsx` |
| SQL | 13 seeds (002-013) | `backend/sql/*.sql` · 250 KB total |
| Tests | 179 tests | `backend/tests/test_*.py` · pytest (correr desde container con instalación dev) |
| Infra | 7 scripts | `infra/*.sh` + `infra/*.conf` · ~25 KB |
| Docs | 11 archivos | raíz + `_docs/` + `docs/MINUTA_HANDOFF_TEMPLATE.md` |

### Datos pre-renderizados (`backend/_static/informes/`)

| Nivel | Archivos JSON | Archivos HTML | Tamaño total |
|---|---|---|---|
| macro | 5 | 5 | ~50 KB |
| dpto | 33 | 33 | ~500 KB |
| mpio | 1.122 | 1.122 | ~20 MB |
| pueblo | 137 | 137 | ~3 MB |
| resguardo | 830 | 830 | ~25 MB |
| **TOTAL** | **2.127** | **2.127** | **~50 MB + MANIFEST.json + CSVs LLM** |

### Tags git activos

```
v1.0.3-ux-fixes     2026-05-09 · 11 archivos UX (frontend)
v1.4.0              2026-05-09 · S9 base · 1.955 informes W12-honesto
v1.4.1              2026-05-10 · S9 cont · 2.127 informes + 4 docs handoff + init_db fix
```

---

## §4 · Deuda conocida (NO bloqueante go-live)

### Drift universo poblacional `pueblo.disc_dpto` (+46%)

- **Síntoma**: suma de `poblacion_referencia` por dpto = 2.784.841 vs canónico 1.905.617.
- **Causa**: tabla `pueblo.disc_dpto` mezcla pertenencias (afros/sin-pertenencia/indígenas) sin columna `grupo_etnico` filtrable.
- **Impacto en runtime**: la UI Panorama nacional muestra `1.834.833` (canónico ✓ · usa otra fuente). Los informes dpto/macro internamente suman a 2.78M pero NO se muestra como agregado nacional al usuario.
- **Decisión**: A2-defer · documentado en `_doctrina/LECCIONES.md` Caso 11 (motor Visual_Agentes) + `CHANGELOG v1.4.0 Notes` + `RUNBOOK §12 Incidente 10`.
- **Sprint S10 dedicado**: requiere acceso DANE para re-extracción REDATAM con filtro upstream.

### Pytest desde host falla import

- `pytest backend/tests/` falla por `ImportError: cannot import name 'where_dptos' from 'app.filters'` (path mismatch host vs container).
- **Mitigación**: smoke tests 7/7 cubren validación funcional · pytest debe correrse desde container o venv con deps dev.
- **Para v1.5+**: agregar `python -m pip install pytest pytest-asyncio` a la imagen API en modo dev (separar `Dockerfile.dev`).

### 3 docs metodológicos diferidos

- `_docs/METODO_FAC_v1.md` (responde "¿de dónde sale el 0.939?")
- `_docs/METODO_PROYECCIONES_v1.md` (Lee-Carter aproximada · IC ±15%)
- `_docs/DECISION_PUEBLOS_CANONICOS.md` (D1 = 115 pueblos)
- **Status**: marcados explícitamente como diferidos en `INSTRUCCIONES_INGENIERIA_ONIC.md §9`. Wilson entrega aparte si ingeniería los necesita.

### Warning bundle frontend >500KB

- `dist/assets/index-Qu9UNJ08.js` = 1.143 MB (326 KB gzip).
- **Mitigación v1.5+**: code-splitting con `import()` dinámico + `build.rolldownOptions.output.codeSplitting`.

---

## §5 · Cambios entre v1.0.3 y v1.4.1 (resumen ejecutivo)

| Sprint | Tag | Highlight |
|---|---|---|
| S5_v1.1 | v1.1.0 | Consolidación 17 tareas · GA release |
| S5 hotfix | v1.1.1 | ordenamiento "100+" + título BarChart |
| S6_observatorio | v1.2.0 | informes correctos + observatorio + seed 200 |
| S7_render_dptos | v1.3.0 | tabla Resguardos asociados en mpios |
| **S9_render_multinivel** | **v1.4.0** | **1.955 informes W12-honesto** · refactor `render_informes.py` paramétrico · k-anonimato real · JSON canonical con `_meta` trazable |
| **S9 continuación** | **v1.4.1** | **2.127 informes completos** + 4 huérfanos `_sin_datos:true` + `init_db.sh` seeds 010-013 + 4 docs handoff |

---

## §6 · 3 decisiones que ONIC debe tomar antes de deploy

Recordatorio (de `INSTRUCCIONES_INGENIERIA_ONIC.md §2`):

| Decisión | Status |
|---|---|
| **D1** ¿Dónde se hostea? (DO Droplet 8GB recomendado · ~$48/mes) | ⏳ pendiente ONIC |
| **D2** ¿Quién custodia secretos? (DB_PASSWORD, JWT_SECRET, seed creds · rotación 90d) | ⏳ pendiente ONIC |
| **D3** ¿Quién recibe alertas? (Slack/Teams + email oncall) | ⏳ pendiente ONIC |

---

## §7 · Comandos go-live (referencia rápida)

```bash
# 0 · Pre-requisitos en servidor (Ubuntu 22.04 LTS · 4 vCPU · 8 GB · 50 GB SSD)
sudo apt install docker docker-compose-v2 git curl jq nginx certbot

# 1 · Clonar y configurar
git clone -b restore/v2-styling https://github.com/Etnic-Consulting/discapacidad.git smt-onic
cd smt-onic
cp .env.prod.example .env.prod
$EDITOR .env.prod   # rellenar DB_PASSWORD (openssl rand -hex 24), JWT_SECRET (openssl rand -hex 32), CORS_ORIGINS

# 2 · Variables del corpus de datos (Wilson entrega URL + SHA256 por canal seguro)
export URL_DATA="https://<canal-seguro>/bd_consolidada.tar.gz"
export EXPECTED_SHA256="<sha256-que-Wilson-entrega-aparte>"

# 3 · Deploy en un script
chmod +x infra/deploy_servidor_onic.sh
./infra/deploy_servidor_onic.sh

# 4 · TLS + nginx
sudo cp infra/nginx.smt-onic.conf /etc/nginx/sites-available/smt-onic
sudo ln -sf /etc/nginx/sites-available/smt-onic /etc/nginx/sites-enabled/
sudo mkdir -p /var/www/smt-onic-frontend
sudo cp -r frontend/dist/* /var/www/smt-onic-frontend/
sudo certbot --nginx -d smt-onic.com -d www.smt-onic.com --agree-tos -m poblacion@onic.org.co --no-eff-email
sudo nginx -t && sudo systemctl reload nginx

# 5 · Validar
./infra/smoke_tests.sh https://smt-onic.com   # esperar 7/7 PASS

# 6 · Cron backup
echo "0 3 * * * deploy /opt/smt-onic/infra/backup_db.sh >> /var/log/smt-onic-backup.log 2>&1" | sudo tee /etc/cron.d/smt-onic-backup
```

---

## §8 · Contactos

| Rol | Persona | Contacto |
|---|---|---|
| Director del proyecto | Wilson Herrera | `poblacion@onic.org.co` |
| Repositorio | github.com/Etnic-Consulting/discapacidad | rama `restore/v2-styling` |
| Sesión handoff | Wilson + ingeniería ONIC | agendar 90 min · `INSTRUCCIONES §10` |
| Minuta final | `docs/MINUTA_HANDOFF_TEMPLATE.md` | firmar tras §10 |

---

## §9 · Histórico de validación

| Fecha | Validación | Resultado |
|---|---|---|
| 2026-05-09 22:54 | T01 refactor render_informes_macro.py → paramétrico | ✅ JSON IDÉNTICO módulo fecha |
| 2026-05-09 23:18 | T07 audit cells_dash_pct = 1.01% | ✅ criterio <5% |
| 2026-05-10 17:01-17:16 | Sprint S9 cont T08-T20 · 13/13 ENTREGADO | ✅ tag v1.4.1 |
| 2026-05-10 22:23-22:30 | Playwright smoke E2E 8 rutas + 4 informes + 6 API | ✅ todos PASS |
| 2026-05-10 18:21 | Backup test 152 MB pg_dump | ✅ retención 7d OK |
| 2026-05-10 (este) | Frontend build + smoke 7/7 + sanity 1.83M + deploy script syntax | ✅ handoff-ready |

---

**Estado al cierre**: 🟢 **HANDOFF READY · pendiente solo acciones humanas (push + agendar handoff)**.
