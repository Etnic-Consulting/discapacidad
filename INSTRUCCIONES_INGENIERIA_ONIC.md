# Handoff a ingeniería ONIC · SMT-ONIC

**Para:** equipo de ingeniería ONIC que va a publicar el dashboard.
**De:** Wilson Herrera (`poblacion@onic.org.co`) · Director del proyecto.
**Repo:** https://github.com/Etnic-Consulting/discapacidad · rama `restore/v2-styling` · commit más reciente prod-ready.

---

## TL;DR · qué tienen que hacer

1. Provisionar un servidor Linux (cualquier cloud o on-prem) que cumpla los mínimos del §1.
2. Resolver las **3 decisiones pendientes** del §2 (yo no las puedo tomar por ustedes).
3. Correr el **script único** del §3 (`./infra/deploy_servidor_onic.sh`).
4. Configurar nginx + DNS + TLS según §4.
5. Validar con smoke tests del §5.

Tiempo estimado: **2-4 horas** la primera vez. Re-deploys posteriores: **15 min**.

---

## §1 · Servidor mínimo

| Recurso | Mínimo | Recomendado |
|---|---|---|
| CPU | 4 vCPU | 8 vCPU |
| RAM | 8 GB | 16 GB |
| Disco | 50 GB SSD | 100 GB SSD |
| OS | Ubuntu 22.04 LTS | Ubuntu 22.04 LTS |
| Software pre-instalado | Docker ≥ 20.10 + Compose v2 + git + curl + jq + nginx + certbot | idem |
| Puertos abiertos al público | 80, 443 | idem |
| Puertos internos | 8095 (API), 5432 (DB · solo localhost) | idem |
| Dominio | smt-onic.com con DNS apuntando al servidor | idem |

**Equivalencias cloud:** AWS EC2 `t3.large` · GCP `e2-standard-4` · Azure `B4ms` · Digital Ocean `s-4vcpu-8gb` · on-prem cualquier VM o bare-metal con esos mínimos.

---

## §2 · 3 decisiones que ONIC debe tomar antes de deploy

Estas 3 no las puedo tomar yo. Necesito que ingeniería las confirme:

### Decisión D1 · ¿Dónde se hostea?

| Opción | Costo aprox/mes USD | Pros | Contras |
|---|---|---|---|
| **AWS EC2 t3.large + RDS** | ~80-120 | Familiar para muchos · ecosistema maduro | Requiere expertise IAM |
| **GCP Compute Engine e2-standard-4** | ~70-100 | Buenos free tiers iniciales | Curva de IAM |
| **Digital Ocean Droplet 8GB** | ~48 | Más simple · 1-click PostgreSQL | Menos features enterprise |
| **On-prem ONIC** | $0 marginal | Control total · datos sensibles indígenas no salen | ONIC asume backups + uptime + DR |

**Recomendación si no hay opinión fuerte:** Digital Ocean por simplicidad, o on-prem ONIC si hay infraestructura disponible (los datos étnicos son sensibles · CDPD ONU + Convenio 169 OIT respaldan soberanía indígena de datos).

### Decisión D2 · ¿Quién custodia secretos?

`DB_PASSWORD`, `JWT_SECRET`, credenciales de cuentas de usuario inicial (`backend/.seed_credentials.txt`).

**Recomendación:** alguien del equipo de ingeniería ONIC los genera, los guarda en un password manager (Bitwarden/1Password de la organización), y los rota cada 90 días. **NO** Wilson, **NO** consultor externo.

### Decisión D3 · ¿Quién recibe alertas en producción?

API caída, errores 5xx, disco lleno, intento de fuerza bruta en /auth.

**Recomendación:** mínimo un canal de Slack/Teams + un email de oncall. No hace falta PagerDuty para v1.

---

## §3 · Deploy en un script

**Pre-requisito:** archivo `.env.prod` configurado (copiar de `.env.prod.example` y rellenar).

```bash
# Una sola vez · primer deploy
git clone -b restore/v2-styling https://github.com/Etnic-Consulting/discapacidad.git smt-onic
cd smt-onic
cp .env.prod.example .env.prod
$EDITOR .env.prod   # rellenar DB_PASSWORD, JWT_SECRET, DOMAIN

# Setear URL del corpus de datos (Wilson lo entrega por canal seguro · Drive/SFTP)
export URL_DATA="https://<canal-seguro>/bd_consolidada.tar.gz"
export EXPECTED_SHA256="<sha256-que-Wilson-entrega-aparte>"

# Ejecutar el orquestador
chmod +x infra/deploy_servidor_onic.sh
./infra/deploy_servidor_onic.sh
```

