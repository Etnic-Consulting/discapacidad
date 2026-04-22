# A6 UX Audit — Usuario No-Experto

## Resumen Ejecutivo

El dashboard SMT-ONIC presenta jerga técnica sin contextualización (CNPV, RUV, tasa x 1000, Washington Group) que desorienta usuarios sin background estadístico. Loading states ausentes en Panorama generan ansiedad. El formulario es inaccesible sin explicación de campos. Hay inconsistencia visual en errores. Mobile responsiveness limitada en mapas. Prioridad inmediata: glosario flotante, loading explícitos, tooltips en KPIs.

---

## Por página

### PanoramaPage
- **Primera impresión**: 6 KPIs grandes (bien). Pero "Cobertura SMT-ONIC 32.4%" sin contexto: ¿qué es bueno?
- **Jerga problemática**: "Prevalencia 60.0‰" (sin aclarar por mil), "Brecha certificación" (sin explicar), "CNPV 2018", "RUV", SMT-ONIC (tres fuentes sin relación clara)
- **Empty states**: isLoading spinner bien (línea 375). Pero accordion pueblo muestra spinner inline, ambiguo.
- **Affordances**: "Ver perfil completo" claro pero checkbox "Comparar" sin label visible previo
- **Accesibilidad**: Alt text ausente en Recharts, Radar tooltip letra pequeña (11px), colores insuficiente contraste
- **Mobile**: grid-6 apila en móvil pero KPICards muy tall. Pirámide sin responsive height.

### LoginPage
- **Primera impresión**: Minimalista, profesional
- **Jerga**: "Dinamizadores autorizados" sin contexto
- **Loading**: "Autenticando…" cuando loading, buen estado
- **Affordances**: Inputs con placeholder, botón claro
- **Accesibilidad**: Inputs sin aria-label explícito (tienen label pero no vinculado), error alert con role="alert" ✓, focus outline probablemente oculto
- **Mobile**: maxWidth 420px OK

### PueblosPage
- **Primera impresión**: Tabla clara con ranking + KPIs
- **Jerga**: "Confiabilidad: ALTA/MEDIA/BAJA" badges sin criterio de cálculo
- **Loading**: isLoading spinner bien
- **Affordances**: Click row navega pero sin hover visual en tabla
- **Accesibilidad**: DataTable sin caption/scope, color único para confiabilidad falla WCAG
- **Mobile**: Tabla scrollable OK

### TerritoriosPage
- **Primera impresión**: Mapa full-screen + panel. Confuso: ¿dónde empieza el tutorial?
- **Jerga**: "Macrorregión ONIC" sin contexto, 6 bandas prevalencia (Baja/Media/Alta/Crítica) parecen arbitrarias
- **Loading**: Overlay bien pero panel cerrado no muestra feedback al cargar
- **Affordances**: Panel toggle (☰) claro, pero estado no visible en botón cerrado
- **Accesibilidad**: Popups Leaflet sin focus manejado, checkboxes sin id/for, escala viridis problemática para daltónicos
- **Mobile**: Panel colapsa <768px bien, pero mapa scrolls mientras abierto crea confusión, ColombiaMap sin viewport scaling

### ConflictoPage
- **Primera impresión**: 4 KPIs + 3 gráficos bien estructurados
- **Jerga**: "Hecho victimizante" sin aclaración (desplazamiento, homicidio?), "Victimas con cap. diversas" ambiguo (¿preexistentes o adquiridas?)
- **Empty states**: allLoading muestra spinner si TODOS fallan, PERO si uno falla otros quedan en blanco sin error
- **Affordances**: Claro
- **Accesibilidad**: BarChart horizontal con labels Y largos, cortan en móvil
- **Mobile**: Margin left BarChart (120px) demasiado

### IndicadoresPage
- **Primera impresión**: 13 indicadores en tabla con semáforos. Denso pero organizado
- **Jerga**: "Consistencia intercensal" con fórmula técnica, "requiere_cruce" y "sin_valor" sin significado
- **Loading**: isLoading spinner bien
- **Affordances**: Click abre serie temporal pero sin indicador fila seleccionada
- **Accesibilidad**: Semáforo circular (14px) con color único, tabla nowrap corta en móvil, chart sin alt
- **Mobile**: Tabla scroll OK pero denso

