/* ============================================
   SMT-ONIC v2.0 — Formulario (Preview / Design)
   Shows the 10-block ONIC instrument structure.
   This is a PREVIEW page only - not functional.
   ============================================ */

const ONIC_COLORS = {
  A: '#02432D',
  B: '#02AB44',
  C: '#1B6B3A',
  D: '#C4920A',
  E: '#2196F3',
  F: '#E8862A',
  G: '#8B5CF6',
  H: '#E8262A',
  I: '#0D47A1',
  J: '#6B6B6B',
};

const cardStyle = {
  background: '#fff',
  borderRadius: 'var(--radius-md)',
  boxShadow: 'var(--shadow-md)',
  marginBottom: '24px',
  overflow: 'hidden',
};

const blockHeader = (color) => ({
  background: color,
  color: '#fff',
  padding: '14px 20px',
  fontSize: '1rem',
  fontWeight: 700,
  fontFamily: 'var(--font-heading)',
  display: 'flex',
  alignItems: 'center',
  gap: '12px',
});

const blockBody = {
  padding: '20px 24px',
  opacity: 0.7,
};

const fieldRow = {
  display: 'flex',
  flexDirection: 'column',
  gap: '4px',
  marginBottom: '16px',
};

const fieldLabel = {
  fontSize: '0.85rem',
  fontWeight: 600,
  color: 'var(--color-charcoal)',
};

const fieldInput = {
  padding: '8px 12px',
  border: '1px solid var(--color-gray-300)',
  borderRadius: 'var(--radius-sm)',
  fontSize: '0.85rem',
  fontFamily: 'var(--font-body)',
  background: 'var(--color-gray-100)',
  color: 'var(--color-gray-400)',
  cursor: 'not-allowed',
};

const fieldSelect = {
  ...fieldInput,
  appearance: 'none',
};

const radioRow = {
  display: 'flex',
  gap: '20px',
  alignItems: 'center',
  flexWrap: 'wrap',
};

const radioLabel = {
  display: 'flex',
  alignItems: 'center',
  gap: '6px',
  fontSize: '0.82rem',
  color: 'var(--color-gray-500)',
  cursor: 'not-allowed',
};

const sectionNote = {
  fontSize: '0.78rem',
  color: 'var(--color-gray-400)',
  fontStyle: 'italic',
  marginTop: '8px',
  lineHeight: 1.5,
};

const uniqueBadge = {
  display: 'inline-block',
  padding: '2px 10px',
  borderRadius: '12px',
  fontSize: '0.7rem',
  fontWeight: 700,
  background: '#f0e6ff',
  color: '#8B5CF6',
  marginLeft: '8px',
  textTransform: 'uppercase',
  letterSpacing: '0.3px',
};

const blockBadge = (color) => ({
  width: '28px',
  height: '28px',
  borderRadius: '6px',
  background: 'rgba(255,255,255,0.25)',
  display: 'inline-flex',
  alignItems: 'center',
  justifyContent: 'center',
  fontSize: '0.8rem',
  fontWeight: 800,
  flexShrink: 0,
});

function DisabledField({ label, placeholder, type = 'text' }) {
  return (
    <div style={fieldRow}>
      <label style={fieldLabel}>{label}</label>
      {type === 'select' ? (
        <select disabled style={fieldSelect}>
          <option>{placeholder || 'Seleccionar...'}</option>
        </select>
      ) : type === 'textarea' ? (
        <textarea
          disabled
          placeholder={placeholder}
          style={{ ...fieldInput, minHeight: '60px', resize: 'none' }}
        />
      ) : (
        <input
          type={type}
          disabled
          placeholder={placeholder}
          style={fieldInput}
        />
      )}
    </div>
  );
}

function RadioScale({ question, scale }) {
  return (
    <div style={{ marginBottom: '16px' }}>
      <div style={{ ...fieldLabel, marginBottom: '8px' }}>{question}</div>
      <div style={radioRow}>
        {scale.map((option, i) => (
          <label key={i} style={radioLabel}>
            <input type="radio" disabled name={question} />
            <span>{option}</span>
          </label>
        ))}
      </div>
    </div>
  );
}

