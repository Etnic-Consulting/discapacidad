/* Static dataset from CNPV 2018 + SMT-ONIC — used as fallback when API is unavailable */

export const KPI_NACIONAL = {
  totalPersonas: 225174,
  pueblos: 121,
  prevalencia: 60.0,
  coberturaRegistro: 32.4,
  brechaCertificacion: 71.3,
  victimasConflicto: 37797,
  poblacionIndigenaTotal: 1905617,
};

export const PREVALENCIA_ETNICA = [
  { grupo: 'Indígena 2005', prevalencia: 59.2, color: '#02432D' },
  { grupo: 'Indígena 2018', prevalencia: 60.0, color: '#02AB44' },
  { grupo: 'Afro 2005',     prevalencia: 64.8, color: '#C4920A' },
  { grupo: 'Afro 2018',     prevalencia: 66.4, color: '#E8B84B' },
  { grupo: 'General 2005',  prevalencia: 77.6, color: '#6B6B6B' },
  { grupo: 'General 2018',  prevalencia: 71.5, color: '#A0A0A0' },
];

export const DIFICULTADES_WG = [
  { dificultad: 'Ver',          value: 37.2 },
  { dificultad: 'Caminar',      value: 30.1 },
  { dificultad: 'Oír',          value: 15.8 },
  { dificultad: 'Act. diarias', value: 14.2 },
  { dificultad: 'Agarrar',      value: 12.4 },
  { dificultad: 'Autocuidado',  value: 11.6 },
  { dificultad: 'Aprender',     value: 10.5 },
  { dificultad: 'Comunicarse',  value: 9.8  },
  { dificultad: 'Relacionarse', value: 7.3  },
];

export const SEXO_DATA = [
  { name: 'Hombres', value: 53.2, color: '#02432D' },
  { name: 'Mujeres', value: 46.8, color: '#C4920A' },
];

export const EDAD_DATA = [
  { rango: '0-4',   personas: 5420  },
  { rango: '5-14',  personas: 18340 },
  { rango: '15-24', personas: 22150 },
  { rango: '25-34', personas: 24800 },
  { rango: '35-44', personas: 28600 },
  { rango: '45-54', personas: 35400 },
  { rango: '55-64', personas: 38200 },
  { rango: '65-74', personas: 32100 },
  { rango: '75+',   personas: 20164 },
];

export const PIRAMIDE = [
  { grupo: '0-4',   h: 2890,  m: 2530  },
  { grupo: '5-14',  h: 9820,  m: 8520  },
  { grupo: '15-24', h: 11780, m: 10370 },
  { grupo: '25-34', h: 13180, m: 11620 },
  { grupo: '35-44', h: 15200, m: 13400 },
  { grupo: '45-54', h: 18820, m: 16580 },
  { grupo: '55-64', h: 20330, m: 17870 },
  { grupo: '65-74', h: 17070, m: 15030 },
  { grupo: '75+',   h: 10720, m: 9444  },
];

export const FUNNEL_STEPS = [
  { label: 'Población indígena total',             value: 1905617, color: '#02AB44', source: 'CNPV 2018',           width: 100 },
  { label: 'Con capacidades diversas (CNPV 2018)', value: 225174,  color: '#C4920A', source: 'CNPV 2018',           width: 85  },
  { label: 'Registrados en RLCPD',                 value: 39374,   color: '#E8862A', source: 'MinSalud RLCPD',      width: 40,
    gap: '185.800 personas no están registradas en el RLCPD' },
  { label: 'Caracterizados por SMT-ONIC',          value: 1044,    color: '#E8262A', source: 'SMT-ONIC 2026',       width: 15,
    gap: '~38.330 personas registradas en RLCPD no caracterizadas por el SMT' },
  { label: 'Con certificado oficial',              value: 428,     color: '#8B1A1A', source: 'SMT-ONIC 2026 (calc.)', width: 5,
    gap: '616 personas caracterizadas aún no tienen certificado' },
];

