# Minuta de handoff · SMT-ONIC a equipo de ingeniería ONIC

**Fecha de la sesión:** ____________________
**Lugar / modalidad:** ____________________
**Versión del sistema entregado:** rama `restore/v2-styling` · tag `v1.0.0-prod-ready` · commit `____________`

---

## Asistentes

| Rol | Nombre | Cargo | Firma |
|---|---|---|---|
| Director del proyecto | Wilson Herrera | Coordinador SMT-ONIC | __________ |
| Ingeniería ONIC · líder | ____________________ | ____________________ | __________ |
| Ingeniería ONIC · backup | ____________________ | ____________________ | __________ |
| Custodio de secretos ONIC | ____________________ | ____________________ | __________ |
| Testigo (opcional) | ____________________ | ____________________ | __________ |

---

## §1 · Decisiones formalizadas en esta sesión

| Decisión | Valor confirmado |
|---|---|
| **D1 · Cloud target** | ☐ AWS · ☐ GCP · ☐ Azure · ☐ Digital Ocean · ☐ On-prem ONIC · ☐ Otro: __________ |
| **D2 · Custodio de secretos** | __________________________________ |
| **D3 · Canal de alertas oncall** | ☐ Slack #_______ · ☐ Email a _______ · ☐ Teams · ☐ Otro: ____________ |
| Frecuencia de backups | ☐ Diaria 03:00 hora Bogotá · ☐ Otra: __________ |
| Destino de backups remotos | __________________________________ (S3/GCS/SFTP/Drive/local-only) |
| Política de retención | ☐ 7 días · ☐ 30 días · ☐ 90 días · ☐ Otro: __________ |
| Dominio en producción | ☐ smt-onic.com (ya configurado) · ☐ Otro: __________ |
| Fecha objetivo de go-live | __________ |

---

## §2 · Lo que se entrega · checklist firmado

### Repositorio
- [ ] Código fuente · `https://github.com/Etnic-Consulting/discapacidad@restore/v2-styling`
- [ ] Tag `v1.0.0-prod-ready` creado y verificado
- [ ] CHANGELOG actualizado al commit del handoff
- [ ] CI verde en GitHub Actions

### Documentación (en repo)
- [ ] `INSTRUCCIONES_INGENIERIA_ONIC.md` (handoff 1-pager)
- [ ] `DEPLOY_PRODUCCION.md` (guía detallada · 10 secciones)
- [ ] `infra/deploy_servidor_onic.sh` (script orquestador)
- [ ] `infra/init_db.sh` (carga inicial idempotente)
- [ ] `infra/smoke_tests.sh` (7 validaciones post-deploy)
- [ ] `infra/nginx.smt-onic.conf` (config nginx lista)
- [ ] `infra/backup_db.sh` (backup diario)
- [ ] `.env.prod.example` (template de env vars)
- [ ] `docker-compose.prod.yml` (stack producción)

### Datos
- [ ] `bd_consolidada.tar.gz` (corpus 271 MB) entregado por canal seguro: ____________________
- [ ] `bd_consolidada.sha256` checksum compartido por canal separado
- [ ] Credenciales seed (`.seed_credentials.txt`) entregadas a custodio (D2)

### Conocimiento metodológico
- [ ] Walkthrough de FAC (`_docs/METODO_FAC_v1.md` en repo Visual_Agentes interno)
- [ ] Walkthrough de proyecciones Lee-Carter (`_docs/METODO_PROYECCIONES_v1.md`)
- [ ] Walkthrough de ICV ponderado (`_docs/METODO_ICV_v1.md`)
- [ ] Walkthrough de triangulación CNPV/RLCPD/SMT (`_docs/METODO_TRIANGULACION_v1.md`)
- [ ] Decisión D1 · 115 pueblos canónicos explicada (`_docs/DECISION_PUEBLOS_CANONICOS.md`)

---

## §3 · Lo que ONIC asume a partir de esta minuta

A partir de la firma, **el equipo de ingeniería ONIC asume responsabilidad** de:

1. **Operación 24/7** del dashboard en producción.
2. **Uptime** y respuesta a incidentes según runbook entregado.
3. **Backups** automáticos diarios · verificación periódica de restore.
4. **Rotación de secretos** cada 90 días (`DB_PASSWORD`, `JWT_SECRET`, PAT GitHub).
5. **Aplicación de parches de seguridad** en sistema operativo, Docker, nginx, dependencias Python/Node.
6. **Custodia de datos sensibles** · cumplimiento Habeas Data (Ley 1581/2012) y soberanía indígena de datos (CDPD ONU + Convenio 169 OIT + Decreto 1953/2014).
7. **Atención a alertas** del canal oncall (D3).
8. **Auditoría OWASP / pentest externo** antes de exposición pública (recomendado · no incluido en entregable).
9. **DPIA** (evaluación de impacto en protección de datos) si se decide exponer públicamente.

---

## §4 · Lo que el Director del proyecto retiene

- **Definición funcional** del dashboard (qué endpoints, qué KPIs, qué visualizaciones).
- **Decisiones metodológicas** (ej: D1 = 115 pueblos canónicos).
- **Validación científica** de cifras y bandas de incertidumbre.
- **Aprobación de cambios** mayores en metodología (FAC, proyecciones, ICV, triangulación).
- **Soporte de segundo nivel** durante 90 días post-handoff (consultas metodológicas).

---

## §5 · Limitaciones conocidas y deuda técnica al cierre

Anotar aquí ítems pendientes que NO bloquean go-live pero deben atenderse en v1.1:

- [ ] Sentry / Datadog / observabilidad fina (sin instalar)
- [ ] WAF / Cloudflare delante de nginx (no configurado)
- [ ] CDN para frontend estático (opcional)
- [ ] `__________________________________`
- [ ] `__________________________________`

---

## §6 · Sesión de Q&A · preguntas registradas

| # | Pregunta | Respuesta breve | Acción posterior |
|---|---|---|---|
| 1 | __________ | __________ | __________ |
| 2 | __________ | __________ | __________ |
| 3 | __________ | __________ | __________ |

---

## §7 · Próximos hitos acordados

| Hito | Responsable | Fecha objetivo |
|---|---|---|
| Provisionar servidor en cloud target (D1) | __________ | __________ |
| Primer deploy con `deploy_servidor_onic.sh` | __________ | __________ |
| Smoke tests verdes en producción | __________ | __________ |
| Configurar cron de backups | __________ | __________ |
| DNS apuntando + TLS válido | __________ | __________ |
| Anuncio interno go-live | __________ | __________ |
| Anuncio público (sitio abierto) | __________ | __________ |

---

## §8 · Firmas

Esta minuta consta de _____ páginas y los firmantes declaran:

a) Que han **revisado** el sistema entregado y la documentación.
b) Que **comprenden** el alcance, las limitaciones y la deuda técnica documentada.
c) Que **aceptan** las responsabilidades del §3 a partir de la fecha de firma.

---

**Director del proyecto**

___________________________
Wilson Herrera · `poblacion@onic.org.co`
Fecha: __________

**Líder de ingeniería ONIC**

___________________________
Nombre: __________
Cargo: __________
Fecha: __________

---

*Esta minuta debe archivarse en el sistema de gestión documental de ONIC y una copia firmada se envía a `poblacion@onic.org.co`.*
