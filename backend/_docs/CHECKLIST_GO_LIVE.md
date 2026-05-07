# Checklist · pre go-live SMT-ONIC v1.0

Lista exhaustiva de verificaciones a completar antes de anunciar la disponibilidad pública del sistema.

## §1 · Decisiones institucionales (3 decisiones)

- [ ] **D1 · Hosting confirmado** (AWS / GCP / Digital Ocean / on-prem ONIC)
- [ ] **D2 · Custodia de secretos asignada** (responsable + gestor de contraseñas + política de rotación 90 días)
- [ ] **D3 · Canal de alertas configurado** (Slack/Teams + email oncall)

## §2 · Infraestructura

- [ ] Servidor provisionado con mínimos: 4 vCPU · 8 GB RAM · 50 GB SSD · Ubuntu 22.04
- [ ] Docker ≥ 20.10 + Compose v2 instalados
- [ ] git, curl, jq, nginx, certbot instalados
- [ ] Puertos 80 y 443 abiertos al público
- [ ] Dominio `smt-onic.com` con DNS apuntando al servidor
- [ ] TLS configurado con Let's Encrypt y renovación automática

## §3 · Código y configuración

- [ ] Rama `restore/v2-styling` mergeada a `main` (o tag `v1.0.0-prod-ready` creado)
- [ ] CI verde en GitHub Actions (`.github/workflows/ci.yml`)
- [ ] `.env.prod` creado en el servidor (NO commitear)
- [ ] `DB_PASSWORD` generado con `openssl rand -hex 24`
- [ ] `JWT_SECRET` generado con `openssl rand -hex 32`
- [ ] `CORS_ORIGINS` apunta solo al dominio productivo

## §4 · Datos

- [ ] `bd_consolidada.tar.gz` recibido por canal seguro
- [ ] Checksum SHA-256 validado: `sha256sum -c bd_consolidada.sha256`
- [ ] Carga inicial ejecutada: `infra/init_db.sh` o `python -m scripts.load_all`
- [ ] Validación de counts:
  - [ ] `proyecciones.fac` = 8 filas
  - [ ] `proyecciones.escenarios` = 832 filas
  - [ ] `indicadores.definiciones` ≥ 12 filas
  - [ ] `smt_geo.resguardos` = 830 filas
  - [ ] `smt_geo.macrorregiones` = 5 filas
  - [ ] `smt.usuarios` ≥ 1 fila (admin seed)

## §5 · Smoke tests (7/7 obligatorios)

Ejecutar `./infra/smoke_tests.sh https://smt-onic.com` y verificar:

- [ ] Test 1 · `/api/v1/health` retorna `status=ok`
- [ ] Test 2 · Login retorna JWT
- [ ] Test 3 · `/proyecciones` retorna 104 filas
- [ ] Test 4 · `/intercensal?aplicar_fac=true` aplica FAC
- [ ] Test 5 · `/brecha` incluye `source_detalle`
- [ ] Test 6 · `/pueblos/` sin token = 401
- [ ] Test 7 · `/pueblos/` con token = 200

## §6 · Pruebas de aceptación funcional

- [ ] Página de login carga y permite ingreso
- [ ] Selector geográfico cascada funciona (macro → dpto → mpio → resguardo)
- [ ] Mapa de calor de Colombia se renderiza
- [ ] Pirámides poblacionales se muestran sin distorsión
- [ ] Comparador intercensal muestra ambos años
- [ ] Generación de informes HTML funciona para los 5 niveles
- [ ] Descarga de Word funciona
- [ ] Descarga de PDF funciona (requiere WeasyPrint instalado en imagen)
- [ ] Modo presentación oculta menús
- [ ] Cierre de sesión funciona

## §7 · Seguridad

- [ ] Endpoints sensibles cerrados con auth (validado por test_auth_matrix.py)
- [ ] Contraseñas semilla rotadas
- [ ] `.seed_credentials.txt` NO está commiteada (verificar `.gitignore`)
- [ ] `.env.prod` NO está commiteada
- [ ] Certificado TLS válido y A+ en SSL Labs

## §8 · Backup y recuperación

- [ ] Cron de backup diario activo en `/etc/cron.d/smt-onic-backup`
- [ ] Primer backup ejecutado y verificado en disco
- [ ] Restauración de prueba documentada (puede ser en staging)
- [ ] Si hay backup remoto: credenciales `BACKUP_REMOTE_URI` configuradas

## §9 · Observabilidad

- [ ] Logs estructurados de uvicorn visibles vía `docker compose logs`
- [ ] Health check externo (Uptime Robot, Pingdom o equivalente) configurado
- [ ] Alerta de error 5xx > umbral configurada
- [ ] Alerta de auth fails > 100/min configurada (intento de fuerza bruta)

## §10 · Documentación entregada

- [ ] `README.md` revisado por equipo ONIC
- [ ] `INSTRUCCIONES_INGENIERIA_ONIC.md` leído por ingeniería
- [ ] `_docs/RUNBOOK_INCIDENTES.md` accesible al equipo de ops
- [ ] `_docs/MATRIZ_AUTH_v1.md` revisada por seguridad ONIC
- [ ] Plantilla de minuta de handoff (`docs/MINUTA_HANDOFF_TEMPLATE.md`) firmada

## §11 · Comunicación

- [ ] Consejera de Mujer, Familia y Generación informada
- [ ] Equipo técnico interno ONIC capacitado (sesión 90 min)
- [ ] Anuncio interno a las consejerías regionales preparado
- [ ] Plan de despliegue progresivo definido (staging → producción → anuncio público)

---

**Sin todos los items en verde, el go-live se posterga.**

© EtniConsulting SAS — 2026
