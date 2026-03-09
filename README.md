# ONIC SMT — Módulo de Caracterización IM 169

**Sistema de Monitoreo Territorial · Organización Nacional Indígena de Colombia**

Dashboard interactivo para la visualización y análisis del módulo de caracterización de población indígena con discapacidad, dones, habilidades y capacidades diversas.

Financiado mediante el Convenio ONIC-AISO · Ministerio de Igualdad y Equidad · 2026.

---

## Descripción

Este módulo presenta los resultados del proceso de caracterización realizado a través de las 5 macrorregiones de la ONIC (Oriente, Occidente, Orinoquía, Amazonía, Norte), integrando:

- **1,044 registros** de personas caracterizadas
- **28+ pueblos indígenas** representados
- **38 organizaciones filiales** activas
- **11 variables** del instrumento con diccionario y evaluación de calidad
- **Sistema de 15 indicadores** para monitoreo e incidencia política

---

## Estructura del proyecto

```
onic-smt-dashboard/
├── src/
│   ├── App.jsx              # Componente principal con las 4 pestañas
│   ├── main.jsx             # Entry point React
│   ├── assets/
│   │   └── logo_ONIC.png
│   ├── data/
│   │   ├── dashboardData.js # Datos procesados desde CARACTERIZACIÓN 2026 v2.0.xlsx
│   │   ├── variables.js     # Diccionario de variables (11 variables)
│   │   ├── sources.js       # Fuentes externas y matriz de integración
│   │   └── indicators.js    # Sistema de indicadores y marco conceptual
│   └── styles/
│       └── index.css        # Design tokens y estilos globales (paleta ONIC)
├── index.html
├── vite.config.js
└── package.json
```

---

## Instalación y ejecución local

```bash
# 1. Clonar el repositorio
git clone https://github.com/TU_USUARIO/onic-smt-dashboard.git
cd onic-smt-dashboard

# 2. Instalar dependencias
npm install

# 3. Ejecutar en modo desarrollo
npm run dev

# 4. Construir para producción
npm run build
```

---

## Despliegue en GitHub Pages

```bash
# En package.json, actualizar la propiedad "homepage":
# "homepage": "https://TU_USUARIO.github.io/onic-smt-dashboard"

# Instalar gh-pages (ya incluido en devDependencies)
npm install

# Desplegar
npm run deploy
```

---

## Paleta de colores ONIC

| Token | Valor | Uso |
|-------|-------|-----|
| `--onic-red` | `#E8262A` | Acento primario, alertas, encabezado de navegación |
| `--onic-green` | `#02432D` | Verde oscuro institucional, header, fondos de sección |
| `--onic-green-mid` | `#02AB44` | Verde medio, gráficas, indicadores positivos |
| `--onic-gold` | `#C4920A` | Dorado, advertencias, dimensión étnico-cultural |
| `--cream` | `#F7F3EE` | Fondo principal |

---

## Datos fuente

Los datos provienen del archivo `CARACTERIZACIÓN 2026 v2.0.xlsx` del instrumento de recolección del SMT, con 5 hojas regionales (Oriente, Occidente, Orinoquía, Amazonía, Norte) y una hoja de definiciones. Los datos han sido normalizados y pre-procesados con Python (openpyxl, pandas) para su integración en el módulo.

**Nota de confidencialidad:** Los datos personales no se publican en este repositorio. El archivo `dashboardData.js` contiene únicamente estadísticas agregadas.

---

## Módulos del dashboard

| Pestaña | Contenido |
|---------|-----------|
| Panorama General | KPIs, gráficas por región, sexo, tipo de discapacidad, grupos etarios, certificación, pueblos, alerta de calidad |
| Diccionario de Variables | 11 fichas de variables con concepto, tipo, fuente, indicadores y evaluación de calidad |
| Fuentes de Información | 6 fuentes externas (DANE, RLCPD, ANT, RUV, SISBEN IV, AISO) y matriz de integración |
| Sistema de Indicadores | 15 indicadores en 4 dimensiones con fórmulas, metas y marco conceptual |

---

*ONIC — NIT 860.521.808-1 · Calle 12B No. 4-38, Bogotá D.C.*
