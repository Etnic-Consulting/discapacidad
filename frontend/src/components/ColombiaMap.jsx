import React, { useMemo, useEffect, useState } from 'react';
import { MapContainer, TileLayer, CircleMarker, Tooltip } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

const DEPT_CENTROIDS = {
  '05': { name: 'Antioquia',         lat:  6.85, lng: -75.71 },
  '08': { name: 'Atlántico',         lat: 10.69, lng: -74.97 },
  '11': { name: 'Bogotá D.C.',       lat:  4.65, lng: -74.10 },
  '13': { name: 'Bolívar',           lat:  8.65, lng: -74.18 },
  '15': { name: 'Boyacá',            lat:  5.77, lng: -72.96 },
  '17': { name: 'Caldas',            lat:  5.30, lng: -75.27 },
  '18': { name: 'Caquetá',           lat:  0.86, lng: -73.84 },
  '19': { name: 'Cauca',             lat:  2.40, lng: -76.83 },
  '20': { name: 'Cesar',             lat:  9.34, lng: -73.65 },
  '23': { name: 'Córdoba',           lat:  8.33, lng: -75.66 },
  '25': { name: 'Cundinamarca',      lat:  5.06, lng: -74.03 },
  '27': { name: 'Chocó',             lat:  6.55, lng: -76.99 },
  '41': { name: 'Huila',             lat:  2.53, lng: -75.52 },
  '44': { name: 'La Guajira',        lat: 11.55, lng: -72.52 },
  '47': { name: 'Magdalena',         lat: 10.41, lng: -74.40 },
  '50': { name: 'Meta',              lat:  3.34, lng: -72.95 },
  '52': { name: 'Nariño',            lat:  1.29, lng: -77.36 },
  '54': { name: 'Norte de Santander', lat: 7.95, lng: -72.89 },
  '63': { name: 'Quindío',           lat:  4.46, lng: -75.67 },
  '66': { name: 'Risaralda',         lat:  5.31, lng: -75.93 },
  '68': { name: 'Santander',         lat:  6.64, lng: -73.65 },
  '70': { name: 'Sucre',             lat:  9.06, lng: -75.10 },
  '73': { name: 'Tolima',            lat:  4.09, lng: -75.15 },
  '76': { name: 'Valle del Cauca',   lat:  3.80, lng: -76.64 },
  '81': { name: 'Arauca',            lat:  6.55, lng: -71.00 },
  '85': { name: 'Casanare',          lat:  5.75, lng: -71.57 },
  '86': { name: 'Putumayo',          lat:  0.43, lng: -75.99 },
  '88': { name: 'San Andrés',        lat: 12.55, lng: -81.71 },
  '91': { name: 'Amazonas',          lat: -1.44, lng: -71.50 },
  '94': { name: 'Guainía',           lat:  2.59, lng: -68.54 },
  '95': { name: 'Guaviare',          lat:  2.05, lng: -72.33 },
  '97': { name: 'Vaupés',            lat:  0.85, lng: -70.81 },
  '99': { name: 'Vichada',           lat:  4.71, lng: -69.41 },
};

const PALETTES = {
  green: ['#F0F7F2', '#C9E5D0', '#8FCA9F', '#4FAE6E', '#0EA84C', '#02432D'],
  red:   ['#F9E1DB', '#EFBBAE', '#D98B76', '#C65A45', '#B33A2F', '#7A231C'],
  blue:  ['#E8F1F8', '#BFD6E8', '#8FB6D6', '#5A91BE', '#2C6FA1', '#13406A'],
};

export default function ColombiaMap({
  valuesByDept = {},
  selected,
  onSelect,
  colorScale = 'green',
  height = 420,
}) {
  const palette = PALETTES[colorScale] || PALETTES.green;
  const max = useMemo(
    () => Math.max(1, ...Object.values(valuesByDept).filter((v) => Number.isFinite(v))),
    [valuesByDept]
  );

  const colorFor = (v) => {
    if (!v) return 'var(--line, #d8d4cc)';
    const idx = Math.min(palette.length - 1, Math.floor((v / max) * palette.length));
    return palette[idx];
  };

  const radiusFor = (v) => {
    if (!v) return 6;
    return 6 + Math.sqrt(v / max) * 22;
  };

  const [isMobile, setIsMobile] = useState(
    typeof window !== 'undefined' && window.matchMedia('(max-width: 768px)').matches
  );
  useEffect(() => {
    if (typeof window === 'undefined') return;
    const mq = window.matchMedia('(max-width: 768px)');
    const onChange = (e) => setIsMobile(e.matches);
    mq.addEventListener('change', onChange);
    return () => mq.removeEventListener('change', onChange);
  }, []);

  const wrapperStyle = {
    width: '100%',
    height: isMobile ? '50vh' : `${height}px`,
    maxHeight: isMobile ? '50vh' : 'none',
    borderRadius: 8,
    overflow: 'hidden',
    border: '1px solid var(--line, #e7e3db)',
  };

  return (
    <div className="map-wrapper" style={wrapperStyle}>
      <MapContainer
        center={[4.6, -74.1]}
        zoom={isMobile ? 4 : 5}
        minZoom={4}
        maxZoom={10}
        scrollWheelZoom={false}
        touchZoom={true}
        zoomControl={true}
        style={{ height: '100%', width: '100%' }}
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; OpenStreetMap'
        />
        {Object.entries(DEPT_CENTROIDS).map(([code, info]) => {
          const v = valuesByDept[code] ?? valuesByDept[info.name] ?? 0;
          const isSelected = selected === code || selected === info.name;
          return (
            <CircleMarker
              key={code}
              center={[info.lat, info.lng]}
              radius={radiusFor(v)}
              pathOptions={{
                color: isSelected ? '#000' : '#fff',
                weight: isSelected ? 2 : 1,
                fillColor: colorFor(v),
                fillOpacity: v ? 0.85 : 0.35,
              }}
              eventHandlers={
                onSelect
                  ? { click: () => onSelect(code, info.name) }
                  : undefined
              }
            >
              <Tooltip direction="top" offset={[0, -4]} sticky>
                <strong>{info.name}</strong>
                <br />
                {v ? v.toLocaleString('es-CO') : 'Sin dato'}
              </Tooltip>
            </CircleMarker>
          );
        })}
      </MapContainer>
    </div>
  );
}