### ProyeccionesPage
- **Primera impresión**: 4 KPIs + gráfico + selector escenarios. Balance bueno
- **Jerga**: "Escenario optimista/pesimista" sin método, "Envejecimiento +3%/año" confuso con prevalencia
- **Empty states**: API fail → FALLBACK sin avisar. SILENCIO DE DATOS.
- **Affordances**: Radios claros con descripción
- **Accesibilidad**: Domain chart [40,100] hardcoded no responsive
- **Mobile**: grid-2 OK

### VozPropiaPage
- **Primera impresión**: 4 KPIs + 2 gráficos + tabla calidad. "Desarmonia espiritual" bien contextualizado (línea 324-343)
- **Jerga**: "Desarmonia espiritual" bien explicada ✓
- **Empty states**: Fallback usado sin aviso
- **Affordances**: Claro
- **Accesibilidad**: Progress bars color único (rojo/oro/verde) falla WCAG, height 8px muy pequeño
- **Mobile**: OK

### InformesPage
- Parcialmente analizado. ReportCover con CSS print. Sin más problemas UX evidente.

### FormularioPage
- **Primera impresión**: 10 bloques A-J colores distintivos. PROBLEMA: 9 preguntas Washington Group sin contexto asustan usuario.
- **Jerga**: "Washington Group" ¿qué es?, preguntas WG escala asimétrica (1-Ninguna ... 4-No puede), "CPLI" sin regulación, "Desarmonia espiritual" no explicada en Bloque G
- **Empty states**: Progress bar bien, submit disabled durante envío ✓
- **Affordances**: SearchableSelect sin aria-describedby, WG_SCALE opciones apretadas grid 2 cols, Bloque G resaltado ✓
- **Accesibilidad**: WG preguntas sin fieldset+legend (debería agrupar 9 radios), radio labels pequeñas (0.82rem), submit sin aria-busy
- **Mobile**: Grid 2 → OK pero radios horizontales desbordan con labels largos

### PuebloDetallePage
- Parcialmente analizado. LoadingTab/ErrorTab bien hechos. Pyramid sin alt text. Acepta compact param para mobile.

---

## Patrones Transversales

1. **Jerga sin glosario**: CNPV, RUV, prevalencia, intercensal, tasa x 1000, macrorregión, ratio masculinidad, Washington Group, desarmonia espiritual, RLCPD, CPLI.
   - Solución: Glosario flotante con icono `?` en KPIs/headers.

2. **Loading states inconsistentes**: Panorama bien, Territorios bien, Conflicto parcial, Formulario indica progreso pero no envío.
   - Solución: Loading global + overlay en fetch long-running.

3. **Errores silenciosos**: Proyecciones y VozPropia usan FALLBACK sin aviso.
   - Solución: Banner naranja "Usando datos de respaldo".

4. **Inconsistencia footer**: Login con nota, otras con fuentes, formulario sin footer.
   - Solución: Footer consistente todas las páginas.

5. **Mobile limitado**: Mapa sin gestión scroll, tablas sin scroll visual, radios desbordan.
   - Solución: Media query <768px grid 1, font-size menor.

6. **Accesibilidad baja**: Recharts sin alt, colores únicos para estado, radio sin fieldset, focus oculto.
   - Solución: Auditoría WAVE, fieldsets, patrones + colores.

---

## Prioridad de Fixes

| Severidad | Página | Descripción | Fix |
|-----------|--------|-------------|-----|
| CRÍTICO | Formulario | 9 preguntas WG sin contexto asustan | Pop-up explicativo al abrir Bloque C |
| CRÍTICO | Territorios | Mapa clickeable pero no hay indicación | Tooltip "Click para popup" o banner intro |
| ALTO | Panorama | "Prevalencia 60.0‰" sin aclaración | Tooltip con promedio nacional 71.5‰ |
| ALTO | Todos | Jerga sin definición (CNPV, RUV, etc) | Glosario flotante con icono `?` |
| ALTO | Conflicto | Endpoint fail deja gráfico en blanco | Error granular por gráfico |
| ALTO | Formulario | Submit sin visual feedback | Overlay "Guardando…" + notificación |
| MEDIO | Todos | Colores únicos estado sin patrón | Agregar ícono (✓/✗/⚠) con color |
| MEDIO | Mobile | Tablas sin indicador scroll | Sombra derecha o ícono scroll |
| BAJO | Todos | Footer inconsistente | Footer consistente en todas las páginas |