export const PUEBLOS = [
  { cod: '720', nombre: 'Wayuu',        poblacion: 380460, conCapDiv: 4831,  prevalencia: 12.7,  confiabilidad: 'ALTA',  departamentos: ['44'] },
  { cod: '500', nombre: 'Nasa',         poblacion: 243176, conCapDiv: 16531, prevalencia: 68.0,  confiabilidad: 'ALTA',  departamentos: ['19', '73'] },
  { cod: '800', nombre: 'Zenú',         poblacion: 307091, conCapDiv: 14867, prevalencia: 48.4,  confiabilidad: 'ALTA',  departamentos: ['23'] },
  { cod: '560', nombre: 'Pastos',       poblacion: 163873, conCapDiv: 11273, prevalencia: 68.8,  confiabilidad: 'ALTA',  departamentos: ['52'] },
  { cod: '282', nombre: 'Embera Chamí', poblacion: 95077,  conCapDiv: 5324,  prevalencia: 56.0,  confiabilidad: 'ALTA',  departamentos: ['76', '66'] },
  { cod: '280', nombre: 'Embera',       poblacion: 50041,  conCapDiv: 3502,  prevalencia: 70.0,  confiabilidad: 'ALTA',  departamentos: ['27'] },
  { cod: '200', nombre: 'Pijao',        poblacion: 36281,  conCapDiv: 2542,  prevalencia: 70.1,  confiabilidad: 'ALTA',  departamentos: ['73'] },
  { cod: '580', nombre: 'Sikuani',      poblacion: 33112,  conCapDiv: 1854,  prevalencia: 56.0,  confiabilidad: 'MEDIA', departamentos: ['50', '99'] },
  { cod: '281', nombre: 'Embera Katío', poblacion: 32899,  conCapDiv: 1850,  prevalencia: 56.2,  confiabilidad: 'ALTA',  departamentos: ['27', '23'] },
  { cod: '210', nombre: 'Awá',          poblacion: 25813,  conCapDiv: 1484,  prevalencia: 57.5,  confiabilidad: 'ALTA',  departamentos: ['52'] },
  { cod: '820', nombre: 'Mokaná',       poblacion: 21817,  conCapDiv: 1410,  prevalencia: 64.6,  confiabilidad: 'MEDIA', departamentos: ['08'] },
  { cod: '750', nombre: 'Yanacona',     poblacion: 20062,  conCapDiv: 1504,  prevalencia: 75.0,  confiabilidad: 'ALTA',  departamentos: ['19'] },
  { cod: '040', nombre: 'Arhuaco',      poblacion: 33562,  conCapDiv: 1310,  prevalencia: 39.0,  confiabilidad: 'ALTA',  departamentos: ['47', '20'] },
  { cod: '290', nombre: 'Misak',        poblacion: 18000,  conCapDiv: 1350,  prevalencia: 75.0,  confiabilidad: 'ALTA',  departamentos: ['19'] },
  { cod: '340', nombre: 'Inga',         poblacion: 18615,  conCapDiv: 1130,  prevalencia: 60.7,  confiabilidad: 'ALTA',  departamentos: ['86'] },
  { cod: '350', nombre: 'Kamëntsá',     poblacion: 9890,   conCapDiv: 1321,  prevalencia: 133.5, confiabilidad: 'ALTA',  departamentos: ['86'] },
  { cod: '050', nombre: 'Wiwa',         poblacion: 9872,   conCapDiv: 502,   prevalencia: 50.9,  confiabilidad: 'MEDIA', departamentos: ['47'] },
  { cod: '850', nombre: 'Kankuamo',     poblacion: 18121,  conCapDiv: 925,   prevalencia: 51.0,  confiabilidad: 'ALTA',  departamentos: ['20'] },
  { cod: '370', nombre: 'Kogui',        poblacion: 14799,  conCapDiv: 580,   prevalencia: 39.2,  confiabilidad: 'MEDIA', departamentos: ['47'] },
  { cod: '710', nombre: 'Wounaan',      poblacion: 12595,  conCapDiv: 812,   prevalencia: 64.5,  confiabilidad: 'ALTA',  departamentos: ['27', '76'] },
  { cod: '660', nombre: 'Tikuna',       poblacion: 7879,   conCapDiv: 412,   prevalencia: 52.3,  confiabilidad: 'MEDIA', departamentos: ['91'] },
  { cod: '690', nombre: "U'wa",         poblacion: 7581,   conCapDiv: 85,    prevalencia: 11.2,  confiabilidad: 'MEDIA', departamentos: ['81', '54'] },
  { cod: '220', nombre: 'Cubeo',        poblacion: 6678,   conCapDiv: 320,   prevalencia: 47.9,  confiabilidad: 'MEDIA', departamentos: ['97'] },
  { cod: '470', nombre: 'Muisca',       poblacion: 14051,  conCapDiv: 892,   prevalencia: 63.5,  confiabilidad: 'ALTA',  departamentos: ['11', '25'] },
  { cod: '730', nombre: 'Murui',        poblacion: 6449,   conCapDiv: 284,   prevalencia: 44.0,  confiabilidad: 'MEDIA', departamentos: ['91', '86'] },
  { cod: '250', nombre: 'Curripaco',    poblacion: 4928,   conCapDiv: 213,   prevalencia: 43.2,  confiabilidad: 'MEDIA', departamentos: ['94'] },
  { cod: '240', nombre: 'Cuna Tule',    poblacion: 2383,   conCapDiv: 162,   prevalencia: 68.0,  confiabilidad: 'MEDIA', departamentos: ['27'] },
  { cod: '320', nombre: 'Jiw',          poblacion: 1200,   conCapDiv: 105,   prevalencia: 87.5,  confiabilidad: 'MEDIA', departamentos: ['95'] },
  { cod: '430', nombre: 'Nukak',        poblacion: 1080,   conCapDiv: 32,    prevalencia: 29.6,  confiabilidad: 'BAJA',  departamentos: ['95'] },
  { cod: '400', nombre: 'Hitnu',        poblacion: 705,    conCapDiv: 44,    prevalencia: 62.4,  confiabilidad: 'BAJA',  departamentos: ['81'] },
];

