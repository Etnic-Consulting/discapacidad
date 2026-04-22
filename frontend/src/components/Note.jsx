export default function Note({ label = 'Nota metodológica', children }) {
  return (
    <div className="note">
      <div className="note-label">{label}</div>
      <p>{children}</p>
    </div>
  );
}
