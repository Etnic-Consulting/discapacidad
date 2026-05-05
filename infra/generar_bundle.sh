#!/usr/bin/env bash
# infra/generar_bundle.sh · genera bundle de datos para deploy fresh
# ====================================================================
# Output:
#   - smt_onic.dump.gz       · pg_dump completo (BD lista para pg_restore)
#   - smt_onic.dump.sha256   · checksum
#   - bundle_meta.json       · metadata (filas por tabla · fecha · versión)
#
# Subir a DigitalOcean Spaces:
#   s3cmd put -r smt_onic.dump.gz s3://onic-smt-data/v1.0.0/
#
# Uso:
#   bash infra/generar_bundle.sh
#
# Generado: Capa H06 · 2026-05-05

set -euo pipefail

OUTPUT_DIR="${OUTPUT_DIR:-./infra/bundle}"
mkdir -p "$OUTPUT_DIR"

CONTAINER="${DB_CONTAINER:-smt-onic-db}"
DB_NAME="${DB_NAME:-smt_onic}"
DB_USER="${DB_USER:-smt_admin}"
TAG="${BUNDLE_TAG:-v1.0.0-$(date +%Y%m%d)}"

echo "[1/4] Verificando container DB activo..."
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER}$"; then
    echo "ERROR: container ${CONTAINER} no está corriendo"
    exit 1
fi

echo "[2/4] pg_dump → ${OUTPUT_DIR}/smt_onic.dump..."
docker exec "$CONTAINER" pg_dump -U "$DB_USER" -d "$DB_NAME" -Fc \
    --no-owner --no-acl \
    > "${OUTPUT_DIR}/smt_onic.dump"
DUMP_SIZE_MB=$(du -m "${OUTPUT_DIR}/smt_onic.dump" | cut -f1)
echo "   dump tamaño: ${DUMP_SIZE_MB} MB"

echo "[3/4] gzip + checksum..."
gzip -f "${OUTPUT_DIR}/smt_onic.dump"
sha256sum "${OUTPUT_DIR}/smt_onic.dump.gz" > "${OUTPUT_DIR}/smt_onic.dump.sha256"
COMPRESSED_MB=$(du -m "${OUTPUT_DIR}/smt_onic.dump.gz" | cut -f1)
echo "   comprimido: ${COMPRESSED_MB} MB"

echo "[4/4] Generando bundle_meta.json..."
docker exec "$CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -t -A -c "
SELECT json_build_object(
    'tag', '${TAG}',
    'generated_at', NOW(),
    'tables', json_agg(json_build_object(
        'schema', schemaname,
        'table', relname,
        'rows', n_live_tup
    ))
) FROM pg_stat_user_tables
WHERE schemaname IN ('cnpv', 'pueblo', 'smt_geo', 'visor_dane', 'smt', 'indicadores', 'proyecciones', 'geo', 'ext')
" > "${OUTPUT_DIR}/bundle_meta.json"

echo ""
echo "✅ Bundle generado en ${OUTPUT_DIR}/"
ls -lh "${OUTPUT_DIR}/"
echo ""
echo "Siguiente paso · subir a DigitalOcean Spaces:"
echo "  s3cmd --host=nyc3.digitaloceanspaces.com \\"
echo "        --host-bucket=%(bucket)s.nyc3.digitaloceanspaces.com \\"
echo "        put ${OUTPUT_DIR}/smt_onic.dump.gz \\"
echo "        s3://onic-smt-data/${TAG}/smt_onic.dump.gz \\"
echo "        --acl-public"
echo ""
echo "Y actualizar URL_DATA en .env.prod del servidor."
