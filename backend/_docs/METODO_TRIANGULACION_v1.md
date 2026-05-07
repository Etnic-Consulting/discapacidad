# Metodología · Triangulación CNPV / RLCPD / SMT

## Problema

Tres registros administrativos miden capacidades diversas en Colombia con criterios distintos:

| Fuente | Universo | Criterio | Cobertura indígena |
|---|---|---|---|
| **CNPV 2018** | Todo Colombia | Autorreporte (Washington Group) | ~110.000 personas indígenas |
| **RLCPD** (Registro de Localización y Caracterización de Personas con Discapacidad) | Personas con certificado de discapacidad vigente | Diagnóstico clínico + entrevista en EPS | Cobertura territorial sesgada |
| **SMT-ONIC** | Población indígena | Caracterización propia ONIC | Captura primaria desde territorios |

## Triangulación

La triangulación cruza las tres fuentes para producir indicadores robustos por territorio:

```
embudo_certificacion[territorio] = {
   "censo_autorreporte": cnpv[territorio].n_disc,
   "registro_oficial": rlcpd[territorio].n_certificado_vigente,
   "smt_onic": smt[territorio].n_caracterizado,
   "tasa_certificacion": rlcpd / cnpv,
   "tasa_caracterizacion_smt": smt / cnpv
}
```

## Almacenamiento

`smt.resumen` (40 filas) contiene los valores triangulados por departamento, con campos:

- `cod_dpto`, `nom_dpto`
- `cnpv_disc_total`
- `rlcpd_certificados`
- `smt_caracterizados`
- `tasa_certificacion_pct`
- `gap_smt_cnpv`
- `fecha_corte`

## Hallazgo clave

La **tasa de certificación** (% de personas con autorreporte de capacidad diversa que tienen certificado RLCPD vigente) es **inferior al 30 %** en la mayoría de departamentos con presencia indígena alta. Esto indica una brecha significativa entre derecho declarado y derecho ejercido, y justifica la incidencia política de la Consejería de Mujer, Familia y Generación.

## Visualización en frontend

- **Embudo de certificación** en página Panorama (`PanoramaPage.jsx`).
- Tabla de triangulación por departamento en página Indicadores.

## Limitaciones

1. El RLCPD tiene actualización por EPS con frecuencia heterogénea · datos pueden estar rezagados 6-18 meses.
2. La caracterización SMT-ONIC depende de la presencia de dinamizadores en territorio · cobertura no homogénea entre macrorregiones.
3. La triangulación a nivel municipio requiere k-anonimato ≥ 5 para evitar re-identificación.

## Referencias

- Minsalud · Sistema RLCPD.
- DANE · CNPV 2018 microdatos.
- ONIC · Sistema de Monitoreo Territorial.

---

© EtniConsulting SAS — 2026
