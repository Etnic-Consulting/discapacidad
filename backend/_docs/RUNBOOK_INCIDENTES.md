# Runbook · incidentes operativos SMT-ONIC

Procedimientos de respuesta a incidentes comunes en producción.

## Severidad

| Nivel | Tiempo de respuesta | Ejemplos |
|---|---|---|
| **P1 · crítico** | < 30 min | API caída · DB no responde · login roto |
| **P2 · alto** | < 4 h | Endpoint específico falla · backup no se ejecutó |
| **P3 · medio** | < 24 h | Cifras inconsistentes · render lento |
| **P4 · bajo** | siguiente sprint | Texto incorrecto · estilo visual |

## Incidente 1 · API no responde (P1)

**Síntomas:** smoke test `/health` falla · uptime monitor alerta.

**Diagnóstico:**
```bash
docker compose ps                     # ¿está el container?
docker compose logs api --tail=100    # ¿qué dice el log?
docker exec smt-onic-api curl localhost:8000/api/v1/health
```

**Acciones:**
1. Si el container está caído: `docker compose --env-file .env.prod up -d api`
2. Si el container reinicia en bucle: revisar `DATABASE_URL`, secretos y dependencias.
3. Si el host está saturado de memoria: `docker compose restart` y abrir ticket de capacidad.
4. Última opción: rollback al commit anterior (ver `DEPLOY_PRODUCCION.md §7`).

## Incidente 2 · Base de datos lenta (P2)

**Síntomas:** endpoints lentos > 3s · timeouts en frontend.

**Diagnóstico:**
```bash
docker exec smt-onic-db psql -U smt_admin -d smt_onic -c "
  SELECT pid, query_start, state, query
  FROM pg_stat_activity
  WHERE state != 'idle'
  ORDER BY query_start;
"
```

**Acciones:**
1. Identificar query lenta y matar si es necesario: `SELECT pg_terminate_backend(<pid>)`.
2. Verificar índices: `\di+ <schema>.<tabla>`.
3. Si conexiones llegan al límite del pool: aumentar `max_connections` o investigar leak en backend.

## Incidente 3 · Disco lleno (P1)

**Síntomas:** alerta `df -h /data` > 80 %.

**Diagnóstico:**
```bash
du -sh /data/*
docker system df
docker volume ls
```

**Acciones:**
1. Limpiar imágenes Docker antiguas: `docker system prune -a` (solo en mantenimiento programado).
2. Rotar logs: `truncate -s 0 /var/log/docker/*.log`.
3. Si la BD ocupa demasiado: `VACUUM FULL` programado y considerar archivado de tablas históricas.

## Incidente 4 · Backup no se ejecutó (P2)

**Síntomas:** `cron` no ejecutó `infra/backup_db.sh` · log vacío.

**Diagnóstico:**
```bash
crontab -l                              # ¿está el cron?
tail -50 /var/log/smt-onic-backup.log   # ¿error específico?
```

**Acciones:**
1. Ejecutar backup manual: `bash infra/backup_db.sh`.
2. Verificar permisos del usuario `deploy`.
3. Si el backup remoto (S3/GCS) falla: revisar credenciales `BACKUP_REMOTE_URI`.

## Incidente 5 · Login roto (P1)

**Síntomas:** los usuarios no pueden ingresar · `/api/v1/auth/login` retorna 401 con credenciales correctas.

**Diagnóstico:**
```bash
docker exec smt-onic-db psql -U smt_admin -d smt_onic -c "
  SELECT username, activo FROM smt.usuarios;
"
docker exec smt-onic-api env | grep JWT_SECRET
```

**Acciones:**
1. Si `JWT_SECRET` cambió, todas las sesiones existentes se invalidan. Comunicar a usuarios y forzar re-login.
2. Si la tabla `smt.usuarios` está vacía o el usuario está `activo=false`, restaurar desde backup.
3. Si `auth/login` retorna 500, revisar `app/services/auth.py` y dependencias `passlib`.

## Incidente 6 · Endpoint con cifras inconsistentes (P3)

**Síntomas:** un usuario reporta que el dato del frontend no coincide con un informe Word descargado.

**Diagnóstico:**
```bash
# Verificar fuente única
docker exec smt-onic-db psql -U smt_admin -d smt_onic -c "
  SELECT * FROM <schema>.<tabla> WHERE <id> = ...
"
```

**Acciones:**
1. Confirmar que ambos consumos (frontend y backend Word) leen de la misma tabla.
2. Si el informe pre-renderizado tiene la cifra desactualizada: re-ejecutar el batch de pre-render correspondiente.
3. Si la inconsistencia viene del seed: aplicar corrección en SQL e indicar versión.

## Incidente 7 · TLS expirado (P1)

**Síntomas:** navegador muestra advertencia de certificado.

**Acciones:**
```bash
sudo certbot renew
sudo nginx -t && sudo systemctl reload nginx
```

`certbot` debería estar en cron automático · si falló, agregar tarea en `/etc/cron.d/certbot`.

## Procedimiento de rollback

Si una nueva versión rompe producción:

```bash
cd /opt/smt-onic
git log --oneline -5                       # identificar commit estable previo
docker compose --env-file .env.prod down
git checkout <commit-estable>
docker compose --env-file .env.prod up -d
bash infra/smoke_tests.sh https://smt-onic.com
```

## Contactos de escalamiento

- **Coordinador técnico:** Wilson Herrera · `poblacion@onic.org.co` · +57 311 220 1903
- **Proveedor:** EtniConsulting SAS

---

© EtniConsulting SAS — 2026
