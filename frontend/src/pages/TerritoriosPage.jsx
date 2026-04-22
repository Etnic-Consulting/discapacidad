/* ============================================
   SMT-ONIC v2.0 — Territorios (Interactive Map)
   Redesigned: full-screen choropleth map with
   three toggleable layers and a collapsible
   controls panel. Now powered by FilterContext.
   ============================================ */

import { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import {
  MapContainer,
  TileLayer,
  GeoJSON,
  CircleMarker,
  Tooltip,
  useMap,
} from 'react-leaflet';
import {
  useMacrorregionesGeo,
  useResguardosGeo,
  useComunidadesGeo,
  usePueblos,
} from '../hooks/useApi';
import { useFilters } from '../context/FilterContext';
import FilterBreadcrumb from '../components/FilterBreadcrumb';
import { PUEBLOS_LIST } from '../components/GlobalSelector';

/* ================================================================
   CONSTANTS
   ================================================================ */

const MAP_CENTER = [4.0, -73.0];
const MAP_ZOOM = 6;

const TILE_URL =
  'https://basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png';
const TILE_ATTR =
  '&copy; <a href="https://carto.com/">CARTO</a> | ONIC SMT 2026';

/* Department approximate bounding boxes for zoom */
const DPTO_CENTERS = {
  '05': [6.8, -75.9],
  '08': [10.7, -75.1],
  '11': [4.6, -74.1],
  '13': [9.7, -75.1],
  '15': [5.8, -73.4],
  '17': [5.3, -75.5],
  '18': [1.5, -75.6],
  '19': [2.5, -76.8],
  '20': [9.3, -73.5],
  '23': [8.3, -75.7],
  '25': [4.9, -74.2],
  '27': [5.7, -76.7],
  '41': [2.5, -75.8],
  '44': [11.5, -72.5],
  '47': [10.4, -74.2],
  '50': [3.5, -73.0],
  '52': [1.3, -77.6],
  '54': [7.9, -72.5],
  '63': [4.5, -75.7],
  '66': [5.0, -75.7],
  '68': [7.1, -73.2],
  '70': [9.3, -75.4],
  '73': [4.0, -75.2],
  '76': [3.8, -76.5],
  '81': [7.0, -70.7],
  '85': [5.3, -72.4],
  '86': [0.8, -76.1],
  '88': [12.5, -81.7],
  '91': [-1.0, -71.9],
  '94': [3.0, -69.5],
  '95': [2.5, -72.6],
  '97': [1.0, -70.2],
  '99': [5.0, -69.5],
};

/* ---- Choropleth scale ---- */
/* Colorblind-safe sequential palette (viridis-inspired) */
const PREVALENCIA_SCALE = [
  { min: 0,   max: 20,     color: '#440154', label: 'Baja',     labelRange: '0 - 20\u2030' },
  { min: 20,  max: 40,     color: '#31688e', label: 'Moderada', labelRange: '20 - 40\u2030' },
  { min: 40,  max: 60,     color: '#35b779', label: 'Media',    labelRange: '40 - 60\u2030' },
  { min: 60,  max: 80,     color: '#fde725', label: 'Alta',     labelRange: '60 - 80\u2030' },
  { min: 80,  max: 100,    color: '#fd8d3c', label: 'Muy alta', labelRange: '80 - 100\u2030' },
  { min: 100, max: Infinity, color: '#d7191c', label: 'Critica',  labelRange: '> 100\u2030' },
];

function getPrevalenciaColor(value) {
  if (value == null || isNaN(value)) return '#ccc';
  for (const band of PREVALENCIA_SCALE) {
    if (value >= band.min && value < band.max) return band.color;
  }
  // Catch exactly 100 in the last band
  return '#d7191c';
}

function fmt(n) {
  return new Intl.NumberFormat('es-CO').format(n);
}

/* ================================================================
   INLINE STYLES
   ================================================================ */

const S = {
  /* ---- page wrapper: map takes full available height ---- */
  wrapper: {
    position: 'relative',
    height: 'calc(100vh - 90px)',
    minHeight: '500px',
    borderRadius: 'var(--radius-md)',
    overflow: 'hidden',
    boxShadow: 'var(--shadow-lg)',
  },

  /* ---- controls panel (left overlay) ---- */
  panel: (open) => ({
    position: 'absolute',
    top: '12px',
    left: '12px',
    zIndex: 1000,
    width: open ? '320px' : '0px',
    maxHeight: 'calc(100% - 24px)',
    background: 'rgba(255,255,255,0.97)',
    borderRadius: 'var(--radius-md)',
    boxShadow: 'var(--shadow-lg)',
    overflow: 'hidden',
    transition: 'width 0.3s ease',
    display: 'flex',
    flexDirection: 'column',
    backdropFilter: 'blur(6px)',
  }),
  panelInner: {
    width: '320px',
    display: 'flex',
    flexDirection: 'column',
    height: '100%',
  },
  panelHeader: {
    padding: '14px 16px 10px',
    borderBottom: '1px solid var(--color-gray-200)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    flexShrink: 0,
  },
  panelTitle: {
    fontFamily: 'var(--font-heading)',
    fontSize: '1rem',
    fontWeight: 700,
    color: 'var(--color-primary)',
  },
  panelBody: {
    padding: '12px 16px 16px',
    flex: 1,
    overflowY: 'auto',
    fontSize: '0.85rem',
  },
  closeBtn: {
    border: 'none',
    background: 'none',
    cursor: 'pointer',
    fontSize: '1.2rem',
    color: 'var(--color-gray-500)',
    padding: '2px 6px',
    lineHeight: 1,
  },

  /* ---- floating toggle button (when panel is closed) ---- */
  floatingBtn: {
    position: 'absolute',
    top: '12px',
    left: '12px',
    zIndex: 1000,
    width: '44px',
    height: '44px',
    borderRadius: 'var(--radius-md)',
    background: 'rgba(255,255,255,0.95)',
    boxShadow: 'var(--shadow-lg)',
    border: 'none',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '1.3rem',
    color: 'var(--color-primary)',
    backdropFilter: 'blur(6px)',
    transition: 'background 0.15s',
  },

  /* ---- section headers inside panel ---- */
  sectionTitle: {
    fontWeight: 600,
    fontSize: '0.72rem',
    textTransform: 'uppercase',
    letterSpacing: '0.6px',
    color: 'var(--color-gray-500)',
    marginBottom: '8px',
    marginTop: '14px',
  },

  /* ---- layer toggles ---- */
  layerRow: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    padding: '7px 0',
    cursor: 'pointer',
  },
  checkbox: {
    accentColor: 'var(--color-green-mid)',
    width: '16px',
    height: '16px',
    cursor: 'pointer',
  },
  layerLabel: {
    fontSize: '0.84rem',
    color: 'var(--color-charcoal)',
    userSelect: 'none',
  },
  layerDot: (color) => ({
    width: '10px',
    height: '10px',
    borderRadius: '50%',
    background: color,
    flexShrink: 0,
  }),

  /* ---- legend ---- */
  legendRow: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    marginBottom: '5px',
    fontSize: '0.78rem',
  },
  legendSwatch: (color) => ({
    width: '18px',
    height: '14px',
    borderRadius: '3px',
    background: color,
    border: '1px solid rgba(0,0,0,0.08)',
    flexShrink: 0,
  }),

  /* ---- select dropdown ---- */
  select: {
    width: '100%',
    padding: '7px 10px',
    border: '1px solid var(--color-gray-300)',
    borderRadius: 'var(--radius-sm)',
    fontSize: '0.82rem',
    fontFamily: 'var(--font-body)',
    background: '#fff',
    color: 'var(--color-charcoal)',
    cursor: 'pointer',
    outline: 'none',
  },

  /* ---- stats summary bar ---- */
  statsBar: {
    padding: '10px 16px',
    borderTop: '1px solid var(--color-gray-200)',
    fontSize: '0.75rem',
    color: 'var(--color-gray-500)',
    textAlign: 'center',
    fontWeight: 500,
    flexShrink: 0,
    background: 'var(--color-gray-100)',
    borderRadius: '0 0 var(--radius-md) var(--radius-md)',
  },

  /* ---- loading overlay ---- */
  loadingOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    zIndex: 900,
    background: 'rgba(247, 243, 238, 0.7)',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '12px',
    backdropFilter: 'blur(2px)',
  },
  loadingText: {
    fontSize: '0.9rem',
    color: 'var(--color-primary)',
    fontWeight: 600,
  },

  /* ---- error banner ---- */
  errorBanner: {
    position: 'absolute',
    bottom: '16px',
    left: '50%',
    transform: 'translateX(-50%)',
    zIndex: 1000,
    padding: '10px 20px',
    background: 'rgba(232, 38, 42, 0.92)',
    color: '#fff',
    borderRadius: 'var(--radius-sm)',
    fontSize: '0.85rem',
    fontWeight: 500,
    boxShadow: 'var(--shadow-md)',
    backdropFilter: 'blur(4px)',
  },

  /* ---- divider ---- */
  divider: {
    height: '1px',
    background: 'var(--color-gray-200)',
    margin: '10px 0',
  },

  /* ---- breadcrumb overlay ---- */
  breadcrumbOverlay: {
    position: 'absolute',
    top: '12px',
    right: '12px',
    zIndex: 1000,
    background: 'rgba(255,255,255,0.95)',
    padding: '6px 14px',
    borderRadius: 'var(--radius-sm)',
    boxShadow: 'var(--shadow-md)',
    backdropFilter: 'blur(6px)',
  },
};

