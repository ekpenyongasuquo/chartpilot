/* QueryHistory.jsx — Left sidebar showing recent queries */
export default function QueryHistory({ history, onReplay }) {
  if (!history.length) return (
    <div style={{
      padding: '20px 16px',
      fontFamily: 'var(--font-mono)',
      fontSize: 11, color: 'var(--text-muted)',
      letterSpacing: 1, textAlign: 'center',
      lineHeight: 2,
    }}>
      NO QUERIES YET<br />
      <span style={{ fontSize: 10 }}>Your session history<br />will appear here</span>
    </div>
  )

  return (
    <div style={{ padding: '8px 0' }}>
      <div style={{
        padding: '8px 16px 12px',
        fontFamily: 'var(--font-mono)',
        fontSize: 10, letterSpacing: 2,
        color: 'var(--text-muted)',
        borderBottom: '1px solid var(--border)',
        marginBottom: 4,
      }}>
        SESSION HISTORY
      </div>
      {history.map((item, i) => (
        <button key={i} onClick={() => onReplay(item.query)}
          style={{
            display: 'block', width: '100%',
            background: 'transparent',
            border: 'none',
            borderBottom: '1px solid var(--border)',
            padding: '10px 16px',
            textAlign: 'left',
            cursor: 'pointer',
            transition: 'background 0.12s',
          }}
          onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-hover)'}
          onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
        >
          <div style={{
            fontFamily: 'var(--font-body)',
            fontSize: 12, color: 'var(--text-secondary)',
            lineHeight: 1.5, marginBottom: 4,
            display: '-webkit-box',
            WebkitLineClamp: 2,
            WebkitBoxOrient: 'vertical',
            overflow: 'hidden',
          }}>
            {item.query}
          </div>
          <div style={{
            display: 'flex', gap: 8, alignItems: 'center',
          }}>
            <span style={{
              fontFamily: 'var(--font-mono)',
              fontSize: 10, color: 'var(--text-muted)',
            }}>{item.time}</span>
            {item.flags > 0 && (
              <span style={{
                fontFamily: 'var(--font-mono)',
                fontSize: 9, letterSpacing: 1,
                color: item.critical ? 'var(--red)' : 'var(--orange)',
                background: item.critical ? 'var(--red-dim)' : 'var(--orange-dim)',
                padding: '1px 6px', borderRadius: 10,
              }}>
                {item.flags} FLAG{item.flags > 1 ? 'S' : ''}
              </span>
            )}
            <span style={{
              fontFamily: 'var(--font-mono)',
              fontSize: 9,
              color: 'var(--text-muted)',
            }}>{item.records} rec</span>
          </div>
        </button>
      ))}
    </div>
  )
}
