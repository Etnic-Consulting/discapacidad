#!/usr/bin/env bash
# infra/backup_db.sh · SMT-ONIC backup diario PostgreSQL
# =======================================================
# Idempotente · safe to re-run.
# Diseñado para correr desde cron como usuario `deploy`.
#
# Cron sugerido (diario 03:00 hora Bogotá):
#   0 3 * * * deploy /opt/smt-onic/infra/backup_db.sh >> /var/log/smt-onic-backup.log 2>&1
#
# Variables opcionales:
#   BACKUP_DIR          · default /opt/smt-onic-backups
#   BACKUP_REMOTE_URI   · ej: s3://onic-smt-backups/db/  · gs://...  · sftp://...
#                         si está seteado, sube tras éxito local
#   BACKUP_RETENTION_DAYS · default 7 (días de retención local)
#
# Generado por Sprint S2 · 2026-05-03

set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/opt/smt-onic-backups}"
BACKUP_REMOTE_URI="${BACKUP_REMOTE_URI:-}"
BACKUP_RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-7}"
DB_CONTAINER="${DB_CONTAINER:-smt-onic-db}"
DB_USER="${DB_USER:-smt_admin}"
DB_NAME="${DB_NAME:-smt_onic}"

TIMESTAMP=$(date -u +%Y%m%dT%H%M%SZ)
BACKUP_FILE="$BACKUP_DIR/smt_onic_$TIMESTAMP.sql.gz"

mkdir -p "$BACKUP_DIR"

echo "[$(date -Iseconds)] backup start → $BACKUP_FILE"

# 1 · pg_dump
if ! docker exec "$DB_CONTAINER" pg_dump -U "$DB_USER" -d "$DB_NAME" --format=plain --no-owner | gzip > "$BACKUP_FILE"; then
  echo "[$(date -Iseconds)] FAIL · pg_dump falló"
  rm -f "$BACKUP_FILE"
  exit 1
fi

SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo "[$(date -Iseconds)] backup local OK · $SIZE"

# 2 · upload remoto si está configurado
if [[ -n "$BACKUP_REMOTE_URI" ]]; then
  case "$BACKUP_REMOTE_URI" in
    s3://*)
      if command -v aws >/dev/null 2>&1; then
        aws s3 cp "$BACKUP_FILE" "$BACKUP_REMOTE_URI" \
          && echo "[$(date -Iseconds)] upload S3 OK" \
          || { echo "[$(date -Iseconds)] FAIL · upload S3"; exit 1; }
      else
        echo "[$(date -Iseconds)] WARN · awscli no instalado · saltando upload"
      fi
      ;;
    gs://*)
      if command -v gsutil >/dev/null 2>&1; then
        gsutil cp "$BACKUP_FILE" "$BACKUP_REMOTE_URI" \
          && echo "[$(date -Iseconds)] upload GCS OK" \
          || { echo "[$(date -Iseconds)] FAIL · upload GCS"; exit 1; }
      else
        echo "[$(date -Iseconds)] WARN · gsutil no instalado · saltando upload"
      fi
      ;;
    sftp://*|scp://*)
      echo "[$(date -Iseconds)] WARN · SFTP/SCP backup remoto requiere config manual · ver runbook"
      ;;
    *)
      echo "[$(date -Iseconds)] WARN · BACKUP_REMOTE_URI con scheme no soportado: $BACKUP_REMOTE_URI"
      ;;
  esac
fi

# 3 · rotar locales · borrar > BACKUP_RETENTION_DAYS días
find "$BACKUP_DIR" -name "smt_onic_*.sql.gz" -type f -mtime +"$BACKUP_RETENTION_DAYS" -delete
KEPT=$(find "$BACKUP_DIR" -name "smt_onic_*.sql.gz" -type f | wc -l)
echo "[$(date -Iseconds)] retención: $KEPT backups locales conservados (límite ${BACKUP_RETENTION_DAYS}d)"

echo "[$(date -Iseconds)] backup done OK"
