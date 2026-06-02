/* Header.jsx */
export default function Header({ doctorId }) {
  return (
    <header style={{
      borderBottom: '1px solid var(--border)',
      background: 'var(--bg-surface)',
      padding: '0 32px',
      height: 60,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      position: 'sticky',
      top: 0,
      zIndex: 100,
      backdropFilter: 'blur(12px)',
    }}>
      {/* Logo */}
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 10 }}>
        <span style={{
          fontFamily: 'var(--font-display)',
          fontSize: 22,
          color: 'var(--amber)',
          letterSpacing: '-0.5px',
        }}>
          ChartPilot
        </span>
        <span style={{
          fontFamily: 'var(--font-mono)',
          fontSize: 10,
          color: 'var(--text-muted)',
          letterSpacing: 2,
          textTransform: 'uppercase',
        }}>
          v1.0 · FMC Calabar
        </span>
      </div>

      {/* Right side */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
        {/* NDPR badge */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: 6,
          background: 'var(--teal-dim)',
          border: '1px solid rgba(45,212,191,0.2)',
          borderRadius: 20,
          padding: '4px 10px',
        }}>
          <div style={{
            width: 6, height: 6, borderRadius: '50%',
            background: 'var(--teal)',
            animation: 'pulse 2s infinite',
          }} />
          <span style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 10,
            color: 'var(--teal)',
            letterSpacing: 1,
          }}>NDPR LOGGED</span>
        </div>

        {/* Doctor ID */}
        <div style={{
          fontFamily: 'var(--font-mono)',
          fontSize: 12,
          color: 'var(--text-secondary)',
        }}>
          <span style={{ color: 'var(--text-muted)' }}>DR · </span>
          {doctorId}
        </div>
      </div>
    </header>
  )
}