/* ================================================================
   SUB-COMPONENTS
   ================================================================ */

/** Button to recenter map to Colombia */
function CenterButton() {
  const map = useMap();
  return (
    <button
      onClick={() => map.setView(MAP_CENTER, MAP_ZOOM, { animate: true })}
      title="Centrar en Colombia"
      aria-label="Centrar en Colombia"
      style={{
        position: 'absolute',
        bottom: '24px',
        right: '12px',
        zIndex: 1000,
        padding: '8px 14px',
        borderRadius: 'var(--radius-sm)',
        background: 'rgba(255,255,255,0.95)',
        boxShadow: 'var(--shadow-md)',
        border: '1px solid var(--color-gray-300)',
        cursor: 'pointer',
        fontSize: '0.82rem',
        fontWeight: 600,
        fontFamily: 'var(--font-body)',
        color: 'var(--color-primary)',
        backdropFilter: 'blur(6px)',
        display: 'flex',
        alignItems: 'center',
        gap: '6px',
      }}
      onMouseEnter={(e) => { e.currentTarget.style.background = 'rgba(255,255,255,1)'; }}
      onMouseLeave={(e) => { e.currentTarget.style.background = 'rgba(255,255,255,0.95)'; }}
    >
      Centrar en Colombia
    </button>
  );
}