function CheckboxOption({ label }) {
  return (
    <label style={{ ...radioLabel, marginBottom: '6px' }}>
      <input type="checkbox" disabled />
      <span>{label}</span>
    </label>
  );
}

/* ---- Washington Group Questions (Bloque C) ---- */
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
  '1 - Ninguna',
  '2 - Alguna',
  '3 - Mucha',
  '4 - No puede',
];

/* ---- Bloque H Barriers ---- */
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

export default function FormularioPage() {
  return (
    <div>
      <div className="page-header">
        <h1>Formulario de Recoleccion</h1>
        <p>
          Instrumento de recoleccion SMT-ONIC para la caracterizacion de personas
          indigenas con capacidades diversas -- 10 bloques tematicos
        </p>
      </div>

      {/* Login mockup */}
      <div style={{
        background: '#f5f5f5',
        borderRadius: 'var(--radius-md)',
        boxShadow: 'var(--shadow-md)',
        padding: '28px 32px',
        marginBottom: '24px',
        maxWidth: '440px',
      }}>
        <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--color-primary)', marginBottom: '20px' }}>
          Acceso al formulario de recoleccion
        </h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', marginBottom: '18px' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <label style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--color-charcoal)' }}>Usuario</label>
            <input
              type="text"
              disabled
              placeholder="Ingrese su usuario"
              style={{
                padding: '10px 14px',
                border: '1px solid var(--color-gray-300)',
                borderRadius: 'var(--radius-sm)',
                fontSize: '0.88rem',
                fontFamily: 'var(--font-body)',
                background: '#e8e8e8',
                color: 'var(--color-gray-400)',
                cursor: 'not-allowed',
              }}
            />
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <label style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--color-charcoal)' }}>Contrasena</label>
            <input
              type="password"
              disabled
              placeholder="Ingrese su contrasena"
              style={{
                padding: '10px 14px',
                border: '1px solid var(--color-gray-300)',
                borderRadius: 'var(--radius-sm)',
                fontSize: '0.88rem',
                fontFamily: 'var(--font-body)',
                background: '#e8e8e8',
                color: 'var(--color-gray-400)',
                cursor: 'not-allowed',
              }}
            />
          </div>
        </div>
        <button
          disabled
          style={{
            width: '100%',
            padding: '10px 20px',
            background: 'var(--color-gray-300)',
            color: '#fff',
            border: 'none',
            borderRadius: 'var(--radius-sm)',
            fontSize: '0.92rem',
            fontWeight: 600,
            fontFamily: 'var(--font-body)',
            cursor: 'not-allowed',
            marginBottom: '16px',
          }}
        >
          Ingresar
        </button>
        <p style={{
          fontSize: '0.82rem',
          color: 'var(--color-gray-500)',
          lineHeight: 1.6,
        }}>
          El formulario de recoleccion estara disponible para dinamizadores
          territoriales autorizados por la ONIC. Para solicitar acceso, contacte a
          poblacion@onic.org.co o al coordinador del SMT (tel. 3112201903).
        </p>
      </div>

      {/* Preview banner */}
      <div style={{
        background: '#e8f4fd',
        borderLeft: '4px solid #2196F3',
        borderRadius: 'var(--radius-sm)',
        padding: '14px 20px',
        marginBottom: '24px',
        fontSize: '0.9rem',
        color: '#0d47a1',
        lineHeight: 1.5,
      }}>
        <strong>Formulario en modo vista previa.</strong> La recoleccion se activara
        cuando el equipo de campo este listo. Este es un diseno del instrumento que
        capturara informacion directamente en territorio.
      </div>

      {/* Statistics bar */}
      <div style={{
        display: 'flex',
        gap: '16px',
        marginBottom: '24px',
        flexWrap: 'wrap',
      }}>
        <div style={{
          background: '#fff',
          borderRadius: 'var(--radius-md)',
          boxShadow: 'var(--shadow-sm)',
          padding: '14px 20px',
          flex: '1 1 200px',
          borderLeft: '4px solid var(--color-green-mid)',
        }}>
          <div style={{ fontSize: '1.5rem', fontWeight: 700, fontFamily: 'var(--font-heading)', color: 'var(--color-primary)' }}>47</div>
          <div style={{ fontSize: '0.82rem', color: 'var(--color-gray-500)' }}>Variables totales</div>
        </div>
        <div style={{
          background: '#fff',
          borderRadius: 'var(--radius-md)',
          boxShadow: 'var(--shadow-sm)',
          padding: '14px 20px',
          flex: '1 1 200px',
          borderLeft: '4px solid var(--color-gold)',
        }}>
          <div style={{ fontSize: '1.5rem', fontWeight: 700, fontFamily: 'var(--font-heading)', color: 'var(--color-primary)' }}>30</div>
          <div style={{ fontSize: '0.82rem', color: 'var(--color-gray-500)' }}>Variables comparables con el censo</div>
        </div>
        <div style={{
          background: '#fff',
          borderRadius: 'var(--radius-md)',
          boxShadow: 'var(--shadow-sm)',
          padding: '14px 20px',
          flex: '1 1 200px',
          borderLeft: '4px solid #8B5CF6',
        }}>
          <div style={{ fontSize: '1.5rem', fontWeight: 700, fontFamily: 'var(--font-heading)', color: '#8B5CF6' }}>17</div>
          <div style={{ fontSize: '0.82rem', color: 'var(--color-gray-500)' }}>Variables propias de los pueblos</div>
        </div>
        <div style={{
          background: '#fff',
          borderRadius: 'var(--radius-md)',
          boxShadow: 'var(--shadow-sm)',
          padding: '14px 20px',
          flex: '1 1 200px',
          borderLeft: '4px solid var(--color-red)',
        }}>
          <div style={{ fontSize: '1.5rem', fontWeight: 700, fontFamily: 'var(--font-heading)', color: 'var(--color-primary)' }}>10</div>
          <div style={{ fontSize: '0.82rem', color: 'var(--color-gray-500)' }}>Bloques tematicos</div>
        </div>
      </div>

      {/* ================================================================
         BLOQUE A: Identificacion Territorial
         ================================================================ */}
      <div style={cardStyle}>
        <div style={blockHeader(ONIC_COLORS.A)}>
          <span style={blockBadge(ONIC_COLORS.A)}>A</span>
          Bloque A: Identificacion Territorial
        </div>
        <div style={blockBody}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px 20px' }}>
            <DisabledField label="Departamento" placeholder="Seleccionar departamento" type="select" />
            <DisabledField label="Municipio" placeholder="Seleccionar municipio" type="select" />
            <DisabledField label="Resguardo / Territorio" placeholder="Nombre del resguardo o territorio" />
            <DisabledField label="Zona" placeholder="Seleccionar zona" type="select" />
            <DisabledField label="Comunidad / Vereda" placeholder="Nombre de la comunidad" />
            <DisabledField label="Macrorregion ONIC" placeholder="Seleccionar macrorregion" type="select" />
          </div>
          <div style={sectionNote}>
            Los datos territoriales permiten georreferenciar la informacion y vincularla
            con los resguardos y comunidades del Sistema de Informacion Geografica de la ONIC.
          </div>
        </div>
      </div>

      {/* ================================================================
         BLOQUE B: Datos Demograficos
         ================================================================ */}
      <div style={cardStyle}>
        <div style={blockHeader(ONIC_COLORS.B)}>
          <span style={blockBadge(ONIC_COLORS.B)}>B</span>
          Bloque B: Datos Demograficos
        </div>
        <div style={blockBody}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px 20px' }}>
            <DisabledField label="Nombre completo" placeholder="Nombres y apellidos" />
            <DisabledField label="Documento de identidad" placeholder="Numero de documento" />
            <div style={fieldRow}>
              <label style={fieldLabel}>Sexo</label>
              <div style={radioRow}>
                <label style={radioLabel}><input type="radio" disabled /><span>Hombre</span></label>
                <label style={radioLabel}><input type="radio" disabled /><span>Mujer</span></label>
                <label style={radioLabel}><input type="radio" disabled /><span>Intersexual</span></label>
                <label style={radioLabel}><input type="radio" disabled /><span>Otro</span></label>
              </div>
            </div>
            <DisabledField label="Fecha de nacimiento" placeholder="DD/MM/AAAA" type="text" />
            <DisabledField label="Edad (anos)" placeholder="Edad calculada" />
            <DisabledField label="Pueblo indigena" placeholder="Seleccionar pueblo" type="select" />
            <DisabledField label="Clan / Familia" placeholder="Nombre del clan" />
            <DisabledField label="Lengua materna" placeholder="Seleccionar lengua" type="select" />
          </div>
        </div>
      </div>

      {/* ================================================================
         BLOQUE C: Dificultades Funcionales (Washington Group)
         ================================================================ */}
      <div style={cardStyle}>
        <div style={blockHeader(ONIC_COLORS.C)}>
          <span style={blockBadge(ONIC_COLORS.C)}>C</span>
          Bloque C: Dificultades Funcionales -- Grupo de Washington
        </div>
        <div style={blockBody}>
          <div style={{
            background: 'var(--color-green-light)',
            borderRadius: 'var(--radius-sm)',
            padding: '12px 16px',
            marginBottom: '20px',
            fontSize: '0.85rem',
            color: 'var(--color-primary)',
            lineHeight: 1.5,
          }}>
            Las siguientes 9 preguntas corresponden al conjunto de preguntas cortas del
            Grupo de Washington sobre estadisticas de la diversidad funcional. Esta es la
            herramienta estandar internacional que permite comparabilidad con el CNPV 2018 del DANE.
            La escala va de 1 (ninguna dificultad) a 4 (no puede hacerlo en absoluto).
          </div>

          {WG_QUESTIONS.map((q, i) => (
            <RadioScale
              key={i}
              question={`C${i + 1}. ${q}`}
              scale={WG_SCALE}
            />
          ))}

          <div style={sectionNote}>
            9 preguntas con escala 1-4. Se considera que una persona tiene capacidades
            diversas si responde "mucha dificultad" (3) o "no puede hacerlo" (4) en al
            menos una pregunta.
          </div>
        </div>
      </div>

      {/* ================================================================
         BLOQUE D: Causa y Origen
         ================================================================ */}
      <div style={cardStyle}>
        <div style={blockHeader(ONIC_COLORS.D)}>
          <span style={blockBadge(ONIC_COLORS.D)}>D</span>
          Bloque D: Causa y Origen
        </div>
        <div style={blockBody}>
          <div style={fieldRow}>
            <label style={fieldLabel}>Origen de la condicion de capacidades diversas</label>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <label style={radioLabel}><input type="radio" disabled /><span>De nacimiento / congenita</span></label>
              <label style={radioLabel}><input type="radio" disabled /><span>Enfermedad adquirida</span></label>
              <label style={radioLabel}><input type="radio" disabled /><span>Accidente</span></label>
              <label style={radioLabel}><input type="radio" disabled /><span>Conflicto armado</span></label>
              <label style={radioLabel}><input type="radio" disabled /><span>Violencia interpersonal</span></label>
              <label style={radioLabel}><input type="radio" disabled /><span>Envejecimiento</span></label>
              <label style={radioLabel}><input type="radio" disabled /><span>Otra causa</span></label>
            </div>
          </div>
          <DisabledField label="Si es por conflicto armado, especificar hecho victimizante" placeholder="Desplazamiento, minas, etc." />
          <DisabledField label="Edad de adquisicion (si aplica)" placeholder="Edad en anos" />
          <DisabledField label="Descripcion adicional" placeholder="Detalles sobre la causa u origen" type="textarea" />
        </div>
      </div>

      {/* ================================================================
         BLOQUE E: Acceso a Salud
         ================================================================ */}
      <div style={cardStyle}>
        <div style={blockHeader(ONIC_COLORS.E)}>
          <span style={blockBadge(ONIC_COLORS.E)}>E</span>
          Bloque E: Acceso a Salud
        </div>
        <div style={blockBody}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px 20px' }}>
            <div style={fieldRow}>
              <label style={fieldLabel}>Afiliacion al sistema de salud</label>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <label style={radioLabel}><input type="radio" disabled /><span>Regimen Subsidiado</span></label>
                <label style={radioLabel}><input type="radio" disabled /><span>Regimen Contributivo</span></label>
                <label style={radioLabel}><input type="radio" disabled /><span>Regimen Especial</span></label>
                <label style={radioLabel}><input type="radio" disabled /><span>No afiliado/a</span></label>
              </div>
            </div>
            <DisabledField label="EPS / Entidad de salud" placeholder="Nombre de la EPS" />
            <div style={fieldRow}>
              <label style={fieldLabel}>Recibe atencion medica actualmente?</label>
              <div style={radioRow}>
                <label style={radioLabel}><input type="radio" disabled /><span>Si</span></label>
                <label style={radioLabel}><input type="radio" disabled /><span>No</span></label>
              </div>
            </div>
            <div style={fieldRow}>
              <label style={fieldLabel}>Recibe servicios de rehabilitacion?</label>
              <div style={radioRow}>
                <label style={radioLabel}><input type="radio" disabled /><span>Si</span></label>
                <label style={radioLabel}><input type="radio" disabled /><span>No</span></label>
              </div>
            </div>
            <div style={fieldRow}>
              <label style={fieldLabel}>Tiene ayudas tecnicas? (silla de ruedas, audifonos, etc.)</label>
              <div style={radioRow}>
                <label style={radioLabel}><input type="radio" disabled /><span>Si</span></label>
                <label style={radioLabel}><input type="radio" disabled /><span>No, pero las necesita</span></label>
                <label style={radioLabel}><input type="radio" disabled /><span>No las necesita</span></label>
              </div>
            </div>
            <DisabledField label="Tipo de ayuda tecnica (si aplica)" placeholder="Especificar" />
          </div>
        </div>
      </div>

      {/* ================================================================
         BLOQUE F: Certificacion y Derechos
         ================================================================ */}
      <div style={cardStyle}>
        <div style={blockHeader(ONIC_COLORS.F)}>
          <span style={blockBadge(ONIC_COLORS.F)}>F</span>
          Bloque F: Certificacion y Derechos
        </div>
        <div style={blockBody}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px 20px' }}>
            <div style={fieldRow}>
              <label style={fieldLabel}>Tiene certificacion de capacidades diversas?</label>
              <div style={radioRow}>
                <label style={radioLabel}><input type="radio" disabled /><span>Si</span></label>
                <label style={radioLabel}><input type="radio" disabled /><span>No</span></label>
                <label style={radioLabel}><input type="radio" disabled /><span>En tramite</span></label>
              </div>
            </div>
            <DisabledField label="Entidad certificadora" placeholder="EPS, IPS, Secretaria de Salud..." />
            <div style={fieldRow}>
              <label style={fieldLabel}>Esta inscrito/a en el RLCPD?</label>
              <div style={radioRow}>
                <label style={radioLabel}><input type="radio" disabled /><span>Si</span></label>
                <label style={radioLabel}><input type="radio" disabled /><span>No</span></label>
                <label style={radioLabel}><input type="radio" disabled /><span>No sabe</span></label>
              </div>
            </div>
            <div style={fieldRow}>
              <label style={fieldLabel}>Es beneficiario/a de algun programa social?</label>
              <div style={radioRow}>
                <label style={radioLabel}><input type="radio" disabled /><span>Si</span></label>
                <label style={radioLabel}><input type="radio" disabled /><span>No</span></label>
              </div>
            </div>
            <DisabledField label="Programas (si aplica)" placeholder="Nombres de los programas" />
            <div style={fieldRow}>
              <label style={fieldLabel}>Es victima del conflicto armado (RUV)?</label>
              <div style={radioRow}>
                <label style={radioLabel}><input type="radio" disabled /><span>Si</span></label>
                <label style={radioLabel}><input type="radio" disabled /><span>No</span></label>
                <label style={radioLabel}><input type="radio" disabled /><span>En proceso</span></label>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ================================================================
         BLOQUE G: Cosmovision y Salud Propia
         ================================================================ */}
      <div style={{
        ...cardStyle,
        border: '2px solid #8B5CF6',
      }}>
        <div style={blockHeader(ONIC_COLORS.G)}>
          <span style={blockBadge(ONIC_COLORS.G)}>G</span>
          Bloque G: Cosmovision y Salud Propia
          <span style={uniqueBadge}>Variables propias</span>
        </div>
        <div style={blockBody}>
          <div style={{
            background: '#f0e6ff',
            borderRadius: 'var(--radius-sm)',
            padding: '12px 16px',
            marginBottom: '20px',
            fontSize: '0.85rem',
            color: '#5B21B6',
            lineHeight: 1.5,
          }}>
            <strong>Seccion unica del instrumento indigena.</strong> Estas preguntas capturan
            dimensiones de salud y bienestar desde la cosmovision de los pueblos, que no
            existen en ningun otro instrumento de medicion estatal. Representan la "capa
            propia" del diseno de doble capa del formulario SMT-ONIC.
          </div>

          <div style={fieldRow}>
            <label style={fieldLabel}>
              Desde la cosmovision de su pueblo, como se entiende su condicion?
              <span style={uniqueBadge}>propia</span>
            </label>
            <textarea
              disabled
              placeholder="Descripcion desde la perspectiva cultural del pueblo"
              style={{ ...fieldInput, minHeight: '70px', resize: 'none' }}
            />
          </div>

          <div style={fieldRow}>
            <label style={fieldLabel}>
              Presenta o ha presentado desarmonia espiritual?
              <span style={uniqueBadge}>propia</span>
            </label>
            <div style={radioRow}>
              <label style={radioLabel}><input type="radio" disabled /><span>Si</span></label>
              <label style={radioLabel}><input type="radio" disabled /><span>No</span></label>
              <label style={radioLabel}><input type="radio" disabled /><span>No sabe / No aplica</span></label>
            </div>
          </div>

          <div style={fieldRow}>
            <label style={fieldLabel}>
              Ha recibido atencion de medicina ancestral o tradicional?
              <span style={uniqueBadge}>propia</span>
            </label>
            <div style={radioRow}>
              <label style={radioLabel}><input type="radio" disabled /><span>Si, regularmente</span></label>
              <label style={radioLabel}><input type="radio" disabled /><span>Si, ocasionalmente</span></label>
              <label style={radioLabel}><input type="radio" disabled /><span>No, pero quisiera</span></label>
              <label style={radioLabel}><input type="radio" disabled /><span>No</span></label>
            </div>
          </div>

          <DisabledField
            label="Tipo de atencion ancestral recibida (si aplica)"
            placeholder="Medico tradicional, partera, uso de plantas medicinales, rituales..."
          />

          <div style={fieldRow}>
            <label style={fieldLabel}>
              Considera que la medicina occidental es suficiente para su bienestar?
              <span style={uniqueBadge}>propia</span>
            </label>
            <div style={radioRow}>
              <label style={radioLabel}><input type="radio" disabled /><span>Si</span></label>
              <label style={radioLabel}><input type="radio" disabled /><span>No</span></label>
              <label style={radioLabel}><input type="radio" disabled /><span>Parcialmente</span></label>
            </div>
          </div>

          <div style={fieldRow}>
            <label style={fieldLabel}>
              Relacion entre la condicion y la perdida del territorio o practicas rituales
              <span style={uniqueBadge}>propia</span>
            </label>
            <textarea
              disabled
              placeholder="Descripcion de la relacion percibida con el territorio, los rituales, la comunidad"
              style={{ ...fieldInput, minHeight: '60px', resize: 'none' }}
            />
          </div>
        </div>
      </div>

      {/* ================================================================
         BLOQUE H: Barreras Territoriales
         ================================================================ */}
      <div style={cardStyle}>
        <div style={blockHeader(ONIC_COLORS.H)}>
          <span style={blockBadge(ONIC_COLORS.H)}>H</span>
          Bloque H: Barreras Territoriales
        </div>
        <div style={blockBody}>
          <div style={{
            ...fieldLabel,
            marginBottom: '12px',
          }}>
            Seleccione todas las barreras que enfrenta la persona para acceder a servicios
            y ejercer sus derechos (seleccion multiple):
          </div>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(2, 1fr)',
            gap: '6px 20px',
          }}>
            {BARRERAS.map((b, i) => (
              <CheckboxOption key={i} label={b} />
            ))}
          </div>
          <DisabledField
            label="Otra barrera no listada"
            placeholder="Especificar"
          />
        </div>
      </div>

      {/* ================================================================
         BLOQUE I: Participacion y Autonomia
         ================================================================ */}
      <div style={cardStyle}>
        <div style={blockHeader(ONIC_COLORS.I)}>
          <span style={blockBadge(ONIC_COLORS.I)}>I</span>
          Bloque I: Participacion y Autonomia
        </div>
        <div style={blockBody}>
          <div style={fieldRow}>
            <label style={fieldLabel}>Participa en espacios comunitarios? (asambleas, mingas, rituales)</label>
            <div style={radioRow}>
              <label style={radioLabel}><input type="radio" disabled /><span>Si, activamente</span></label>
              <label style={radioLabel}><input type="radio" disabled /><span>Si, ocasionalmente</span></label>
              <label style={radioLabel}><input type="radio" disabled /><span>No, por barreras</span></label>
              <label style={radioLabel}><input type="radio" disabled /><span>No, por decision propia</span></label>
            </div>
          </div>
          <div style={fieldRow}>
            <label style={fieldLabel}>Puede tomar decisiones sobre su propia vida de manera autonoma?</label>
            <div style={radioRow}>
              <label style={radioLabel}><input type="radio" disabled /><span>Si, plenamente</span></label>
              <label style={radioLabel}><input type="radio" disabled /><span>Parcialmente, requiere apoyo</span></label>
              <label style={radioLabel}><input type="radio" disabled /><span>No, depende de otros</span></label>
            </div>
          </div>
          <div style={fieldRow}>
            <label style={fieldLabel}>Tiene acceso a educacion?</label>
            <div style={radioRow}>
              <label style={radioLabel}><input type="radio" disabled /><span>Si</span></label>
              <label style={radioLabel}><input type="radio" disabled /><span>No</span></label>
            </div>
          </div>
          <DisabledField label="Nivel educativo alcanzado" placeholder="Seleccionar" type="select" />
          <div style={fieldRow}>
            <label style={fieldLabel}>Realiza alguna actividad productiva o laboral?</label>
            <div style={radioRow}>
              <label style={radioLabel}><input type="radio" disabled /><span>Si</span></label>
              <label style={radioLabel}><input type="radio" disabled /><span>No</span></label>
            </div>
          </div>
          <DisabledField label="Tipo de actividad (si aplica)" placeholder="Agricultura, artesania, otro" />
        </div>
      </div>

      {/* ================================================================
         BLOQUE J: Lengua y Comunicacion
         ================================================================ */}
      <div style={cardStyle}>
        <div style={blockHeader(ONIC_COLORS.J)}>
          <span style={blockBadge(ONIC_COLORS.J)}>J</span>
          Bloque J: Lengua y Comunicacion
        </div>
        <div style={blockBody}>
          <DisabledField label="Lengua(s) que habla" placeholder="Seleccionar lengua(s)" type="select" />
          <div style={fieldRow}>
            <label style={fieldLabel}>Habla espanol?</label>
            <div style={radioRow}>
              <label style={radioLabel}><input type="radio" disabled /><span>Si, fluido</span></label>
              <label style={radioLabel}><input type="radio" disabled /><span>Si, basico</span></label>
              <label style={radioLabel}><input type="radio" disabled /><span>No</span></label>
            </div>
          </div>
          <div style={fieldRow}>
            <label style={fieldLabel}>Forma de comunicacion preferida</label>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <label style={radioLabel}><input type="radio" disabled /><span>Oral en lengua propia</span></label>
              <label style={radioLabel}><input type="radio" disabled /><span>Oral en espanol</span></label>
              <label style={radioLabel}><input type="radio" disabled /><span>Lengua de senas colombiana</span></label>
              <label style={radioLabel}><input type="radio" disabled /><span>Comunicacion alternativa / aumentativa</span></label>
              <label style={radioLabel}><input type="radio" disabled /><span>Otra</span></label>
            </div>
          </div>
          <div style={fieldRow}>
            <label style={fieldLabel}>Necesita interprete para acceder a servicios?</label>
            <div style={radioRow}>
              <label style={radioLabel}><input type="radio" disabled /><span>Si</span></label>
              <label style={radioLabel}><input type="radio" disabled /><span>No</span></label>
            </div>
          </div>
        </div>
      </div>

      {/* ================================================================
         Variables Propias vs Variables Comparables
         ================================================================ */}
      <div style={{
        ...cardStyle,
        background: 'linear-gradient(135deg, #fff 0%, #f5f0ff 100%)',
        border: '1px solid var(--color-gray-200)',
      }}>
        <div style={{ padding: '24px' }}>
          <h2 style={{ marginBottom: '16px', color: 'var(--color-primary)' }}>
            Variables propias vs Variables comparables
          </h2>
          <p style={{
            fontSize: '0.92rem',
            lineHeight: 1.7,
            color: 'var(--color-gray-600)',
            marginBottom: '20px',
          }}>
            El formulario SMT-ONIC utiliza un <strong>diseno de doble capa</strong>: una capa
            de variables comparables con los instrumentos estatales (CNPV, RLCPD) y una capa
            de variables propias que capturan dimensiones culturalmente significativas para
            los pueblos indigenas. Este diseno permite tanto la incidencia politica basada
            en datos comparables como la visibilizacion de realidades que el Estado no mide.
          </p>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '20px' }}>
            {/* Comparable */}
            <div style={{
              background: '#fff',
              borderRadius: 'var(--radius-md)',
              padding: '18px',
              border: '1px solid var(--color-green-mid)',
            }}>
              <div style={{
                fontSize: '0.85rem',
                fontWeight: 700,
                color: 'var(--color-green-mid)',
                marginBottom: '12px',
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
              }}>
                30 Variables comparables
              </div>
              <ul style={{ fontSize: '0.85rem', lineHeight: 1.7, color: 'var(--color-gray-600)', paddingLeft: '18px' }}>
                <li>Bloques A-F: Identificacion, demografia, dificultades funcionales (Washington Group), causa, salud, certificacion</li>
                <li>Permiten comparar con datos del CNPV 2018 del DANE</li>
                <li>Compatibles con el RLCPD y estandares internacionales</li>
                <li>Base para calcular brechas y tasas de prevalencia</li>
              </ul>
            </div>

            {/* Propias */}
            <div style={{
              background: '#fff',
              borderRadius: 'var(--radius-md)',
              padding: '18px',
              border: '1px solid #8B5CF6',
            }}>
              <div style={{
                fontSize: '0.85rem',
                fontWeight: 700,
                color: '#8B5CF6',
                marginBottom: '12px',
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
              }}>
                17 Variables propias
              </div>
              <ul style={{ fontSize: '0.85rem', lineHeight: 1.7, color: 'var(--color-gray-600)', paddingLeft: '18px' }}>
                <li>Bloque G: Cosmovision, desarmonia espiritual, medicina ancestral</li>
                <li>Bloque H: Barreras territoriales especificas</li>
                <li>Bloque I: Participacion comunitaria y autonomia</li>
                <li>Bloque J: Lengua propia y formas de comunicacion</li>
                <li>Capturan lo que el Estado no mide pero los pueblos necesitan visibilizar</li>
              </ul>
            </div>
          </div>

          {/* Stats summary */}
          <div style={{
            marginTop: '20px',
            background: 'var(--color-gold-light)',
            borderRadius: 'var(--radius-sm)',
            padding: '14px 18px',
            fontSize: '0.9rem',
            color: '#7a5a00',
            textAlign: 'center',
            lineHeight: 1.5,
          }}>
            <strong>Este formulario captura 47 variables:</strong> 30 comparables con el censo
            + 17 propias de los pueblos. El resultado es un instrumento que sirve tanto para
            la interlocucion con el Estado como para el fortalecimiento del gobierno propio.
          </div>
        </div>
      </div>
    </div>
  );
}