export const RESGUARDOS = [
  { cod: 'R001', nombre: 'Gran Resguardo Wayuu de Alta y Media Guajira', dpto: '44', pueblo: '720', poblacion: 150230, area: 1067505, estCapDiv: 1908 },
  { cod: 'R002', nombre: 'Resguardo Toribío',                            dpto: '19', pueblo: '500', poblacion: 37212,  area: 18260,   estCapDiv: 2530 },
  { cod: 'R003', nombre: 'Resguardo Caldono',                            dpto: '19', pueblo: '500', poblacion: 14830,  area: 12500,   estCapDiv: 1008 },
  { cod: 'R004', nombre: 'Resguardo de Cumbal',                          dpto: '52', pueblo: '560', poblacion: 21404,  area: 21350,   estCapDiv: 1473 },
  { cod: 'R005', nombre: 'Resguardo Arhuaco Sierra Nevada',              dpto: '47', pueblo: '040', poblacion: 28130,  area: 195900,  estCapDiv: 1097 },
  { cod: 'R006', nombre: 'Resguardo de Guambia',                         dpto: '19', pueblo: '290', poblacion: 16480,  area: 20150,   estCapDiv: 1236 },
  { cod: 'R007', nombre: 'Resguardo de Pueblo Bello',                    dpto: '20', pueblo: '040', poblacion: 8950,   area: 45200,   estCapDiv: 349  },
  { cod: 'R008', nombre: 'Resguardo Puerto Nariño',                      dpto: '91', pueblo: '660', poblacion: 6210,   area: 36100,   estCapDiv: 325  },
];

export const CONFLICTO_DPTO = [
  { dpto: 'Cauca',      victimas: 8940 },
  { dpto: 'Nariño',     victimas: 6120 },
  { dpto: 'La Guajira', victimas: 4830 },
  { dpto: 'Chocó',      victimas: 4310 },
  { dpto: 'Antioquia',  victimas: 3450 },
  { dpto: 'Putumayo',   victimas: 2890 },
  { dpto: 'Tolima',     victimas: 2120 },
  { dpto: 'Huila',      victimas: 1480 },
  { dpto: 'Caldas',     victimas: 1210 },
  { dpto: 'Otros',      victimas: 2447 },
];

export const HECHOS_CONFLICTO = [
  { hecho: 'Desplazamiento forzado', pct: 74.9 },
  { hecho: 'Homicidio',              pct: 10.1 },
  { hecho: 'Amenaza',                pct: 6.1  },
  { hecho: 'Desaparición forzada',   pct: 3.8  },
  { hecho: 'Minas antipersonal',     pct: 2.6  },
  { hecho: 'Confinamiento',          pct: 1.3  },
  { hecho: 'Otros',                  pct: 1.0  },
];

export const PROYECCIONES = [
  { anio: 2005, poblacion: 1392623, conCapDiv: 82473,  prev: 59.2 },
  { anio: 2010, poblacion: 1580000, conCapDiv: 102700, prev: 65.0 },
  { anio: 2015, poblacion: 1750000, conCapDiv: 128620, prev: 73.5 },
  { anio: 2018, poblacion: 1905617, conCapDiv: 225174, prev: 118.2 },
  { anio: 2020, poblacion: 1980000, conCapDiv: 142400, prev: 71.9 },
  { anio: 2023, poblacion: 2080000, conCapDiv: 156500, prev: 75.2 },
  { anio: 2026, poblacion: 2180000, conCapDiv: 170200, prev: 78.0 },
];

