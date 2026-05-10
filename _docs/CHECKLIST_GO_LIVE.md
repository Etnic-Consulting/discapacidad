# Checklist go-live · SMT-ONIC

> Versión: v1.4.1 · 2026-05-10 · target dominio: `smt-onic.com`
> Audiencia: ingeniería ONIC + Wilson antes de habilitar tráfico público.

## §1 · Decisiones operativas (3)

- [ ] **D1 confirmada** · proveedor cloud o on-prem definido (Digital Ocean Droplet 8GB recomendado · ver `INSTRUCCIONES_INGENIERIA_ONIC.md §2`).
- [ ] **D2 confirmada** · custodia de secretos asignada (DB_PASSWORD, JWT_SECRET, seed creds) · password manager organizacional · rotación 90d.
- [ ] **D3 confirmada** · canal de alertas operativo (Slack/Teams + email oncall) · sin PagerDuty obligatorio v1.

## §2 · Servidor + DNS + TLS (5)

- [ ] Servidor mínimo aprovisionado · 4 vCPU · 8 GB RAM · 50 GB SSD · Ubuntu 22.04 LTS.
- [ ] Software instalado · Docker ≥20.10 · Compose v2 · git · curl · jq · nginx · certbot.
- [ ] DNS apuntando · `dig smt-onic.com` retorna IP del servidor · TTL ≤300.
- [ ] Firewall abierto · puertos 80, 443 al público · 5432 solo localhost.
- [ ] TLS válido · `sudo certbot certificates` muestra expiry ≥90 días · auto-renew en cron.

## §3 · Variables de entorno + secretos (5)

- [ ] `.env.prod` creado con todos los campos del `.env.prod.example` rellenos.
- [ ] `DB_PASSWORD` generado con `openssl rand -hex 24` · NO commiteado.
- [ ] `JWT_SECRET` generado con `openssl rand -hex 32` · NO commiteado.
- [ ] `CORS_ORIGINS` incluye `https://smt-onic.com,https://www.smt-onic.com` solamente.
- [ ] `backend/.seed_credentials.txt` creado con usuarios iniciales · password hash bcrypt · permisos 600.

## §4 · Base de datos + seeds (6)

- [ ] Postgres + PostGIS up · `docker compose ps` muestra `smt-onic-db` healthy.
- [ ] Schemas creados · `\dn` lista 10 schemas: cnpv · ext · geo · indicadores · proyecciones · pueblo · smt · smt_geo · victimas · visor_dane.
- [ ] Seeds 002-009 aplicados · `infra/init_db.sh` ejecutado sin error.
- [ ] **Seeds 010-013 aplicados** · CRÍTICO · sin ellos nacional indígena queda mal asignado a Cumaribo/Vichada (~3.7M en vez de ~1.83M).
- [ ] Validación count: `proyecciones.fac` = 8 · `proyecciones.escenarios` = 832 · `indicadores.definiciones` ≥12.
- [ ] Validación sanity: `SUM(pob_total) FROM cnpv.prevalencia_etnia_dpto WHERE grupo_etnico='Indigena'` ≈ 1.83M (NO 3.7M).

## §5 · Informes pre-renderizados + render (4)

- [ ] `backend/_static/informes/` poblado · counts esperados: macro=5 · dpto=33 · mpio=1.122 · pueblo=124-125 · resguardo=830.
- [ ] `MANIFEST.json` regenerado · contiene 2.114+ entries.
- [ ] Audit `python -m backend.scripts.audit_informes` reporta `cells_dash_pct < 5%` global · `llm_bloqueado=0` · `sin_citas=0`.
- [ ] Drift universo poblacional documentado · operador conoce que suma dpto/macro = ~2.78M es leak heredado (no bug runtime · ver `_doctrina/LECCIONES.md`).

## §6 · Backups + observabilidad (5)

- [ ] `infra/backup_db.sh` ejecutable · primera corrida exitosa · archivo en `/opt/smt-onic/backups/`.
- [ ] Cron diario configurado · `/etc/cron.d/smt-onic-backup` con run 03:00 hora Bogotá.
- [ ] Logs estructurados · `docker compose logs api` retorna JSON parseable.
- [ ] Logrotate configurado · `/etc/logrotate.d/smt-onic` rota diario, retiene 14d.
- [ ] (Opcional v1.5+) Sentry/Datadog agente instalado · diferido a sprint observabilidad.

## §7 · Smoke tests + validación end-to-end (8)

- [ ] Smoke 1 · `/api/v1/health` → 200.
- [ ] Smoke 2 · `/auth/login` con seed creds → 200 + JWT.
- [ ] Smoke 3 · `/dashboard/proyecciones` → 104 filas.
- [ ] Smoke 4 · `/dashboard/intercensal?aplicar_fac=true` → FAC aplicado.
- [ ] Smoke 5 · `/dashboard/brecha` → incluye `source_detalle`.
- [ ] Smoke 6 · `/pueblos/` SIN token → 401 Unauthorized.
- [ ] Smoke 7 · `/pueblos/` CON token → 200 + N pueblos.
- [ ] Smoke informes nuevos · `/api/v1/informes/mpio/_catalog` → 1.122 entries · `/api/v1/informes/pueblo/660` → JSON canonical TIKUNA.

## §8 · Handoff + minuta (4)

- [ ] 4 docs `_docs/*.md` accesibles · ARCHITECTURE · MATRIZ_AUTH_v1 · RUNBOOK_INCIDENTES · CHECKLIST_GO_LIVE.
- [ ] `INSTRUCCIONES_INGENIERIA_ONIC.md` v1.4.1 leído por L1 ingeniería.
- [ ] Sesión handoff 90min con Wilson realizada · 4 secciones (`§10` doc) cubiertas.
- [ ] Minuta `docs/MINUTA_HANDOFF_TEMPLATE.md` firmada · ingeniería confirma recibo + asume operación.

## Validación

Si **todos los items** están marcados ✓ → **GO-LIVE APROBADO** · habilitar DNS público.

Si quedan items pendientes → **NO go-live** · resolver pendientes · re-correr checklist.

Firma operador: ________________________
Fecha: __________