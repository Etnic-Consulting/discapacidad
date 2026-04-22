import { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function LoginPage() {
  const { login, loading } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = location.state?.from || '/formulario';

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const onSubmit = async (e) => {
    e.preventDefault();
    setError('');
    try {
      await login(username.trim(), password);
      navigate(from, { replace: true });
    } catch (err) {
      setError(err.message || 'No fue posible iniciar sesion');
    }
  };

  return (
    <div style={{ minHeight: 'calc(100vh - 90px)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '40px 20px', background: 'var(--paper, #FAF6EC)' }}>
      <div style={{ width: '100%', maxWidth: '420px', background: '#fff', borderRadius: '12px', padding: '40px 36px', boxShadow: '0 8px 32px rgba(14, 31, 26, 0.08)', border: '1px solid var(--line, #E4DFD6)' }}>
        <div style={{ marginBottom: '28px', textAlign: 'center' }}>
          <div style={{ fontFamily: 'var(--mono, monospace)', fontSize: '0.7rem', color: 'var(--primary, #02432D)', letterSpacing: '0.12em', marginBottom: '8px' }}>
            SMT — ONIC / ACCESO DINAMIZADORES
          </div>
          <h1 style={{ fontFamily: 'var(--serif, Georgia)', fontSize: '1.8rem', fontWeight: 600, margin: 0, color: 'var(--ink, #0E1F1A)' }}>
            Iniciar sesion
          </h1>
          <p style={{ color: 'var(--ink-muted, #5B6B66)', fontSize: '0.9rem', marginTop: '6px' }}>
            Ingrese sus credenciales para registrar informacion
          </p>
        </div>

        <form onSubmit={onSubmit}>
          <label style={{ display: 'block', marginBottom: '16px' }}>
            <span style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: 'var(--ink-soft, #2D3A36)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '6px' }}>
              Usuario
            </span>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              autoFocus
              autoComplete="username"
              placeholder="Ingrese su usuario"
              style={inputStyle}
            />
          </label>

          <label style={{ display: 'block', marginBottom: '20px' }}>
            <span style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: 'var(--ink-soft, #2D3A36)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '6px' }}>
              Contrasena
            </span>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="current-password"
              placeholder="Ingrese su contrasena"
              style={inputStyle}
            />
          </label>

          {error && (
            <div role="alert" style={{ background: 'var(--alert-soft, #F9E1DB)', color: 'var(--alert, #B33A2F)', padding: '10px 14px', borderRadius: '6px', fontSize: '0.85rem', marginBottom: '16px', border: '1px solid var(--alert, #B33A2F)' }}>
              {error}
            </div>
          )}

          <button type="submit" disabled={loading} style={{
            width: '100%',
            background: loading ? 'var(--ink-faint)' : 'var(--primary, #02432D)',
            color: '#fff',
            border: 'none',
            padding: '12px 20px',
            borderRadius: '8px',
            fontWeight: 600,
            fontSize: '0.95rem',
            letterSpacing: '0.02em',
            cursor: loading ? 'wait' : 'pointer',
            transition: 'background 0.15s',
          }}>
            {loading ? 'Autenticando…' : 'Iniciar sesion'}
          </button>
        </form>

        <div style={{ marginTop: '24px', paddingTop: '16px', borderTop: '1px solid var(--line-soft, #EFEBE2)', fontSize: '0.78rem', color: 'var(--ink-muted, #5B6B66)', lineHeight: 1.5 }}>
          <strong style={{ color: 'var(--ink, #0E1F1A)' }}>Nota:</strong> El acceso al formulario esta restringido a dinamizadores
          autorizados por la Consejeria Mayor ONIC. Ante problemas de acceso contactar a <strong>poblacion@onic.org.co</strong>.
        </div>
      </div>
    </div>
  );
}

const inputStyle = {
  width: '100%',
  padding: '10px 14px',
  fontSize: '0.95rem',
  border: '1px solid var(--line, #E4DFD6)',
  borderRadius: '6px',
  background: '#fff',
  color: 'var(--ink, #0E1F1A)',
  fontFamily: 'var(--sans, sans-serif)',
  outline: 'none',
};