export const INDICADORES = [
  { cat: 'Salud',      code: 'SAL-01', nombre: 'Cobertura de salud efectiva',   valor: 42.3, meta: 90,  estado: 'critico' },
  { cat: 'Salud',      code: 'SAL-02', nombre: 'Acceso a medicina propia',       valor: 67.5, meta: 100, estado: 'medio' },
  { cat: 'Educación',  code: 'EDU-01', nombre: 'Tasa de analfabetismo (≥15)',    valor: 28.4, meta: 5,   estado: 'critico', invertido: true },
  { cat: 'Educación',  code: 'EDU-02', nombre: 'Permanencia secundaria',         valor: 54.2, meta: 90,  estado: 'medio' },
  { cat: 'Territorio', code: 'TER-01', nombre: 'Tenencia resguardo titulado',    valor: 73.8, meta: 100, estado: 'bueno' },
  { cat: 'Territorio', code: 'TER-02', nombre: 'Acceso a agua potable',          valor: 38.1, meta: 95,  estado: 'critico' },
  { cat: 'Cultura',    code: 'CUL-01', nombre: 'Hablantes de lengua materna',    valor: 61.2, meta: 85,  estado: 'medio' },
  { cat: 'Cultura',    code: 'CUL-02', nombre: 'Prácticas de partería propia',   valor: 45.6, meta: 70,  estado: 'medio' },
  { cat: 'DDHH',       code: 'DDH-01', nombre: 'Denuncias atendidas',            valor: 82.0, meta: 100, estado: 'bueno' },
  { cat: 'DDHH',       code: 'DDH-02', nombre: 'Casos con certificado víctima',  valor: 28.9, meta: 90,  estado: 'critico' },
  { cat: 'Económico',  code: 'ECO-01', nombre: 'Ingresos por debajo de LP',      valor: 67.3, meta: 15,  estado: 'critico', invertido: true },
  { cat: 'Económico',  code: 'ECO-02', nombre: 'Proyectos productivos activos',  valor: 36.5, meta: 60,  estado: 'medio' },
];

export const INFORMES = [
  { id: 'INF-2026-001', titulo: 'Panorama Nacional Capacidades Diversas 2026', fecha: '2026-03-15', tipo: 'Nacional', estado: 'Publicado',    paginas: 48 },
  { id: 'INF-2026-002', titulo: 'Perfil Pueblo Nasa — Cauca',                  fecha: '2026-03-08', tipo: 'Pueblo',   estado: 'Publicado',    paginas: 24 },
  { id: 'INF-2026-003', titulo: 'Brecha de Certificación Nasa-Misak',          fecha: '2026-02-28', tipo: 'Temático', estado: 'En revisión',  paginas: 32 },
  { id: 'INF-2026-004', titulo: 'Conflicto Armado y Capacidades Diversas',     fecha: '2026-02-14', tipo: 'Temático', estado: 'Publicado',    paginas: 56 },
  { id: 'INF-2026-005', titulo: 'Intercensal 2005–2018 · Pueblos Amazónicos',  fecha: '2026-01-30', tipo: 'Regional', estado: 'Publicado',    paginas: 40 },
  { id: 'INF-2026-006', titulo: 'Territorios Wayuu — La Guajira',              fecha: '2026-01-12', tipo: 'Regional', estado: 'Publicado',    paginas: 28 },
];

export const FORMULARIO_SECCIONES = [
  { id: 'A', titulo: 'Identificación de la persona',      preguntas: 8,  completas: 8 },
  { id: 'B', titulo: 'Pertenencia étnica y territorial',  preguntas: 6,  completas: 6 },
  { id: 'C', titulo: 'Dificultades funcionales (WG-SS)',  preguntas: 9,  completas: 7 },
  { id: 'D', titulo: 'Salud y atención',                  preguntas: 12, completas: 3 },
  { id: 'E', titulo: 'Educación',                         preguntas: 7,  completas: 0 },
  { id: 'F', titulo: 'Vivienda y hogar',                  preguntas: 10, completas: 0 },
  { id: 'G', titulo: 'Participación comunitaria',         preguntas: 6,  completas: 0 },
  { id: 'H', titulo: 'Víctima del conflicto',             preguntas: 5,  completas: 0 },
];

export const VOZ_ACTIVIDAD = [
  { fecha: '2026-04-18', pueblo: 'Nasa',     territorio: 'Toribío',      accion: 'Caracterización de 12 personas',     monitor: 'Mayora Luz Aidé' },
  { fecha: '2026-04-16', pueblo: 'Wayuu',    territorio: 'Alta Guajira', accion: 'Censo de hogares completado (85)',    monitor: 'Anuu Iipana' },
  { fecha: '2026-04-15', pueblo: 'Misak',    territorio: 'Silvia',       accion: 'Taller Washington Group (28 asist.)', monitor: 'Mama María Campo' },
  { fecha: '2026-04-12', pueblo: 'Arhuaco',  territorio: 'Pueblo Bello', accion: 'Ruta de certificación iniciada (6)',  monitor: 'Ricardo Torres' },
  { fecha: '2026-04-10', pueblo: 'Kamëntsá', territorio: 'Sibundoy',     accion: 'Cartografía social actualizada',     monitor: 'Taita Juan Chindoy' },
];
