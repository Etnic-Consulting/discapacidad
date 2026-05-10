# Runbook de incidentes · SMT-ONIC producción

**Audiencia**: equipo oncall ingeniería ONIC.
**Última actualización**: 2026-05-10 · v1.4.1.

---

## §1 · Cuándo usar este documento

Abrir este runbook cuando:
- Alerta automática dispara (Slack/Teams oncall).
- Usuario reporta error visible en https://smt-onic.com.
- Smoke test cron falla.
- Backup nocturno falló.
- Hook `verificar_universo_poblacional.py` dispara (>2M).

Si el síntoma no matchea ninguno de los 10 incidentes listados → ver `§13 · Apéndice · diagnósticos rápidos` para herramientas generales.

---

## §2 · Convenciones

| Sección | Significado |
|---|---|
| **Síntoma** | Lo que ve el operador (alerta, error usuario, log line) |
| **Diagnóstico** | Comandos a correr en orden para confirmar causa |
| **Acción** | Qué hacer una vez confirmada la causa |
| **Escalation** | A quién avisar si no se resuelve en X minutos · ver §14 chain |

---

## §3 · Incidente 1 · API 5xx persistente

**Síntoma**: `/api/v1/health` retorna 500 o 503 · `curl https://smt-onic.com/api/v1/health` falla con stacktrace o "503 Service Unavailable".

**Diagnóstico**:
```bash
# 1. Status contenedor
docker compose ps
# 2. Logs últimos 50 líneas API
docker compose logs api --tail=50
# 3. Resources
docker stats --no-stream
```

Buscar:
- Stacktrace Python · indica bug code.
- `MemoryError` o OOM kill · indica RAM insuficiente.
- `connection refused` a DB · ver Incidente 2.

**Acción**:
- Si OOM → subir RAM Docker o reducir workers Uvicorn (`UVICORN_WORKERS` en `.env.prod` · default 4 → 2).
- Si exception puntual → fix code + redeploy (`git pull && docker compose --env-file .env.prod build api && docker compose up -d`).
- Si DB unreachable → resolver Incidente 2 primero.

**Escalation**: si >15min sin resolver → avisar Wilson (`poblacion@onic.org.co`).

---

## §4 · Incidente 2 · DB connection pool exhausted

**Síntoma**: API responde 503 con mensaje "remaining connection slots reserved" · log Postgres "FATAL: too many connections".

**Diagnóstico**:
```bash
# Conexiones activas
docker exec smt-onic-db psql -U smt_admin -d smt_onic -c "
  SELECT count(*) AS total,
         count(*) FILTER (WHERE state='active') AS active,
         count(*) FILTER (WHERE state='idle') AS idle
  FROM pg_stat_activity"
```

Si `total >= 90` → pool exhausted.

**Acción**:
1. **Inmediato** (cortar leak): `docker compose restart api` · libera todas las conexiones.
2. **Corto plazo**: subir `max_connections` en `infra/postgres.conf` (default 100 → 200) · restart db.
3. **Largo plazo**: reducir pool API · agregar a `.env.prod`:
   ```
   SQLALCHEMY_POOL_SIZE=10
   SQLALCHEMY_MAX_OVERFLOW=20
   ```

**Escalation**: si recurre >2x/día → revisar leaks en `backend/app/db/session.py` (verificar que todos los endpoints usen `Depends(get_db)` correctamente con yield).

---

## §5 · Incidente 3 · Disco lleno

**Síntoma**: `df -h` muestra `/var/lib/docker` o `/opt/smt-onic` >90% · errores escritura logs nginx/api.

**Diagnóstico**:
```bash
# Identificar carpeta gorda
du -sh /var/lib/docker/* /opt/smt-onic/* 2>/dev/null | sort -h | tail -20
# Logs Docker (frecuente culpable)
sudo du -sh /var/lib/docker/containers/*/
```

**Acción** (en orden):
1. Rotar logs: `sudo logrotate -f /etc/logrotate.d/smt-onic`.
2. Purgar backups antiguos: `find /opt/smt-onic/backups -name "*.sql.gz" -mtime +30 -delete`.
3. Purgar imágenes Docker huérfanas: `docker system prune -a --volumes -f`.
4. Si sigue lleno: `truncate -s 0 /var/lib/docker/containers/*/*-json.log` (cuidado · pierde logs históricos).

