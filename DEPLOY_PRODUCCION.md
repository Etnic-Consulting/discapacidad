# Deploy a producción · SMT-ONIC

**Audiencia:** equipo de ingeniería que va a publicar el dashboard en https://smt-onic.com.
**Estado actual:** rama `restore/v2-styling` · Sprint S1 al ~80% (10 tareas residuales menores en `_docs/ROADMAP_SPRINT_S1_S2.md`).

## 1. Pre-requisitos

| Requisito | Mínimo | Notas |
|---|---|---|
| **Docker Engine** | ≥ 20.10 | Compose v2 incluido (`docker compose`, sin guion) |
| **CPU / RAM** | 4 vCPU · 8 GB RAM | PostGIS y FastAPI consumen ~2-3 GB en operación |
| **Disco** | 50 GB libres | BD CNPV (~2 GB con índices) + logs + backups |
| **Puertos abiertos** | 80, 443, 5450 (DB, opcional externo) | API en 8095 detrás de reverse proxy (nginx) |
| **Dominio** | smt-onic.com con DNS apuntando al servidor | TLS via Let's Encrypt + nginx |
| **Cuenta GitHub** | con scope `repo` para `Etnic-Consulting/discapacidad` | ya confirmada para `wilsonherrera77` |
| **PAT activo** | ⚠️ rotar antes de handoff (H-ONIC-007 pendiente) | usar `gh auth refresh -s repo` |

## 2. Variables de entorno

Crear `.env.prod` en la raíz del repo (NO commitear · ya está en `.gitignore`):

```bash
DB_PASSWORD=<generar con: openssl rand -hex 24>
JWT_SECRET=<generar con: openssl rand -hex 32>
SMT_ONIC_DOMAIN=smt-onic.com
CORS_ORIGINS='["https://smt-onic.com","https://www.smt-onic.com"]'
DISCAPACIDAD_DIR=/data/discapacidad   # path absoluto en el servidor
```

Para el **mount del corpus** (`bd_consolidada/` con CSVs y seeds):

```bash
mkdir -p /data/discapacidad/bd_consolidada
# Subir tar.gz desde local · ver §6 Carga inicial
```

## 3. Primer deploy (orden estricto)

```bash
# 3.1 · Clonar repo (rama prod-ready)
git clone -b restore/v2-styling https://github.com/Etnic-Consulting/discapacidad.git smt-onic
cd smt-onic

# 3.2 · Cargar env vars
cp .env.example .env.prod
$EDITOR .env.prod   # rellenar valores del §2

# 3.3 · Levantar DB (sola · espera healthy)
docker compose --env-file .env.prod up -d db
docker compose ps   # verificar smt-onic-db en estado healthy (5-15s)

# 3.4 · Aplicar schema base (ya se aplica auto via docker-entrypoint-initdb.d/01-schema.sql)
# Verificar:
docker exec smt-onic-db psql -U smt_admin -d smt_onic -c "\dn"
# Debe listar: cnpv, ext, geo, indicadores, pueblo, smt, smt_geo, victimas, visor_dane, public

# 3.5 · Aplicar seeds en orden numérico ascendente (incluye fixes 010-013)
for f in 002_auth_formulario.sql 003_macro_dptos.sql 003_seed_proyecciones_fac.sql \
         004_seed_proyecciones_escenarios.sql 005_seed_indicadores_definiciones.sql \
         006_seed_indicadores_icv.sql 007_seed_triangulacion.sql \
         008_seed_prev_estandarizada_stub.sql 009_fix_pueblos_e2e.sql \
         010_fix_seed_99773_agregado_nacional.sql \
         011_fix_dpto_99_agregados_nacionales.sql \
         012_smt_resumen.sql \
         013_fix_trigger_dim_dptos.sql; do
  docker exec -i smt-onic-db psql -U smt_admin -d smt_onic < backend/sql/$f
done

# Las migraciones 010 y 011 son idempotentes con DO block de validación: corrigen
# un bug del seed CNPV donde el agregado nacional indígena fue mal asignado al
# cod_mpio=99773 (Cumaribo) y al cod_dpto=99 (Vichada). Sin estas, las cifras
# agregadas para Vichada o consultas departamentales mostrarán ~1.9M indígenas
# concentrados erróneamente en un solo territorio.

# Verificar inserción:
docker exec smt-onic-db psql -U smt_admin -d smt_onic -c "
  SELECT COUNT(*) AS fac FROM proyecciones.fac;                 -- esperar 8
  SELECT COUNT(*) AS escenarios FROM proyecciones.escenarios;   -- esperar 832
  SELECT COUNT(*) AS indicadores FROM indicadores.definiciones; -- esperar >=12
  SELECT SUM(pob_total) AS total_indigenas
  FROM cnpv.prevalencia_etnia_dpto
  WHERE grupo_etnico='Indigena' AND periodo='2018';             -- esperar ~1.83M (NO 3.7M · si da 3.7M faltan 010/011)
"

# 3.6 · Cargar datos CNPV completos
docker exec smt-onic-api python -m scripts.load_all
# (15-30 min · carga ~1-2M filas · barra de progreso en logs)

# 3.7 · Levantar API
docker compose --env-file .env.prod up -d api
docker compose ps   # ambos healthy

# 3.8 · Smoke tests (ver §4)
```