/** Syncs map view when department/municipality filter changes */
function MapController({ dpto, mpio }) {
  const map = useMap();

  useEffect(() => {
    /* Give the container a tick to settle before invalidating */
    const timer = setTimeout(() => map.invalidateSize(), 200);
    return () => clearTimeout(timer);
  }, [map]);

  useEffect(() => {
    if (mpio) {
      // Municipality selected: zoom tighter. Use dept center with higher zoom.
      const dptoCode = dpto || (mpio ? mpio.substring(0, 2) : '');
      if (dptoCode && DPTO_CENTERS[dptoCode]) {
        map.setView(DPTO_CENTERS[dptoCode], 10, { animate: true });
      }
    } else if (dpto && DPTO_CENTERS[dpto]) {
      map.setView(DPTO_CENTERS[dpto], 8, { animate: true });
    } else if (!dpto) {
      map.setView(MAP_CENTER, MAP_ZOOM, { animate: true });
    }
  }, [dpto, mpio, map]);

  return null;
}

/** Resguardos choropleth layer with hover + click */
function ResguardosLayer({ data, selectedResguardo, pueblosList }) {
  const highlightRef = useRef(null);
  const map = useMap();

  /* If a resguardo is selected, zoom to its bounds */
  useEffect(() => {
    if (!selectedResguardo || !data?.features) return;
    const feature = data.features.find((f) => {
      const codTerr = f.properties?.cod_resguardo || f.properties?.ccdgo_terr || '';
      const territorio = f.properties?.territorio || '';
      return codTerr === selectedResguardo || territorio === selectedResguardo;
    });
    if (feature && feature.geometry) {
      try {
        // Create a temporary GeoJSON layer to get bounds
        const tempLayer = window.L?.geoJSON(feature);
        if (tempLayer) {
          const bounds = tempLayer.getBounds();
          if (bounds.isValid()) {
            map.fitBounds(bounds, { padding: [40, 40], maxZoom: 13, animate: true });
          }
        }
      } catch (_) { /* no-op */ }
    }
  }, [selectedResguardo, data, map]);

  const style = useCallback((feature) => {
    const tasa = feature?.properties?.tasa_prevalencia;
    const codTerr = feature?.properties?.cod_resguardo || feature?.properties?.ccdgo_terr || '';
    const isSelected = selectedResguardo && codTerr === selectedResguardo;
    return {
      fillColor: getPrevalenciaColor(tasa),
      fillOpacity: isSelected ? 0.85 : 0.65,
      color: isSelected ? '#C4920A' : '#ffffff',
      weight: isSelected ? 3.5 : 1.5,
      opacity: 0.9,
    };
  }, [selectedResguardo]);

  const onEachFeature = useCallback((feature, layer) => {
    const p = feature.properties || {};
    const pueblo = p.pueblo || 'Sin dato';
    const tasa = p.tasa_prevalencia;
    const tasaStr = tasa != null ? `${Number(tasa).toFixed(1)}\u2030` : '--';

    /* Tooltip on hover */
    layer.bindTooltip(
      `<div style="font-size:0.82rem;line-height:1.4">` +
        `<strong>${pueblo}</strong><br/>` +
        `Tasa: ${tasaStr}` +
      `</div>`,
      { sticky: true, direction: 'top', opacity: 0.95 }
    );

    /* Popup on click */
    const territorio = p.territorio || p.nombre || 'Resguardo';
    const departamento = p.departamento || '--';
    const municipio = p.municipio || '--';
    const poblacion = p.poblacion;
    const conCap = p.con_cap_diversas;
    /* Look up pueblo code: first from properties, then by matching name in pueblosList (API) or PUEBLOS_LIST (fallback) */
    let codPueblo = p.cod_pueblo || p.pueblo_cod || '';
    if (!codPueblo && pueblo && pueblo !== 'Sin dato') {
      const lookupList = (pueblosList && pueblosList.length > 0) ? pueblosList : PUEBLOS_LIST;
      const match = lookupList.find(
        (pl) => (pl.nombre || pl.pueblo || '').toLowerCase() === pueblo.toLowerCase()
      );
      if (match) codPueblo = match.cod || match.cod_pueblo;
    }

    const popupHtml =
      `<div style="min-width:220px;font-family:Inter,sans-serif;font-size:0.82rem;line-height:1.5">` +
        `<div style="font-size:1rem;font-weight:700;color:#02432D;margin-bottom:4px">` +
          `${pueblo}` +
        `</div>` +
        `<div style="font-size:0.85rem;color:#6B6B6B;margin-bottom:8px">` +
          `${territorio}` +
        `</div>` +
        `<div style="display:grid;grid-template-columns:1fr 1fr;gap:2px 12px;margin-bottom:8px">` +
          `<span style="color:#6B6B6B">Departamento</span><span style="font-weight:600">${departamento}</span>` +
          `<span style="color:#6B6B6B">Municipio</span><span style="font-weight:600">${municipio}</span>` +
          (poblacion != null
            ? `<span style="color:#6B6B6B">Poblacion</span><span style="font-weight:600">${fmt(poblacion)}</span>`
            : '') +
          (conCap != null
            ? `<span style="color:#6B6B6B">Con cap. diversas</span><span style="font-weight:600">${fmt(conCap)}</span>`
            : '') +
        `</div>` +
        `<div style="padding:6px 10px;background:${getPrevalenciaColor(tasa)};border-radius:4px;text-align:center;font-weight:700;font-size:0.9rem;margin-bottom:8px">` +
          `Tasa: ${tasaStr}` +
        `</div>` +
        (codPueblo
          ? `<a href="/pueblos/${codPueblo}" ` +
            `style="display:block;text-align:center;color:#02AB44;font-weight:600;font-size:0.82rem;text-decoration:none">` +
            `Ver perfil del pueblo &#8594;` +
            `</a>`
          : '') +
      `</div>`;

    layer.bindPopup(popupHtml, { maxWidth: 280 });

    /* Hover highlight */
    layer.on('mouseover', () => {
      if (highlightRef.current && highlightRef.current !== layer) {
        try { highlightRef.current.setStyle({ weight: 1.5, color: '#ffffff' }); } catch (_) { /* no-op */ }
      }
      layer.setStyle({ weight: 3, color: '#02432D' });
      layer.bringToFront();
      highlightRef.current = layer;
    });

    layer.on('mouseout', () => {
      layer.setStyle({ weight: 1.5, color: '#ffffff' });
      highlightRef.current = null;
    });
  }, [pueblosList]);

  if (!data) return null;

  return (
    <GeoJSON
      key={`layer-resguardos-${data?.features?.length ?? 0}-${selectedResguardo || ''}`}
      data={data}
      style={style}
      onEachFeature={onEachFeature}
    />
  );
}