**Escalation**: si servidor freeza → reboot · luego investigar causa raíz (logs verbosos, backup remoto no sube, etc.).

---

## §6 · Incidente 4 · Bruteforce en /auth/login

**Síntoma**: logs nginx muestran picos de POST `/auth/login` desde misma IP · 401s repetidos.

**Diagnóstico**:
```bash
# Top 10 IPs con 401 en /auth/login
awk '$9==401 && $7=="/auth/login"' /var/log/nginx/access.log \
  | awk '{print $1}' | sort | uniq -c | sort -rn | head -10
```

Si >100 intentos/min desde 1 IP → bruteforce confirmado.

**Acción**:
1. **Inmediato**: bloquear IP via iptables:
   ```bash
   sudo iptables -A INPUT -s <IP-ofensiva> -j DROP
   ```
2. **Corto plazo**: activar fail2ban con jail SMT-ONIC (config en `infra/fail2ban.smt-onic.conf` · 5 fallos en 5min → ban 1h).
3. **Largo plazo**: agregar rate limit nginx en `infra/nginx.smt-onic.conf`:
   ```nginx
   limit_req_zone $binary_remote_addr zone=auth:10m rate=5r/m;
   location /auth/login { limit_req zone=auth burst=2; }
   ```

**Escalation**: si patrón distribuido (botnet · múltiples IPs simultáneas) → ingeniería ONIC evalúa Cloudflare/WAF · avisar L2.

---

## §7 · Incidente 5 · TLS expirado

**Síntoma**: navegador muestra warning "NET::ERR_CERT_DATE_INVALID" · `curl` falla con `SSL certificate has expired`.

**Diagnóstico**:
```bash
sudo certbot certificates
# Muestra "VALID: <N> days" · si <7 días es preocupante · si negativo está expirado
```

**Acción**:
1. Renovación manual: `sudo certbot renew --force-renewal`.
2. Recargar nginx: `sudo systemctl reload nginx`.
3. Verificar auto-renew cron: `cat /etc/cron.d/certbot` · debe existir entry diario.

**Escalation**: si certbot falla por DNS challenge → verificar DNS A record apunta correctamente · si problema persiste, usar HTTP-01 challenge (`certbot --webroot -w /var/www/smt-onic-frontend`).

---

## §8 · Incidente 6 · Frontend muestra `—` en KPIs

**Síntoma**: dashboard carga estructura pero todos los números aparecen como `—`, "Loading..." indefinidamente, o pantalla en blanco.

**Diagnóstico**: abrir DevTools (F12) · pestaña Console + Network:
- Si CORS error → `.env.prod` `CORS_ORIGINS` mal seteado.
- Si 401 → token expiró · re-login.
- Si 5xx → backend caído (Incidente 1).
- Si 404 → endpoint no existe (frontend desactualizado).

**Acción**:
- CORS: corregir `CORS_ORIGINS='["https://smt-onic.com","https://www.smt-onic.com"]'` · restart api.
- 401: re-login en UI · si persiste, verificar que JWT_SECRET no cambió mid-sesión.
- 5xx: ver Incidente 1.
- 404 endpoint: rebuild frontend (`cd frontend && npm run build && sudo cp -r dist/* /var/www/smt-onic-frontend/`).

**Escalation**: si afecta >50% usuarios → rollback frontend al tag anterior:
```bash
git checkout v1.4.0 -- frontend/dist/
sudo cp -r frontend/dist/* /var/www/smt-onic-frontend/
sudo systemctl reload nginx
```

---

## §9 · Incidente 7 · Smoke test 6 falla (auth abierta)

**🚨 CRÍTICO · datos sensibles potencialmente expuestos**.

**Síntoma**: `./infra/smoke_tests.sh` reporta test 6 FAIL · `GET /pueblos/` sin token retorna 200 (debería 401).

**Diagnóstico**:
```bash
# Verificar Depends(get_current_user) en endpoint /pueblos/
grep -A2 'router.get."/"' backend/app/routers/pueblos.py
# Debe incluir: Depends(get_current_user)
```