## 4. Smoke tests post-deploy

```bash
# 4.1 · Health
curl -fsS http://localhost:8095/api/v1/health | jq
# Esperar: {"status":"ok","db":"connected"}

# 4.2 · Auth login (los endpoints de datos están cerrados desde S1.D24)
TOKEN=$(curl -s -X POST http://localhost:8095/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"wilson","password":"<seed-password>"}' | jq -r .access_token)

# 4.3 · Endpoint nuevo · proyecciones (T08)
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8095/api/v1/dashboard/proyecciones?grupo_etnico=Indigena" | jq '.total, .data[0]'
# Esperar: 104 (4 escenarios × 26 años) y un objeto con prevalencia_pct + IC

# 4.4 · Endpoint extendido · intercensal con FAC (T02)
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8095/api/v1/dashboard/intercensal?grupo_etnico=Indigena&aplicar_fac=true" | jq '.fac_aplicado, .advertencia'
# Esperar: true · "Cifras 2005 ajustadas con FAC..."

# 4.5 · Endpoint extendido · brecha con sources detallados (T06)
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8095/api/v1/dashboard/brecha" | jq '.pasos[0].source_detalle'
# Esperar: objeto con cita + marco_normativo + url + metodologia

# 4.6 · Auth aplicada · sin token debe retornar 401
curl -i http://localhost:8095/api/v1/pueblos/ 2>&1 | head -3
# Esperar: HTTP/1.1 401 Unauthorized

# 4.7 · Frontend levanta (si está deployado en :5174 o detrás de nginx)
curl -fsS https://smt-onic.com/ | grep -q 'SMT-ONIC' && echo OK || echo FAIL
```

## 5. Reverse proxy (nginx · ejemplo)

```nginx
server {
    listen 443 ssl http2;
    server_name smt-onic.com www.smt-onic.com;

    ssl_certificate     /etc/letsencrypt/live/smt-onic.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/smt-onic.com/privkey.pem;

    location /api/ {
        proxy_pass http://127.0.0.1:8095;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        root /var/www/smt-onic-frontend;
        try_files $uri $uri/ /index.html;
    }
}
```

## 6. Carga inicial de datos (corpus 271 MB)

```bash
# En el servidor · una sola vez
mkdir -p /data/discapacidad
cd /data/discapacidad
# Recibir tar.gz por canal seguro (Drive/SFTP) · descomprimir
tar -xzf bd_consolidada.tar.gz
# Verificar checksums: cat bd_consolidada/.checksums.sha256 | sha256sum -c -
docker exec smt-onic-api python -m scripts.load_all
```

## 7. Rollback

```bash
# Último resort si un deploy rompe producción:
docker compose down
git checkout <commit-anterior-estable>
docker compose --env-file .env.prod up -d db api
# Si seeds 003/004/005 introdujeron datos malos:
docker exec smt-onic-db psql -U smt_admin -d smt_onic -c "
  TRUNCATE proyecciones.fac CASCADE;
  TRUNCATE proyecciones.escenarios CASCADE;
  TRUNCATE indicadores.definiciones CASCADE;
"
# Re-ejecutar 3.5 con seeds previos backed up.
```

## 8. Monitoring básico

| Métrica | Cómo | Alerta |
|---|---|---|
| API up | `curl /api/v1/health` cada 30s | 3 fallas consecutivas |
| DB connections | `docker exec ... pg_stat_activity` | > 80% pool |
| Disk | `df -h /data` | > 80% |
| Errores 5xx | logs uvicorn (`docker logs smt-onic-api`) | > 5/min |
| Auth fails | search `401` o `403` en logs | > 100/min (posible ataque) |

## 9. Checklist pre-handoff a ingeniería

- [ ] Rotar PAT GitHub (H-ONIC-007)
- [ ] Generar `DB_PASSWORD` y `JWT_SECRET` con `openssl rand`
- [ ] Smoke tests §4 todos verdes localmente
- [ ] Sprint S1.C frontend Phase 2 cerrado (refactores PUEBLOS, RESGUARDOS, CONFLICTO_DPTO, PROYECCIONES, INDICADORES → hooks API)
- [ ] Hotfixes Sprint 0 mergeados desde `copia noteboo/snapshot_2026-04-22_10-33`
- [ ] Tag `v1.0.0-prod-ready` creado y pushed
- [ ] PR a `main` aprobado y mergeado
- [ ] CI verde en GitHub Actions (`.github/workflows/ci.yml`)
- [ ] Backup automático de DB configurado (cron + pg_dump)
- [ ] Sentry / observabilidad básica configurada (opcional v1.1)

## 10. Contactos

- **Director del proyecto:** Wilson Herrera · `poblacion@onic.org.co`
- **Repo:** https://github.com/Etnic-Consulting/discapacidad
- **Sprint Tracker:** `proyectos/discapacidad/sprints/S1_higiene_datos/PIZARRA.md` (en repo Visual_Agentes interno)
- **Doctrina:** `proyectos/discapacidad/_docs/ROADMAP_SPRINT_S1_S2.md`