/** Macrorregiones dashed-border overlay with labels */
function MacrorregionesLayer({ data }) {
  const style = useCallback(() => ({
    fillColor: 'transparent',
    fillOpacity: 0,
    color: '#02432D',
    weight: 2.5,
    dashArray: '8 6',
    opacity: 0.8,
  }), []);

  const onEachFeature = useCallback((feature, layer) => {
    const name = feature.properties?.macro
      || feature.properties?.nombre
      || feature.properties?.macrorregion
      || 'Macrorregion';

    layer.bindTooltip(name, {
      permanent: true,
      direction: 'center',
      className: 'macro-label',
    });
  }, []);

  if (!data) return null;

  return (
    <GeoJSON
      key={`layer-macrorregiones-${data?.features?.length ?? 0}`}
      data={data}
      style={style}
      onEachFeature={onEachFeature}
    />
  );
}

/** Community point markers */
function ComunidadesLayer({ data }) {
  if (!data || !data.features) return null;

  return (
    <>
      {data.features.map((feature, i) => {
        const p = feature.properties || {};
        const coords = feature.geometry?.coordinates;
        if (!coords) return null;
        const position = [coords[1], coords[0]]; // GeoJSON is [lng, lat]

        const personas = p.personas || 0;
        const radius = Math.max(3, Math.min(12, Math.sqrt(personas) * 0.8));

        return (
          <CircleMarker
            key={`com-${i}`}
            center={position}
            radius={radius}
            pathOptions={{
              fillColor: '#C4920A',
              fillOpacity: 0.75,
              color: '#8B6914',
              weight: 1,
              opacity: 0.9,
            }}
          >
            <Tooltip
              direction="top"
              offset={[0, -6]}
              opacity={0.95}
            >
              <div style={{ fontSize: '0.82rem', lineHeight: 1.4 }}>
                <strong>{p.nombre || 'Comunidad'}</strong><br />
                Pueblo: {p.pueblo || '--'}<br />
                Personas: {personas ? fmt(personas) : '--'}
              </div>
            </Tooltip>
          </CircleMarker>
        );
      })}
    </>
  );
}