Si falta el `Depends` → regresión introducida por commit reciente.

**Acción**:
1. **Inmediato** (mitigar exposición): poner nginx en mode mantenimiento:
   ```bash
   sudo cp infra/nginx.maintenance.conf /etc/nginx/sites-available/smt-onic
   sudo systemctl reload nginx
   ```
2. Identificar commit que rompió auth: `git log --oneline backend/app/routers/pueblos.py` · buscar commit reciente sin `Depends`.
3. Revertir commit problemático o cherry-pick `8d1c526` (commit T24 original que cerró auth).
4. Rebuild + redeploy: `docker compose --env-file .env.prod build api && docker compose up -d`.
5. Validar smoke 6 OK antes de desactivar mantenimiento.

**Escalation**: **NIVEL L3 inmediato** · avisar Wilson + seguridad ONIC por teléfono directo · datos potencialmente expuestos requiere notificación Habeas Data si confirmado leak >24h.

---

## §10 · Incidente 8 · Nginx 502 Bad Gateway

**Síntoma**: usuario ve "502 Bad Gateway" · `curl https://smt-onic.com/api/v1/health` retorna 502.

**Diagnóstico**:
```bash
# 1. ¿Está corriendo el contenedor API?
docker compose ps api
# 2. ¿Responde internamente?
docker exec smt-onic-api curl -s localhost:8095/api/v1/health
# 3. Logs nginx
sudo tail -50 /var/log/nginx/error.log
```

**Acción**:
- API down → `docker compose --env-file .env.prod up -d api`.
- API up pero nginx no llega → revisar `infra/nginx.smt-onic.conf` upstream:
  ```nginx
  upstream smt_onic_api {
    server 127.0.0.1:8095;
  }
  ```
- Si config nginx corrupto → restaurar desde repo:
  ```bash
  git checkout main -- infra/nginx.smt-onic.conf
  sudo cp infra/nginx.smt-onic.conf /etc/nginx/sites-available/smt-onic
  sudo nginx -t && sudo systemctl reload nginx
  ```

**Escalation**: si nginx no levanta tras restore → L2.

---

## §11 · Incidente 9 · Backup falló

**Síntoma**: `tail /var/log/smt-onic-backup.log` muestra error · `/opt/smt-onic/backups/` sin archivo del día.

**Diagnóstico**:
```bash
# Re-correr backup manualmente con verbose
bash -x /opt/smt-onic/infra/backup_db.sh
```

Causas comunes:
- DB caída (Incidente 1/2).
- Disco lleno (Incidente 3).
- `BACKUP_REMOTE_URI` mal configurado (S3/GCS credenciales).

**Acción**:
1. Resolver causa raíz primero (DB/disco).
2. Backup manual de emergencia:
   ```bash
   docker exec smt-onic-db pg_dump -U smt_admin smt_onic \
     | gzip > /opt/smt-onic/backups/manual-$(date +%Y%m%d-%H%M%S).sql.gz
   ```
3. Validar tamaño esperado (~500MB-1.5GB).
4. Reactivar cron una vez resuelta causa.

**Escalation**: si >48h sin backup exitoso → **CRÍTICO** · DPIA/Habeas Data viola política de respaldo · L2 + Wilson.

---

## §12 · Incidente 10 · Hook universo poblacional dispara (>2M)

**Síntoma**: alerta automática "agregado nacional indígena > 2M" · dashboard panorama muestra cifra alta (esperado ~1.83M CNPV 2018).

**Diagnóstico**:
```bash
# Sanity check directo a DB
docker exec smt-onic-db psql -U smt_admin -d smt_onic -c "
  SELECT SUM(pob_total)::int AS total_indigena
  FROM cnpv.prevalencia_etnia_dpto
  WHERE grupo_etnico='Indigena' AND periodo='2018';
"
```

Interpretar resultado:

| Total | Causa | Severidad |
|---|---|---|
| **~3.7M (≈ 2× CNPV)** | Seeds 010-011 NO aplicados · cifra agregado nacional concentrada erróneamente en Cumaribo (cod_mpio=99773) y Vichada (cod_dpto=99) | CRÍTICO · fix inmediato |
| **~2.78M (≈ 1.5× CNPV)** | Leak afros/sin-pertenencia heredado en `pueblo.disc_dpto` · NO es bug runtime · documentado | INFORMATIVO · acción diferida |
| **~1.83M (1.7M-2.0M)** | OK · universo canónico | sin acción |