> **Nota v1.4.1 · migraciones de integridad de datos (seeds 010-013)**
>
> El despliegue aplica 13 seeds SQL idempotentes en `backend/sql/` (002-013). Los 4 fixes críticos son:
>
> - `010_fix_seed_99773_agregado_nacional.sql` y `011_fix_dpto_99_agregados_nacionales.sql` corrigen un error en el seed CNPV 2018 donde los datos nacionales indígenas fueron asignados incorrectamente al `cod_mpio=99773` (Cumaribo) y al `cod_dpto=99` (Vichada). Sin estos, el total nacional indígena suma ~3.7M en vez de ~1.83M esperado.
> - `012_smt_resumen.sql` crea vista materializada para dashboard SMT (`/voz-propia` y `/panorama`).
> - `013_fix_trigger_dim_dptos.sql` arregla trigger que refresca FK al insertar dptos.
>
> El script `infra/init_db.sh` los aplica en orden automáticamente (T10 · 2026-05-10 · fix bug donde solo aplicaba 002-009). Incluye sanity check 7b validando que el agregado nacional indígena esté en rango 1.7M-2.0M. Si la suma da >3M, las migraciones 010-011 no se aplicaron · re-correr `init_db.sh` es idempotente.

El script `deploy_servidor_onic.sh`:
1. Valida pre-requisitos (docker, jq, curl, env vars).
2. Levanta DB (PostGIS).
3. Corre `infra/init_db.sh` (descarga corpus · checksum · seeds 001-011 en orden · `load_all.py` · validación de counts).
4. Levanta API.
5. Construye frontend estático (`npm run build` → `frontend/dist/`).
6. Corre `infra/smoke_tests.sh` (7 tests del §5).
7. Reporta status. Exit 0 = listo · Exit 1 = abortar y revisar logs.

**Re-deploys** (cuando ONIC haga merge a `main` o reciba un tag `v*`):
```bash
cd smt-onic
git pull origin main
docker compose --env-file .env.prod build api
docker compose --env-file .env.prod up -d
./infra/smoke_tests.sh https://smt-onic.com
```

**Re-deploys automáticos vía GitHub Actions** (opcional · cuando ONIC esté listo):
1. En GitHub repo Settings → Secrets, agregar: `PROD_SSH_HOST`, `PROD_SSH_USER`, `PROD_SSH_KEY`, `PROD_DEPLOY_PATH`.
2. En Settings → Variables, crear variable `DEPLOY_ENABLED=true`.
3. A partir de ese punto, cualquier tag `v*` empujado al repo dispara `deploy.yml` que construye imagen + SSH al servidor + pull + restart + smoke tests.
4. Si la variable `DEPLOY_ENABLED` no existe o es distinta de `true`, el workflow solo publica la imagen Docker en GHCR (no toca el servidor) · útil mientras se configura el cloud.

---

## §4 · Nginx + TLS

```bash
# 4.1 · Copiar config de nginx
sudo cp infra/nginx.smt-onic.conf /etc/nginx/sites-available/smt-onic
sudo ln -sf /etc/nginx/sites-available/smt-onic /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# 4.2 · Copiar frontend al docroot
sudo mkdir -p /var/www/smt-onic-frontend
sudo cp -r frontend/dist/* /var/www/smt-onic-frontend/

# 4.3 · TLS via Let's Encrypt
sudo certbot --nginx -d smt-onic.com -d www.smt-onic.com \
  --agree-tos -m poblacion@onic.org.co --no-eff-email

# 4.4 · Recargar nginx
sudo nginx -t && sudo systemctl reload nginx
```

Config de nginx en `infra/nginx.smt-onic.conf` (incluida en el repo).

---

## §5 · Smoke tests post-deploy

```bash
./infra/smoke_tests.sh https://smt-onic.com
```

Valida en orden:
1. `/api/v1/health` responde 200.
2. Login retorna JWT.
3. `/dashboard/proyecciones` retorna 104 filas (8 grupos × FAC × 26 años / etnia).
4. `/dashboard/intercensal?aplicar_fac=true` aplica FAC correctamente.
5. `/dashboard/brecha` incluye `source_detalle` por paso.
6. `/pueblos/` sin token retorna **401** (auth correctamente cerrada).
7. `/pueblos/` con token retorna 200 con N pueblos.

**Smoke informes v1.4.1** (nuevos · validar tras re-render multinivel):

8. `/api/v1/informes/mpio/_catalog` retorna **1.122** entries.
9. `/api/v1/informes/pueblo/660` retorna JSON canonical con `tipo:"pueblo"`, `nombre:"TIKUNA"`, `con_disc:397`.
10. `/api/v1/informes/MANIFEST.json` retorna **2.127** informes totales (5 macro + 33 dpto + 1.122 mpio + 137 pueblo + 830 resguardo).

Exit 0 = go-live OK · Exit 1 = abortar y rollback (ver `DEPLOY_PRODUCCION.md §7`).

---

## §6 · Backups (configurar día 1 · NO opcional)

Programar en cron del servidor:

```bash
# /etc/cron.d/smt-onic-backup · diario 03:00 hora Bogotá
0 3 * * * deploy /opt/smt-onic/infra/backup_db.sh >> /var/log/smt-onic-backup.log 2>&1
```

Script `infra/backup_db.sh` (incluido) hace `pg_dump` y rota a 7 días locales + sube a S3/GCS si `BACKUP_REMOTE_URI` está seteado.

---