/* ================================================================
   MAIN COMPONENT
   ================================================================ */

export default function TerritoriosPage() {
  /* ---- Filter context ---- */
  const {
    dpto, mpio, resguardo, dptoNombre, mpioNombre, resguardoNombre,
    departamentos, municipios, resguardos,
    setDpto, setMpio, setResguardo, clearAll, hasFilters,
  } = useFilters();

  /* ---- layer visibility state ---- */
  const [showMacro, setShowMacro] = useState(false);
  const [showResguardos, setShowResguardos] = useState(true);
  const [showComunidades, setShowComunidades] = useState(false);

  /* ---- panel state ---- */
  const [panelOpen, setPanelOpen] = useState(true);

  /* ---- data hooks ---- */
  const { data: apiPueblosData } = usePueblos();
  const allPueblosList = useMemo(() => {
    const raw = apiPueblosData?.data;
    if (!raw || raw.length === 0) return PUEBLOS_LIST;
    return raw.map((p) => ({ cod: p.cod_pueblo, nombre: p.pueblo }));
  }, [apiPueblosData]);

  const {
    data: macroData,
    isLoading: loadingMacro,
    isError: errorMacro,
  } = useMacrorregionesGeo();

  const {
    data: resguardosData,
    isLoading: loadingResguardos,
    isError: errorResguardos,
  } = useResguardosGeo();

  const {
    data: comunidadesData,
    isLoading: loadingComunidades,
    isError: errorComunidades,
  } = useComunidadesGeo(dpto || undefined, { enabled: showComunidades });

  /* ---- Filter resguardos by department/municipality ---- */
  const filteredResguardosData = useMemo(() => {
    if (!resguardosData?.features) return resguardosData;
    if (!dpto) return resguardosData;

    // Find department name for matching
    const dptoNameForFilter = dptoNombre;

    let filtered = resguardosData.features;

    if (dptoNameForFilter) {
      filtered = filtered.filter((f) => {
        const featureDpto = f.properties?.departamento || '';
        return featureDpto.toLowerCase().includes(dptoNameForFilter.toLowerCase())
          || dptoNameForFilter.toLowerCase().includes(featureDpto.toLowerCase());
      });
    }

    if (mpio && mpioNombre) {
      filtered = filtered.filter((f) => {
        const featureMpio = f.properties?.municipio || '';
        const featureCodMpio = f.properties?.cod_mpio || '';
        return featureCodMpio === mpio
          || featureMpio.toLowerCase().includes(mpioNombre.toLowerCase())
          || mpioNombre.toLowerCase().includes(featureMpio.toLowerCase());
      });
    }

    return {
      ...resguardosData,
      features: filtered,
    };
  }, [resguardosData, dpto, mpio, dptoNombre, mpioNombre]);

  /* ---- derived loading / error ---- */
  const isLoading =
    (showResguardos && loadingResguardos)
    || (showMacro && loadingMacro)
    || (showComunidades && loadingComunidades);

  const hasError =
    (showResguardos && errorResguardos)
    || (showMacro && errorMacro)
    || (showComunidades && errorComunidades);

  /* ---- stats summary ---- */
  const stats = useMemo(() => {
    const displayData = filteredResguardosData || resguardosData;
    const resguardoCount = displayData?.features?.length || 0;
    const pueblosSet = new Set();
    if (displayData?.features) {
      displayData.features.forEach((f) => {
        if (f.properties?.pueblo) pueblosSet.add(f.properties.pueblo);
      });
    }
    return {
      resguardos: resguardoCount,
      pueblos: pueblosSet.size || 67,
      macrorregiones: macroData?.features?.length || 5,
    };
  }, [filteredResguardosData, resguardosData, macroData]);

  /* ---- responsive: collapse panel on narrow screens ---- */
  useEffect(() => {
    const mq = window.matchMedia('(max-width: 768px)');
    if (mq.matches) setPanelOpen(false);
    const handler = (e) => { if (e.matches) setPanelOpen(false); };
    mq.addEventListener('change', handler);
    return () => mq.removeEventListener('change', handler);
  }, []);

  /* ================================================================
     RENDER
     ================================================================ */
  return (
    <div style={S.wrapper}>
      {/* ---- MAP ---- */}
      <MapContainer
        center={MAP_CENTER}
        zoom={MAP_ZOOM}
        style={{ height: '100%', width: '100%' }}
        scrollWheelZoom={true}
        zoomControl={true}
      >
        <MapController dpto={dpto} mpio={mpio} />
        <CenterButton />

        <TileLayer
          attribution={TILE_ATTR}
          url={TILE_URL}
        />

        {/* Layer 1: Macrorregiones (dashed borders, no fill) */}
        {showMacro && <MacrorregionesLayer data={macroData} />}

        {/* Layer 2: Resguardos choropleth (filtered by dept/mpio) */}
        {showResguardos && <ResguardosLayer data={filteredResguardosData} selectedResguardo={resguardo} pueblosList={allPueblosList} />}

        {/* Layer 3: Comunidades (circle markers) */}
        {showComunidades && <ComunidadesLayer data={comunidadesData} />}
      </MapContainer>

      {/* ---- LOADING OVERLAY ---- */}
      {isLoading && (
        <div style={S.loadingOverlay}>
          <div className="spinner" />
          <div style={S.loadingText}>Cargando capas territoriales...</div>
        </div>
      )}

      {/* ---- ERROR BANNER ---- */}
      {hasError && !isLoading && (
        <div style={S.errorBanner}>
          Error al cargar datos geograficos. Se muestra el mapa base.
        </div>
      )}

      {/* ---- BREADCRUMB OVERLAY ---- */}
      {hasFilters && (
        <div style={S.breadcrumbOverlay}>
          <FilterBreadcrumb />
        </div>
      )}

      {/* ---- CONTROLS PANEL ---- */}
      {panelOpen ? (
        <div style={S.panel(true)}>
          <div style={S.panelInner}>
            {/* Header */}
            <div style={S.panelHeader}>
              <span style={S.panelTitle}>Mapa Territorial</span>
              <button
                style={S.closeBtn}
                onClick={() => setPanelOpen(false)}
                title="Cerrar panel"
                aria-label="Cerrar panel de controles"
              >
                {'\u2715'}
              </button>
            </div>

            {/* Scrollable body */}
            <div style={S.panelBody}>
              {/* ---- LAYER TOGGLES ---- */}
              <div style={{ ...S.sectionTitle, marginTop: 0 }}>Capas del mapa</div>

              <label style={S.layerRow}>
                <input
                  type="checkbox"
                  checked={showResguardos}
                  onChange={() => setShowResguardos((v) => !v)}
                  style={S.checkbox}
                />
                <span style={S.layerDot('#02AB44')} />
                <span style={S.layerLabel}>Resguardos (prevalencia)</span>
              </label>

              <label style={S.layerRow}>
                <input
                  type="checkbox"
                  checked={showMacro}
                  onChange={() => setShowMacro((v) => !v)}
                  style={S.checkbox}
                />
                <span style={S.layerDot('#02432D')} />
                <span style={S.layerLabel}>Macrorregiones ONIC</span>
              </label>

              <label style={S.layerRow}>
                <input
                  type="checkbox"
                  checked={showComunidades}
                  onChange={() => setShowComunidades((v) => !v)}
                  style={S.checkbox}
                />
                <span style={S.layerDot('#C4920A')} />
                <span style={S.layerLabel}>Comunidades (puntos)</span>
              </label>

              {/* ---- COLOR LEGEND (always visible) ---- */}
              <div style={S.divider} />
              <div style={S.sectionTitle}>
                Tasa de capacidades diversas (por mil habitantes)
              </div>
              {PREVALENCIA_SCALE.map((band) => (
                <div key={band.label} style={S.legendRow}>
                  <div style={S.legendSwatch(band.color)} />
                  <span style={{ flex: 1 }}>{band.labelRange}</span>
                  <span style={{ color: 'var(--color-gray-400)', fontSize: '0.72rem' }}>
                    {band.label}
                  </span>
                </div>
              ))}

              {/* ---- INDICATOR SELECTOR (future) ---- */}
              <div style={S.divider} />
              <div style={S.sectionTitle}>Indicador</div>
              <select style={S.select} defaultValue="prevalencia_general">
                <option value="prevalencia_general">Prevalencia general</option>
                <option disabled value="por_tipo" style={{ color: 'var(--color-gray-400)' }}>
                  Por tipo de capacidad (pronto)
                </option>
                <option disabled value="conflicto" style={{ color: 'var(--color-gray-400)' }}>
                  Conflicto armado (pronto)
                </option>
              </select>

              {/* ---- DEPARTMENT FILTER (synced with global context) ---- */}
              <div style={S.divider} />
              <div style={S.sectionTitle}>Filtrar por departamento</div>
              <select
                style={S.select}
                value={dpto}
                onChange={(e) => setDpto(e.target.value)}
              >
                <option value="">Todo el pais</option>
                {departamentos.map((d) => (
                  <option key={d.cod_dpto} value={d.cod_dpto}>{d.nom_dpto}</option>
                ))}
              </select>

              {/* ---- MUNICIPALITY FILTER (only when dept selected) ---- */}
              {dpto && (
                <>
                  <div style={{ ...S.sectionTitle, marginTop: '10px' }}>Filtrar por municipio</div>
                  <select
                    style={S.select}
                    value={mpio}
                    onChange={(e) => setMpio(e.target.value)}
                  >
                    <option value="">Todos los municipios</option>
                    {municipios.map((m) => (
                      <option key={m.cod_mpio} value={m.cod_mpio}>{m.nom_mpio}</option>
                    ))}
                  </select>
                </>
              )}

              {/* ---- RESGUARDO FILTER (only when municipio selected and has resguardos) ---- */}
              {mpio && resguardos.length > 0 && (
                <>
                  <div style={{ ...S.sectionTitle, marginTop: '10px' }}>Filtrar por resguardo</div>
                  <select
                    style={S.select}
                    value={resguardo}
                    onChange={(e) => setResguardo(e.target.value)}
                  >
                    <option value="">Todos los resguardos ({resguardos.length})</option>
                    {resguardos.map((r) => (
                      <option key={r.cod_resguardo} value={r.cod_resguardo}>
                        {r.nombre}{r.pueblo_onic ? ` - ${r.pueblo_onic}` : ''}
                      </option>
                    ))}
                  </select>
                </>
              )}

              {hasFilters && (
                <button
                  onClick={clearAll}
                  style={{
                    marginTop: '10px',
                    padding: '4px 12px',
                    border: '1px solid var(--color-gray-300)',
                    borderRadius: 'var(--radius-sm)',
                    background: 'var(--color-gray-100)',
                    color: 'var(--color-gray-600)',
                    fontSize: '0.78rem',
                    cursor: 'pointer',
                    fontFamily: 'var(--font-body)',
                  }}
                >
                  Restablecer vista nacional
                </button>
              )}

              {/* DidYouKnow callout */}
              <div style={S.divider} />
              <div style={{
                background: 'var(--color-gold-light)',
                borderLeft: '3px solid var(--color-gold)',
                borderRadius: 'var(--radius-sm)',
                padding: '10px 12px',
                marginTop: '8px',
              }}>
                <div style={{ fontSize: '0.68rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.5px', color: 'var(--color-gold)', marginBottom: '4px' }}>
                  Sabias que...
                </div>
                <div style={{ fontSize: '0.78rem', fontStyle: 'italic', color: 'var(--color-charcoal)', lineHeight: 1.5, marginBottom: '4px' }}>
                  El 64.3% de las viviendas indigenas no tiene acueducto y el 96.9% no tiene internet.
                </div>
                <div style={{ fontSize: '0.68rem', color: 'var(--color-gray-500)', fontWeight: 500 }}>
                  Fuente: CNPV 2018 - DANE
                </div>
              </div>
            </div>

            {/* Stats footer */}
            <div style={S.statsBar}>
              {fmt(stats.resguardos)} resguardos &nbsp;|&nbsp; {stats.pueblos} pueblos &nbsp;|&nbsp; {stats.macrorregiones} macrorregiones
            </div>
          </div>
        </div>
      ) : (
        /* Floating button to reopen panel */
        <button
          style={S.floatingBtn}
          onClick={() => setPanelOpen(true)}
          title="Abrir controles del mapa"
          aria-label="Abrir panel de controles"
          onMouseEnter={(e) => { e.currentTarget.style.background = 'rgba(255,255,255,1)'; }}
          onMouseLeave={(e) => { e.currentTarget.style.background = 'rgba(255,255,255,0.95)'; }}
        >
          {'\u2630'}
        </button>
      )}

      {/* ---- Macrorregion label CSS (injected once) ---- */}
      <style>{`
        .macro-label {
          background: transparent !important;
          border: none !important;
          box-shadow: none !important;
          font-family: 'Playfair Display', Georgia, serif;
          font-size: 0.8rem;
          font-weight: 700;
          color: #02432D;
          text-shadow: 1px 1px 3px rgba(255,255,255,0.9), -1px -1px 3px rgba(255,255,255,0.9);
          white-space: nowrap;
          letter-spacing: 0.5px;
        }
        .macro-label::before {
          display: none;
        }

        /* Mobile: hide panel scrollbar for cleanliness */
        @media (max-width: 768px) {
          .leaflet-control-zoom {
            top: 60px !important;
          }
        }

        /* Make leaflet popup match ONIC style */
        .leaflet-popup-content-wrapper {
          border-radius: 8px !important;
          box-shadow: 0 4px 16px rgba(0,0,0,0.12) !important;
        }
        .leaflet-popup-content {
          margin: 12px 14px !important;
        }
        .leaflet-popup-tip {
          box-shadow: 0 2px 8px rgba(0,0,0,0.08) !important;
        }
      `}</style>
    </div>
  );
}