**Acción**:

**Caso ~3.7M (seeds faltantes)**:
```bash
# Re-correr init_db.sh (idempotente · aplica todos los seeds 002-013)
./infra/init_db.sh
# Validar
docker exec smt-onic-db psql -U smt_admin -d smt_onic -c "
  SELECT SUM(pob_total) FROM cnpv.prevalencia_etnia_dpto WHERE grupo_etnico='Indigena' AND periodo='2018'
"
# Esperar ~1.83M post-fix
```

**Caso ~2.78M (leak heredado)**: este es el comportamiento conocido v1.4.x · documentado en `_doctrina/LECCIONES.md` Caso 11 (motor Visual_Agentes) y en `CHANGELOG.md` v1.4.0 sección Notes. **NO modificar `pueblo.disc_dpto` upstream sin coordinar con Wilson** · re-extracción REDATAM requiere acceso DANE. Sprint S10 futuro está dedicado a este fix.

**Acción inmediata si la cifra inflada está visible en UI pública**:
- Considerar deshabilitar temporalmente el endpoint que la expone (`/dashboard/prevalencia/departamento`) hasta que esté el fix S10.
- O agregar disclaimer en el frontend "cifras dpto pueden estar infladas por mezcla étnica · ver nota técnica".

**Escalation**: si caso ~3.7M no resuelve con re-correr `init_db.sh` → L2 + Wilson · puede haber bug en los seeds 010-011 mismos.

---

## §13 · Apéndice · comandos diagnósticos rápidos

```bash
# 1. Estado contenedores
docker compose ps

# 2. Logs últimos 100 líneas API
docker compose logs --tail=100 api

# 3. Logs últimos 100 líneas DB
docker compose logs --tail=100 db

# 4. Resource usage
docker stats --no-stream

# 5. DB conexiones activas
docker exec smt-onic-db psql -U smt_admin -d smt_onic -c "SELECT count(*) FROM pg_stat_activity"

# 6. Health check API
curl -s http://localhost:8095/api/v1/health | jq

# 7. Smoke tests completos
./infra/smoke_tests.sh https://smt-onic.com

# 8. Disco
df -h /var/lib/docker /opt/smt-onic

# 9. Backup status
tail -20 /var/log/smt-onic-backup.log

# 10. TLS expiry
sudo certbot certificates

# 11. Sanity universo indígena
docker exec smt-onic-db psql -U smt_admin -d smt_onic -c "
  SELECT SUM(pob_total) FROM cnpv.prevalencia_etnia_dpto WHERE grupo_etnico='Indigena' AND periodo='2018'
"

# 12. Top errores nginx últimas 100 lineas
sudo tail -100 /var/log/nginx/error.log
```

---

## §14 · Apéndice · escalation chain

| Nivel | Responsable | SLA | Contacto |
|---|---|---|---|
| **L0 · operador** | turno oncall ingeniería ONIC | <15 min | Slack/Teams oncall |
| **L1 · líder ingeniería** | jefe equipo ingeniería ONIC | <1h | email + Slack |
| **L2 · director proyecto** | Wilson Herrera | <4h | `poblacion@onic.org.co` |
| **L3 · seguridad CRÍTICO** (auth abierta · datos expuestos · Habeas Data) | ONIC seguridad + Wilson | inmediato | teléfono directo + email |

---

## §15 · Cross-references

- `_docs/ARCHITECTURE.md` · §1-§8 contexto sistémico
- `_docs/MATRIZ_AUTH_v1.md` · §3 detalle por router (Incidente 7)
- `_docs/CHECKLIST_GO_LIVE.md` · §4 sanity check seeds (Incidente 10)
- `_doctrina/LECCIONES.md` (motor Visual_Agentes) · Caso 11 (Incidente 10 leak heredado)
- `INSTRUCCIONES_INGENIERIA_ONIC.md` · §3 (deploy script único)
- `DEPLOY_PRODUCCION.md` · §7-§9 (rollback procedures)