## §7 · Lo que NO está incluido y ONIC debe agregar

- **Sentry / Datadog / New Relic** para observabilidad fina (la app ya emite logs estructurados a stdout · falta el agente).
- **WAF / Cloudflare** delante de nginx (recomendado por sensibilidad de datos étnicos).
- **CDN** para `frontend/dist/` (opcional · el sitio es liviano).
- **Auditoría OWASP / pentest externo** antes de go-live público (recomendado · CDPD ONU implica deber de cuidado reforzado).
- **Política de retención de datos** (CNPV es público pero la triangulación con SMT no · ONIC debe documentar).
- **DPIA** (evaluación de impacto en protección de datos · Habeas Data Ley 1581/2012).

---

## §8 · Cuando algo falla

| Síntoma | Diagnóstico | Acción |
|---|---|---|
| `docker info` falla | Docker daemon caído | `sudo systemctl start docker` |
| Smoke test 1 falla (`/health`) | API no responde | `docker compose logs api --tail=50` |
| Smoke test 3 falla (`/proyecciones` total=0) | Seeds no aplicados | Re-correr `./infra/init_db.sh` (idempotente) |
| Smoke test 6 falla (auth abierta) | T24 no mergeado | Verificar commit `8d1c526` está en HEAD |
| Frontend muestra `—` en KPIs | API no responde o CORS | Revisar `CORS_ORIGINS` en `.env.prod` |
| `nginx -t` falla | Config rota | Restaurar `/etc/nginx/sites-available/smt-onic` desde repo |
| TLS expirado | certbot no renovó | `sudo certbot renew` (debería estar en cron auto) |

Más detalle en `DEPLOY_PRODUCCION.md §7-§9` y `_docs/RUNBOOK_INCIDENTES.md`.

---

## §9 · Documentación complementaria en el repo

**Disponibles en `_docs/` (v1.4.1)**:

- `DEPLOY_PRODUCCION.md` (raíz) — guía detallada de deploy (10 secciones · referencia profunda).
- `_docs/ARCHITECTURE.md` — topología 3 capas + schemas DB + flujo datos + auth flow JWT.
- `_docs/MATRIZ_AUTH_v1.md` — endpoints públicos vs auth vs admin con rationale doctrinal.
- `_docs/RUNBOOK_INCIDENTES.md` — 10 incidentes típicos con diagnóstico + acción + escalation.
- `_docs/CHECKLIST_GO_LIVE.md` — 40 items binarios pre-go-live.

**Diferidos** (notas metodológicas internas · Wilson entrega aparte si ingeniería los necesita):

- `_docs/METODO_FAC_v1.md` — metodología FAC (responde "¿de dónde sale el 0.939?") · pendiente extraer de notas internas.
- `_docs/METODO_PROYECCIONES_v1.md` — Lee-Carter aproximada (bandas IC ±15%) · pendiente.
- `_docs/DECISION_PUEBLOS_CANONICOS.md` — D1 = 115 pueblos (vs 121 vs 102) · pendiente.

---

## §10 · Sesión de handoff sugerida (90 min)

Cuando el equipo ONIC esté listo, agendar una sesión con Wilson para:

1. **20 min** · Walkthrough de arquitectura: `_docs/ARCHITECTURE.md` y este doc.
2. **30 min** · Deploy en vivo en un servidor de staging ONIC siguiendo §3-§5.
3. **20 min** · Q&A sobre datos sensibles, auditoría, decisiones D1/D2/D3.
4. **20 min** · Firma de minuta de handoff: ingeniería confirma que recibe el sistema, sabe operarlo, y asume responsabilidad de uptime/backups/security.

Plantilla de minuta en `docs/MINUTA_HANDOFF_TEMPLATE.md`.

---

**Contacto Director:** Wilson Herrera · `poblacion@onic.org.co`
**Repo:** https://github.com/Etnic-Consulting/discapacidad
**Estado al cierre:** rama `restore/v2-styling` · tag estable **v1.4.1** (2026-05-10) · Sprint S9_render_multinivel cerrado (7+13 tareas ENTREGADO) · **2.127 informes pre-renderizados** con lógica W12-honesta (k-anonimato real · JSON canonical con `_meta` trazable · 4 huérfanos cubiertos con `_sin_datos:true`). `init_db.sh` aplica seeds 002-013 (los 4 fixes 010-013 son CRÍTICOS · sin ellos nacional indígena queda mal asignado). 4 docs nuevos en `_docs/` (ARCHITECTURE, MATRIZ_AUTH_v1, RUNBOOK_INCIDENTES, CHECKLIST_GO_LIVE).

**Deuda conocida heredada (no bloqueante go-live)**: drift universo poblacional `pueblo.disc_dpto` +46% (afros/sin-pertenencia leak) · NO filtrable runtime (tabla sin `grupo_etnico`) · documentado en `_doctrina/LECCIONES.md` Caso 11 (motor Visual_Agentes) + `_docs/RUNBOOK_INCIDENTES.md` Incidente 10. Sprint S10 dedicado para fix REDATAM re-extracción.
