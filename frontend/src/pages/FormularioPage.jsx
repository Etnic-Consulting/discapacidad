/* ============================================
   SMT-ONIC — Formulario funcional (10 bloques A-J)
   Requiere autenticacion. Guarda en smt.respuestas_formulario.
   ============================================ */
import { useMemo, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import SearchableSelect from '../components/SearchableSelect';
import {
  fetchFormMacros,
  fetchFormDptos,
  fetchFormMpios,
  fetchFormResguardos,
  fetchFormComunidades,
} from '../lib/api';

const ONIC_COLORS = {
  A: '#02432D', B: '#02AB44', C: '#1B6B3A', D: '#C4920A', E: '#2196F3',
  F: '#E8862A', G: '#8B5CF6', H: '#E8262A', I: '#0D47A1', J: '#6B6B6B',
};

const WG_QUESTIONS = [
  'Tiene dificultad para ver, incluso si usa gafas o lentes de contacto?',
  'Tiene dificultad para oir, incluso si usa un aparato auditivo?',
  'Tiene dificultad para caminar o subir escaleras?',
  'Tiene dificultad para agarrar objetos o abrir recipientes con las manos?',
  'Tiene dificultad para banarse, vestirse o comer por si mismo/a?',
  'Tiene dificultad para comunicarse, entender o ser entendido/a por otros?',
  'Tiene dificultad para aprender, recordar o concentrarse?',
  'Tiene dificultad para relacionarse con los demas?',
  'Tiene dificultad para realizar las actividades diarias?',
];
const WG_SCALE = [
  { v: '1', l: '1 - Ninguna' },
  { v: '2', l: '2 - Alguna' },
  { v: '3', l: '3 - Mucha' },
  { v: '4', l: '4 - No puede' },
];
const BARRERAS = [
  'Distancia al centro de salud mas cercano (>4 horas)',
  'Falta de transporte adecuado',
  'No hay profesionales de salud con enfoque diferencial',
  'Barrera de lengua / idioma',
  'No hay servicios de rehabilitacion en el territorio',
  'Desconfianza en el sistema de salud occidental',
  'Falta de ayudas tecnicas o dispositivos',
  'Conflicto armado / inseguridad impide el desplazamiento',
  'No hay rampas, caminos accesibles u otras adaptaciones',
  'Desconocimiento de derechos y rutas de atencion',
];

const cardStyle = {
  background: '#fff',
  borderRadius: '10px',
  boxShadow: '0 2px 10px rgba(14,31,26,0.06)',
  marginBottom: '20px',
  overflow: 'hidden',
  border: '1px solid var(--line, #E4DFD6)',
};
const blockHeader = (color) => ({
  background: color, color: '#fff',
  padding: '12px 18px', fontSize: '0.98rem', fontWeight: 700,
  fontFamily: 'var(--serif, Georgia)',
  display: 'flex', alignItems: 'center', gap: '10px',
});
const blockBadge = {
  width: 26, height: 26, borderRadius: 6,
  background: 'rgba(255,255,255,0.25)',
  display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
  fontSize: '0.78rem', fontWeight: 800,
};
const blockBody = { padding: '18px 22px' };
const fieldRow = { display: 'flex', flexDirection: 'column', gap: 4, marginBottom: 14 };
const fieldLabel = { fontSize: '0.82rem', fontWeight: 600, color: 'var(--ink-soft, #2D3A36)' };
const fieldInput = {
  padding: '8px 12px',
  border: '1px solid var(--line, #E4DFD6)',
  borderRadius: 6, fontSize: '0.88rem',
  background: '#fff', color: 'var(--ink, #0E1F1A)',
  fontFamily: 'var(--sans, sans-serif)', outline: 'none',
};
const radioRow = { display: 'flex', gap: 16, alignItems: 'center', flexWrap: 'wrap' };
const radioLabel = { display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.82rem', color: 'var(--ink, #0E1F1A)', cursor: 'pointer' };
const grid2 = { display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '10px 18px' };

function Text({ label, name, value, onChange, type = 'text', placeholder }) {
  return (
    <div style={fieldRow}>
      <label style={fieldLabel}>{label}</label>
      <input type={type} name={name} value={value || ''} placeholder={placeholder}
        onChange={(e) => onChange(name, e.target.value)} style={fieldInput} />
    </div>
  );
}
function Textarea({ label, name, value, onChange, placeholder }) {
  return (
    <div style={fieldRow}>
      <label style={fieldLabel}>{label}</label>
      <textarea name={name} value={value || ''} placeholder={placeholder}
        onChange={(e) => onChange(name, e.target.value)}
        style={{ ...fieldInput, minHeight: 60, resize: 'vertical' }} />
    </div>
  );
}
function Radios({ label, name, options, value, onChange }) {
  return (
    <div style={fieldRow}>
      <label style={fieldLabel}>{label}</label>
      <div style={radioRow}>
        {options.map((o) => {
          const ov = typeof o === 'string' ? o : o.v;
          const ol = typeof o === 'string' ? o : o.l;
          return (
            <label key={ov} style={radioLabel}>
              <input type="radio" name={name} checked={value === ov}
                onChange={() => onChange(name, ov)} />
              <span>{ol}</span>
            </label>
          );
        })}
      </div>
    </div>
  );
}
function TerritorioCascada({ data, setData }) {
  const patch = (fields) => setData((d) => ({ ...d, ...fields }));

  const fMacros = useCallback(() => fetchFormMacros(), []);
  const fDptos = useCallback((q) => fetchFormDptos({ cod_macro: data.macrorregion, q }), [data.macrorregion]);
  const fMpios = useCallback((q) => fetchFormMpios({ cod_dpto: data.cod_dpto, q }), [data.cod_dpto]);
  const fResg = useCallback((q) => fetchFormResguardos({ cod_mpio: data.cod_mpio, cod_dpto: data.cod_dpto, q }),
    [data.cod_mpio, data.cod_dpto]);
  const fComun = useCallback((q) => fetchFormComunidades({
    cod_resguardo: data.cod_resguardo, cod_mpio: data.cod_mpio, cod_dpto: data.cod_dpto, q,
  }), [data.cod_resguardo, data.cod_mpio, data.cod_dpto]);

  const rowStyle = { display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px 18px' };
  const soloRow = { display: 'grid', gridTemplateColumns: '1fr', gap: '12px' };

  return (
    <>
      <p style={{ fontSize: '0.82rem', color: 'var(--ink-muted, #5B6B66)', margin: '0 0 10px' }}>
        Busca por nombre o codigo. Al elegir una comunidad se autocompletan los niveles superiores.
      </p>

      <div style={soloRow}>
        <div style={fieldRow}>
          <label style={fieldLabel}>Macrorregion ONIC</label>
          <SearchableSelect
            value={data.macrorregion || null}
            displayValue={data.macrorregion || ''}
            placeholder="5 macrorregiones ONIC"
            fetcher={fMacros}
            prefetch
            onSelect={(opt) => {
              if (!opt) {
                patch({ macrorregion: '', cod_dpto: '', nom_dpto: '', cod_mpio: '', nom_mpio: '', cod_resguardo: '', resguardo: '', nombre_comunidad: '' });
                return;
              }
              patch({ macrorregion: opt.value, cod_dpto: '', nom_dpto: '', cod_mpio: '', nom_mpio: '', cod_resguardo: '', resguardo: '', nombre_comunidad: '' });
            }}
          />
        </div>
      </div>

      <div style={{ ...rowStyle, marginTop: 10 }}>
        <div style={fieldRow}>
          <label style={fieldLabel}>Departamento</label>
          <SearchableSelect
            value={data.cod_dpto || null}
            displayValue={data.nom_dpto ? `${data.nom_dpto} (${data.cod_dpto})` : ''}
            placeholder="Escribe nombre del departamento"
            fetcher={fDptos}
            fetcherKey={`dpto:${data.macrorregion || ''}`}
            prefetch
            onSelect={(opt) => {
              if (!opt) { patch({ cod_dpto: '', nom_dpto: '', cod_mpio: '', nom_mpio: '', cod_resguardo: '', resguardo: '', nombre_comunidad: '' }); return; }
              patch({
                cod_dpto: opt.value, nom_dpto: opt.nombre || opt.label,
                cod_mpio: '', nom_mpio: '',
                cod_resguardo: '', resguardo: '',
                nombre_comunidad: '',
              });
            }}
          />
        </div>

        <div style={fieldRow}>
          <label style={fieldLabel}>Municipio</label>
          <SearchableSelect
            value={data.cod_mpio || null}
            displayValue={data.nom_mpio ? `${data.nom_mpio} (${data.cod_mpio})` : ''}
            placeholder={data.cod_dpto ? 'Escribe nombre del municipio' : 'Selecciona primero un departamento'}
            disabled={!data.cod_dpto}
            fetcher={fMpios}
            fetcherKey={`mpio:${data.cod_dpto || ''}`}
            prefetch
            onSelect={(opt) => {
              if (!opt) { patch({ cod_mpio: '', nom_mpio: '', cod_resguardo: '', resguardo: '', nombre_comunidad: '' }); return; }
              patch({
                cod_mpio: opt.value, nom_mpio: opt.nombre || opt.label,
                cod_resguardo: '', resguardo: '',
                nombre_comunidad: '',
              });
            }}
          />
        </div>
      </div>

      <div style={{ ...rowStyle, marginTop: 10 }}>
        <div style={fieldRow}>
          <label style={fieldLabel}>Resguardo / territorio</label>
          <SearchableSelect
            value={data.cod_resguardo || null}
            displayValue={data.resguardo || ''}
            placeholder={data.cod_dpto ? 'Escribe nombre o pueblo' : 'Filtra primero por dpto o mpio'}
            disabled={!data.cod_dpto}
            fetcher={fResg}
            fetcherKey={`resg:${data.cod_mpio || data.cod_dpto || ''}`}
            prefetch
            onSelect={(opt) => {
              if (!opt) { patch({ cod_resguardo: '', resguardo: '', nombre_comunidad: '' }); return; }
              const extra = {};
              if (opt.cod_mpio && !data.cod_mpio) extra.cod_mpio = opt.cod_mpio;
              patch({
                cod_resguardo: opt.value,
                resguardo: opt.nombre || opt.label,
                nombre_comunidad: '',
                ...extra,
              });
            }}
          />
        </div>

        <div style={fieldRow}>
          <label style={fieldLabel}>Comunidad indigena</label>
          <SearchableSelect
            value={data.nombre_comunidad || null}
            displayValue={data.nombre_comunidad || ''}
            placeholder={data.cod_resguardo || data.cod_mpio || data.cod_dpto ? 'Escribe nombre de la comunidad' : 'Filtra primero por territorio'}
            disabled={!(data.cod_resguardo || data.cod_mpio || data.cod_dpto)}
            fetcher={fComun}
            fetcherKey={`com:${data.cod_resguardo || data.cod_mpio || data.cod_dpto || ''}`}
            prefetch
            minChars={0}
            onSelect={(opt) => {
              if (!opt) { patch({ nombre_comunidad: '' }); return; }
              const extra = {};
              if (opt.cod_dpto && !data.cod_dpto) extra.cod_dpto = opt.cod_dpto;
              if (opt.cod_mpio && !data.cod_mpio) extra.cod_mpio = opt.cod_mpio;
              if (opt.cod_resguardo && !data.cod_resguardo) {
                extra.cod_resguardo = opt.cod_resguardo;
                extra.resguardo = opt.resguardo || '';
              }
              if (opt.macro && !data.macrorregion) extra.macrorregion = opt.macro;
              patch({ nombre_comunidad: opt.value, ...extra });
            }}
          />
        </div>
      </div>
    </>
  );
}

function Checkboxes({ label, name, options, value, onChange }) {
  const arr = Array.isArray(value) ? value : [];
  const toggle = (o) => {
    const next = arr.includes(o) ? arr.filter((x) => x !== o) : [...arr, o];
    onChange(name, next);
  };
  return (
    <div style={fieldRow}>
      <label style={fieldLabel}>{label}</label>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '4px 18px' }}>
        {options.map((o) => (
          <label key={o} style={radioLabel}>
            <input type="checkbox" checked={arr.includes(o)} onChange={() => toggle(o)} />
            <span>{o}</span>
          </label>
        ))}
      </div>
    </div>
  );
}

const INITIAL = {
  // A territorio (cods + nombres legibles para autocompletar y revisar antes de enviar)
  cod_dpto: '', nom_dpto: '',
  cod_mpio: '', nom_mpio: '',
  cod_resguardo: '', resguardo: '',
  nombre_comunidad: '',
  zona: '', macrorregion: '',
  // B demografia
  nombre_completo: '', documento_persona: '', sexo: '',
  fecha_nacimiento: '', edad: '', cod_pueblo: '', clan: '', lengua_materna: '',
  // C washington group
  wg1: '', wg2: '', wg3: '', wg4: '', wg5: '', wg6: '', wg7: '', wg8: '', wg9: '',
  // D origen
  origen: '', hecho_victimizante: '', edad_adquisicion: '', descripcion_causa: '',
  // E salud
  afiliacion: '', eps: '', atencion_medica: '', rehabilitacion: '',
  ayuda_tecnica: '', tipo_ayuda: '',
  // F certificacion
  cert_cd: '', entidad_cert: '', rlcpd: '', prog_social: '', programas: '', victima_ruv: '',
  // G cosmovision (propias)
  cosmov_entendimiento: '', desarmonia: '', atencion_ancestral: '',
  tipo_atencion_ancestral: '', medicina_occidental: '', rel_territorio: '',
  // H barreras
  barreras: [], otra_barrera: '',
  // I participacion
  participacion: '', autonomia: '', educacion: '', nivel_educativo: '', actividad_productiva: '', tipo_actividad: '',
  // J lengua
  lenguas: '', espanol: '', comunicacion: '', interprete: '',
  // CPLI
  cpli_consentimiento: '', cpli_firma: '',
};

function computeProgress(data) {
  const keys = Object.keys(INITIAL);
  const filled = keys.filter((k) => {
    const v = data[k];
    if (Array.isArray(v)) return v.length > 0;
    return v !== '' && v != null;
  }).length;
  return Math.round((filled / keys.length) * 100);
}

export default function FormularioPage() {
  const { user, logout, token } = useAuth();
  const navigate = useNavigate();
  const [data, setData] = useState(INITIAL);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const set = (name, value) => setData((d) => ({ ...d, [name]: value }));
  const progress = useMemo(() => computeProgress(data), [data]);

  const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8095';

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setResult(null);
    if (data.cpli_consentimiento !== 'si') {
      setError('El Consentimiento Previo Libre e Informado (CPLI) es obligatorio para registrar la informacion.');
      return;
    }
    const { cod_pueblo, cod_dpto, cod_mpio, nombre_comunidad, documento_persona, cpli_consentimiento, ...datos } = data;
    const payload = {
      cod_pueblo: cod_pueblo || null,
      cod_dpto: cod_dpto || null,
      cod_mpio: cod_mpio || null,
      nombre_comunidad: nombre_comunidad || null,
      documento_persona: documento_persona || null,
      cpli_consentimiento: 'si',
      datos,
    };
    setSubmitting(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/formulario/respuesta`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      });
      if (res.status === 401) {
        await logout();
        navigate('/login');
        return;
      }
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Error al guardar' }));
        throw new Error(err.detail || 'Error al guardar');
      }
      const json = await res.json();
      setResult({ id: json.id, fecha: json.fecha_envio });
      setData(INITIAL);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (err) {
      setError(err.message || 'No fue posible enviar el formulario');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="page-inner">
      {/* Header */}
      <div style={{
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        marginBottom: 20, padding: '18px 22px',
        background: '#fff', borderRadius: 10,
        boxShadow: '0 2px 10px rgba(14,31,26,0.06)',
        border: '1px solid var(--line, #E4DFD6)',
      }}>
        <div>
          <div style={{ fontFamily: 'var(--mono, monospace)', fontSize: '0.7rem', color: 'var(--primary, #02432D)', letterSpacing: '0.12em', marginBottom: 6 }}>
            SMT — ONIC / FORMULARIO DE RECOLECCION
          </div>
          <h1 style={{ fontFamily: 'var(--serif, Georgia)', fontSize: '1.6rem', margin: 0 }}>
            Registro de caracterizacion
          </h1>
          <p style={{ margin: '6px 0 0', color: 'var(--ink-muted, #5B6B66)', fontSize: '0.88rem' }}>
            10 bloques tematicos — requiere CPLI — se guarda en la base de datos SMT.
          </p>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: '0.85rem', color: 'var(--ink-soft, #2D3A36)' }}>
            <strong>{user?.nombre || user?.username}</strong> <span style={{ color: 'var(--ink-muted, #5B6B66)' }}>({user?.rol})</span>
          </div>
          <button onClick={async () => { await logout(); navigate('/login'); }}
            style={{ marginTop: 6, padding: '6px 14px', background: 'transparent',
              color: 'var(--primary, #02432D)', border: '1px solid var(--primary, #02432D)',
              borderRadius: 6, fontSize: '0.8rem', cursor: 'pointer' }}>
            Cerrar sesion
          </button>
        </div>
      </div>

      {/* KPIs */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 14, marginBottom: 20 }}>
        <div style={{ background: '#fff', borderRadius: 10, padding: '14px 18px', borderLeft: '4px solid var(--primary, #02432D)', boxShadow: '0 2px 10px rgba(14,31,26,0.06)' }}>
          <div style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--primary, #02432D)' }}>{progress}%</div>
          <div style={{ fontSize: '0.78rem', color: 'var(--ink-muted, #5B6B66)' }}>Progreso del formulario</div>
        </div>
        <div style={{ background: '#fff', borderRadius: 10, padding: '14px 18px', borderLeft: '4px solid #E8862A', boxShadow: '0 2px 10px rgba(14,31,26,0.06)' }}>
          <div style={{ fontSize: '1.4rem', fontWeight: 700 }}>10</div>
          <div style={{ fontSize: '0.78rem', color: 'var(--ink-muted, #5B6B66)' }}>Bloques A-J</div>
        </div>
        <div style={{ background: '#fff', borderRadius: 10, padding: '14px 18px', borderLeft: '4px solid #8B5CF6', boxShadow: '0 2px 10px rgba(14,31,26,0.06)' }}>
          <div style={{ fontSize: '1.4rem', fontWeight: 700, color: data.cpli_consentimiento === 'si' ? '#02AB44' : '#E8262A' }}>
            {data.cpli_consentimiento === 'si' ? 'OK' : '—'}
          </div>
          <div style={{ fontSize: '0.78rem', color: 'var(--ink-muted, #5B6B66)' }}>CPLI</div>
        </div>
        <div style={{ background: '#fff', borderRadius: 10, padding: '14px 18px', borderLeft: '4px solid #2196F3', boxShadow: '0 2px 10px rgba(14,31,26,0.06)' }}>
          <div style={{ fontSize: '1.4rem', fontWeight: 700, color: result ? '#02AB44' : 'var(--ink-muted, #5B6B66)' }}>
            {result ? `#${result.id}` : '—'}
          </div>
          <div style={{ fontSize: '0.78rem', color: 'var(--ink-muted, #5B6B66)' }}>Ultimo registro</div>
        </div>
      </div>

      {result && (
        <div role="status" style={{
          background: '#e6f7ec', border: '1px solid #02AB44', color: '#0b5d2a',
          padding: '12px 16px', borderRadius: 8, marginBottom: 18, fontSize: '0.9rem',
        }}>
          Registro <strong>#{result.id}</strong> guardado correctamente en la base de datos.
        </div>
      )}
      {error && (
        <div role="alert" style={{
          background: 'var(--alert-soft, #F9E1DB)', border: '1px solid var(--alert, #B33A2F)',
          color: 'var(--alert, #B33A2F)', padding: '12px 16px', borderRadius: 8, marginBottom: 18, fontSize: '0.9rem',
        }}>
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} aria-busy={submitting}>
        {/* BLOQUE A */}
        <div style={cardStyle}>
          <div style={blockHeader(ONIC_COLORS.A)}>
            <span style={blockBadge}>A</span>Bloque A — Identificacion Territorial
          </div>
          <div style={blockBody}>
            <TerritorioCascada data={data} setData={setData} />
            <div style={{ ...grid2, marginTop: 14 }}>
              <Radios
                label="Zona"
                name="zona"
                value={data.zona}
                onChange={set}
                options={['Rural', 'Urbana', 'Dispersa']}
              />
            </div>
          </div>
        </div>

        {/* BLOQUE B */}
        <div style={cardStyle}>
          <div style={blockHeader(ONIC_COLORS.B)}>
            <span style={blockBadge}>B</span>Bloque B — Datos Demograficos
          </div>
          <div style={blockBody}>
            <div style={grid2}>
              <Text label="Nombre completo" name="nombre_completo" value={data.nombre_completo} onChange={set} />
              <Text label="Documento de identidad" name="documento_persona" value={data.documento_persona} onChange={set} />
              <Radios label="Sexo" name="sexo" value={data.sexo} onChange={set}
                options={[{ v: 'H', l: 'Hombre' }, { v: 'M', l: 'Mujer' }, { v: 'I', l: 'Intersexual' }, { v: 'O', l: 'Otro' }]} />
              <Text label="Fecha de nacimiento" name="fecha_nacimiento" value={data.fecha_nacimiento} onChange={set} type="date" />
              <Text label="Edad (anos)" name="edad" value={data.edad} onChange={set} type="number" />
              <Text label="Codigo pueblo indigena" name="cod_pueblo" value={data.cod_pueblo} onChange={set} placeholder="Ej. 001" />
              <Text label="Clan / Familia" name="clan" value={data.clan} onChange={set} />
              <Text label="Lengua materna" name="lengua_materna" value={data.lengua_materna} onChange={set} />
            </div>
          </div>
        </div>

        {/* BLOQUE C */}
        <div style={{ padding: '12px 16px', background: '#EFF6FF', border: '1px solid #93C5FD', borderRadius: 6, color: '#1E3A8A', fontSize: '0.88rem', marginBottom: 12 }}>
          <strong>Sobre estas preguntas</strong>
          <br />
          Las siguientes preguntas siguen el Grupo de Washington (Naciones Unidas), un estandar internacional para identificar capacidades diversas. Responde segun la dificultad real para realizar cada actividad, sin minimizar ni exagerar.
        </div>
        <div style={cardStyle}>
          <div style={blockHeader(ONIC_COLORS.C)}>
            <span style={blockBadge}>C</span>Bloque C — Dificultades Funcionales (Grupo de Washington)
          </div>
          <div style={blockBody}>
            {WG_QUESTIONS.map((q, i) => (
              <Radios key={i} label={`C${i + 1}. ${q}`} name={`wg${i + 1}`}
                value={data[`wg${i + 1}`]} onChange={set} options={WG_SCALE} />
            ))}
          </div>
        </div>

        {/* BLOQUE D */}
        <div style={cardStyle}>
          <div style={blockHeader(ONIC_COLORS.D)}>
            <span style={blockBadge}>D</span>Bloque D — Causa y Origen
          </div>
          <div style={blockBody}>
            <Radios label="Origen de la condicion" name="origen" value={data.origen} onChange={set}
              options={['De nacimiento', 'Enfermedad adquirida', 'Accidente', 'Conflicto armado', 'Violencia interpersonal', 'Envejecimiento', 'Otra']} />
            <Text label="Hecho victimizante (si aplica)" name="hecho_victimizante" value={data.hecho_victimizante} onChange={set} />
            <Text label="Edad de adquisicion" name="edad_adquisicion" value={data.edad_adquisicion} onChange={set} type="number" />
            <Textarea label="Descripcion adicional" name="descripcion_causa" value={data.descripcion_causa} onChange={set} />
          </div>
        </div>

        {/* BLOQUE E */}
        <div style={cardStyle}>
          <div style={blockHeader(ONIC_COLORS.E)}>
            <span style={blockBadge}>E</span>Bloque E — Acceso a Salud
          </div>
          <div style={blockBody}>
            <Radios label="Afiliacion al sistema de salud" name="afiliacion" value={data.afiliacion} onChange={set}
              options={['Subsidiado', 'Contributivo', 'Especial', 'No afiliado']} />
            <Text label="EPS / Entidad de salud" name="eps" value={data.eps} onChange={set} />
            <Radios label="Recibe atencion medica actualmente?" name="atencion_medica" value={data.atencion_medica} onChange={set} options={['Si', 'No']} />
            <Radios label="Recibe servicios de rehabilitacion?" name="rehabilitacion" value={data.rehabilitacion} onChange={set} options={['Si', 'No']} />
            <Radios label="Tiene ayudas tecnicas?" name="ayuda_tecnica" value={data.ayuda_tecnica} onChange={set}
              options={['Si', 'No, las necesita', 'No las necesita']} />
            <Text label="Tipo de ayuda tecnica" name="tipo_ayuda" value={data.tipo_ayuda} onChange={set} />
          </div>
        </div>

        {/* BLOQUE F */}
        <div style={cardStyle}>
          <div style={blockHeader(ONIC_COLORS.F)}>
            <span style={blockBadge}>F</span>Bloque F — Certificacion y Derechos
          </div>
          <div style={blockBody}>
            <Radios label="Tiene certificacion de capacidades diversas?" name="cert_cd" value={data.cert_cd} onChange={set}
              options={['Si', 'No', 'En tramite']} />
            <Text label="Entidad certificadora" name="entidad_cert" value={data.entidad_cert} onChange={set} />
            <Radios label="Esta inscrito/a en el RLCPD?" name="rlcpd" value={data.rlcpd} onChange={set}
              options={['Si', 'No', 'No sabe']} />
            <Radios label="Beneficiario/a de programa social?" name="prog_social" value={data.prog_social} onChange={set} options={['Si', 'No']} />
            <Text label="Programas (si aplica)" name="programas" value={data.programas} onChange={set} />
            <Radios label="Victima del conflicto armado (RUV)?" name="victima_ruv" value={data.victima_ruv} onChange={set}
              options={['Si', 'No', 'En proceso']} />
          </div>
        </div>

        {/* BLOQUE G (propias) */}
        <div style={{ ...cardStyle, border: '2px solid #8B5CF6' }}>
          <div style={blockHeader(ONIC_COLORS.G)}>
            <span style={blockBadge}>G</span>Bloque G — Cosmovision y Salud Propia
          </div>
          <div style={blockBody}>
            <Textarea label="Desde la cosmovision de su pueblo, como se entiende su condicion?" name="cosmov_entendimiento" value={data.cosmov_entendimiento} onChange={set} />
            <Radios label="Presenta o ha presentado desarmonia espiritual?" name="desarmonia" value={data.desarmonia} onChange={set}
              options={['Si', 'No', 'No sabe']} />
            <Radios label="Ha recibido atencion de medicina ancestral o tradicional?" name="atencion_ancestral" value={data.atencion_ancestral} onChange={set}
              options={['Si regularmente', 'Si ocasionalmente', 'No pero quisiera', 'No']} />
            <Text label="Tipo de atencion ancestral recibida" name="tipo_atencion_ancestral" value={data.tipo_atencion_ancestral} onChange={set} />
            <Radios label="La medicina occidental es suficiente para su bienestar?" name="medicina_occidental" value={data.medicina_occidental} onChange={set}
              options={['Si', 'No', 'Parcialmente']} />
            <Textarea label="Relacion entre la condicion y la perdida del territorio o practicas rituales" name="rel_territorio" value={data.rel_territorio} onChange={set} />
          </div>
        </div>

        {/* BLOQUE H */}
        <div style={cardStyle}>
          <div style={blockHeader(ONIC_COLORS.H)}>
            <span style={blockBadge}>H</span>Bloque H — Barreras Territoriales
          </div>
          <div style={blockBody}>
            <Checkboxes label="Barreras que enfrenta la persona (seleccion multiple)" name="barreras" value={data.barreras} onChange={set} options={BARRERAS} />
            <Text label="Otra barrera no listada" name="otra_barrera" value={data.otra_barrera} onChange={set} />
          </div>
        </div>

        {/* BLOQUE I */}
        <div style={cardStyle}>
          <div style={blockHeader(ONIC_COLORS.I)}>
            <span style={blockBadge}>I</span>Bloque I — Participacion y Autonomia
          </div>
          <div style={blockBody}>
            <Radios label="Participa en espacios comunitarios?" name="participacion" value={data.participacion} onChange={set}
              options={['Si activamente', 'Si ocasionalmente', 'No por barreras', 'No por decision propia']} />
            <Radios label="Puede tomar decisiones autonomamente?" name="autonomia" value={data.autonomia} onChange={set}
              options={['Si plenamente', 'Parcialmente', 'No depende de otros']} />
            <Radios label="Tiene acceso a educacion?" name="educacion" value={data.educacion} onChange={set} options={['Si', 'No']} />
            <Text label="Nivel educativo alcanzado" name="nivel_educativo" value={data.nivel_educativo} onChange={set} />
            <Radios label="Realiza actividad productiva o laboral?" name="actividad_productiva" value={data.actividad_productiva} onChange={set} options={['Si', 'No']} />
            <Text label="Tipo de actividad" name="tipo_actividad" value={data.tipo_actividad} onChange={set} />
          </div>
        </div>

        {/* BLOQUE J */}
        <div style={cardStyle}>
          <div style={blockHeader(ONIC_COLORS.J)}>
            <span style={blockBadge}>J</span>Bloque J — Lengua y Comunicacion
          </div>
          <div style={blockBody}>
            <Text label="Lengua(s) que habla" name="lenguas" value={data.lenguas} onChange={set} />
            <Radios label="Habla espanol?" name="espanol" value={data.espanol} onChange={set}
              options={['Si fluido', 'Si basico', 'No']} />
            <Radios label="Forma de comunicacion preferida" name="comunicacion" value={data.comunicacion} onChange={set}
              options={['Oral lengua propia', 'Oral espanol', 'Senas colombiana', 'Alternativa', 'Otra']} />
            <Radios label="Necesita interprete?" name="interprete" value={data.interprete} onChange={set} options={['Si', 'No']} />
          </div>
        </div>

        {/* CPLI */}
        <div style={{ ...cardStyle, border: '2px solid var(--gold, #C4920A)' }}>
          <div style={blockHeader('var(--gold, #C4920A)')}>
            <span style={blockBadge}>★</span>Consentimiento Previo Libre e Informado (CPLI)
          </div>
          <div style={blockBody}>
            <p style={{ fontSize: '0.88rem', color: 'var(--ink-soft, #2D3A36)', marginBottom: 12, lineHeight: 1.6 }}>
              La persona encuestada manifiesta haber sido informada sobre los fines de este registro,
              el tratamiento de sus datos bajo la Ley 1581/2012 y la politica de datos de la ONIC, y
              otorga su consentimiento libre para ser incluida en el SMT-ONIC.
            </p>
            <Radios label="Consentimiento otorgado?" name="cpli_consentimiento" value={data.cpli_consentimiento} onChange={set}
              options={[{ v: 'si', l: 'Si, autorizo' }, { v: 'no', l: 'No autorizo' }]} />
            <Text label="Firma / testigo (nombre)" name="cpli_firma" value={data.cpli_firma} onChange={set} />
          </div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12, marginTop: 20, marginBottom: 40 }}>
          <button type="button" onClick={() => setData(INITIAL)}
            style={{ padding: '10px 20px', background: 'transparent',
              color: 'var(--ink-soft, #2D3A36)', border: '1px solid var(--line, #E4DFD6)',
              borderRadius: 8, fontSize: '0.9rem', cursor: 'pointer' }}>
            Limpiar
          </button>
          <button type="submit" disabled={submitting}
            aria-busy={submitting}
            aria-label={submitting ? 'Guardando formulario, por favor espere' : 'Enviar formulario'}
            style={{ padding: '10px 28px',
              background: submitting ? 'var(--ink-faint)' : 'var(--primary, #02432D)',
              color: '#fff', border: 'none', borderRadius: 8,
              fontSize: '0.95rem', fontWeight: 600,
              cursor: submitting ? 'wait' : 'pointer',
              display: 'inline-flex', alignItems: 'center', gap: 8 }}>
            {submitting && (
              <span aria-hidden="true" style={{
                display: 'inline-block', width: 12, height: 12,
                border: '2px solid rgba(255,255,255,0.4)',
                borderTopColor: '#fff', borderRadius: '50%',
                animation: 'spin 0.8s linear infinite',
              }} />
            )}
            {submitting ? 'Guardando…' : 'Enviar formulario'}
          </button>
        </div>
      </form>
    </div>
  );
}
