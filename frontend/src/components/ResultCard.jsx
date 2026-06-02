/* ResultCard.jsx — Clinical result display with flags and raw records */
import { useState } from 'react'

export default function ResultCard({ result, query }) {
  const [showRaw, setShowRaw] = useState(false)

  if (!result) return null

  const hasCritical = result.critical_flags?.some(f => f.severity === 'CRITICAL')
  const hasWarning = result.critical_flags?.some(f => f.severity === 'WARNING')

  return (
    <div style={{
      animation: 'fadeSlideUp 0.35s ease both',
      marginBottom: 24,
    }}>
      {/* Result header bar */}
      <div style={{
        display: 'flex', alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: 12,
      }}>
        <div style={{
          fontFamily: 'var(--font-mono)',
          fontSize: 11,
          color: 'var(--text-muted)',
          letterSpacing: 1,
        }}>
          QUERY RESULT · {result.record_count} RECORD{result.record_count !== 1 ? 'S' : ''} · {result.response_time_ms}ms
        </div>
        <div style={{
          fontFamily: 'var(--font-mono)',
          fontSize: 11,
          color: result.success ? 'var(--teal)' : 'var(--red)',
          letterSpacing: 1,
        }}>
          {result.success ? '● RETRIEVED' : '● FAILED'}
        </div>
      </div>

      {/* Critical flags — shown first if present */}
      {result.critical_flags?.length > 0 && (
        <div style={{ marginBottom: 16, display: 'flex', flexDirection: 'column', gap: 8 }}>
          {result.critical_flags.map((flag, i) => (
            <FlagBanner key={i} flag={flag} delay={i * 0.08} />
          ))}
        </div>
      )}

      {/* Interpreted query */}
      <div style={{
        background: 'var(--bg-surface)',
        border: '1px solid var(--border)',
        borderRadius: 'var(--radius)',
        padding: '10px 16px',
        marginBottom: 12,
        display: 'flex', gap: 10, alignItems: 'flex-start',
      }}>
        <span style={{
          fontFamily: 'var(--font-mono)', fontSize: 10,
          color: 'var(--text-muted)', letterSpacing: 1,
          flexShrink: 0, marginTop: 2,
        }}>INTERPRETED AS</span>
        <span style={{
          fontFamily: 'var(--font-body)', fontSize: 13,
          color: 'var(--text-secondary)', fontStyle: 'italic',
        }}>
          {result.query_interpreted}
        </span>
      </div>

      {/* Clinical summary — the main output */}
      <div style={{
        background: hasCritical
          ? 'rgba(239,68,68,0.05)'
          : hasWarning
            ? 'rgba(249,115,22,0.05)'
            : 'var(--bg-surface)',
        border: `1px solid ${hasCritical
          ? 'rgba(239,68,68,0.25)'
          : hasWarning
            ? 'rgba(249,115,22,0.2)'
            : 'var(--border-amber)'}`,
        borderRadius: 'var(--radius-lg)',
        padding: '20px 24px',
        marginBottom: 12,
      }}>
        <div style={{
          fontFamily: 'var(--font-mono)',
          fontSize: 10, letterSpacing: 2,
          color: 'var(--amber)', marginBottom: 12,
        }}>
          CLINICAL SUMMARY
        </div>
        <div style={{
          fontFamily: 'var(--font-body)',
          fontSize: 15, lineHeight: 1.75,
          color: 'var(--text-primary)',
          whiteSpace: 'pre-wrap',
        }}>
          {result.summary}
        </div>
      </div>

      {/* Confirmation gate (human-in-the-loop) */}
      {result.requires_confirmation && (
        <ConfirmationGate result={result} />
      )}

      {/* Raw records toggle */}
      {result.records?.length > 0 && (
        <div>
          <button
            onClick={() => setShowRaw(!showRaw)}
            style={{
              background: 'transparent',
              border: '1px solid var(--border)',
              borderRadius: 'var(--radius)',
              padding: '8px 16px',
              fontFamily: 'var(--font-mono)',
              fontSize: 11, letterSpacing: 1,
              color: 'var(--text-muted)',
              cursor: 'pointer',
              transition: 'all 0.15s',
              marginBottom: showRaw ? 12 : 0,
            }}
            onMouseEnter={e => {
              e.target.style.borderColor = 'var(--border-amber)'
              e.target.style.color = 'var(--amber)'
            }}
            onMouseLeave={e => {
              e.target.style.borderColor = 'var(--border)'
              e.target.style.color = 'var(--text-muted)'
            }}
          >
            {showRaw ? '▾' : '▸'} RAW RECORDS ({result.records.length})
          </button>

          {showRaw && (
            <div style={{
              background: 'var(--bg-surface)',
              border: '1px solid var(--border)',
              borderRadius: 'var(--radius)',
              overflow: 'auto',
              maxHeight: 320,
              animation: 'fadeIn 0.2s ease',
            }}>
              <RawTable records={result.records} />
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function FlagBanner({ flag, delay }) {
  const isCritical = flag.severity === 'CRITICAL'
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 12,
      background: isCritical ? 'var(--red-dim)' : 'var(--orange-dim)',
      border: `1px solid ${isCritical ? 'rgba(239,68,68,0.35)' : 'rgba(249,115,22,0.3)'}`,
      borderRadius: 'var(--radius)',
      padding: '10px 16px',
      animation: `flagPop 0.3s ${delay}s ease both`,
    }}>
      <span style={{ fontSize: 18, flexShrink: 0 }}>
        {isCritical ? '🚨' : '⚠️'}
      </span>
      <div style={{ flex: 1 }}>
        <div style={{
          fontFamily: 'var(--font-mono)',
          fontSize: 11, letterSpacing: 1,
          color: isCritical ? 'var(--red)' : 'var(--orange)',
          marginBottom: 2,
        }}>
          {flag.severity} — {flag.field}
        </div>
        <div style={{
          fontFamily: 'var(--font-body)',
          fontSize: 13,
          color: 'var(--text-primary)',
        }}>
          {flag.message} &nbsp;
          <span style={{ color: 'var(--text-muted)', fontSize: 12 }}>
            (ref: {flag.threshold})
          </span>
        </div>
      </div>
    </div>
  )
}

function ConfirmationGate({ result }) {
  const [confirmed, setConfirmed] = useState(null)

  if (confirmed !== null) {
    return (
      <div style={{
        padding: '12px 16px',
        background: confirmed ? 'var(--teal-dim)' : 'var(--bg-raised)',
        border: `1px solid ${confirmed ? 'rgba(45,212,191,0.3)' : 'var(--border)'}`,
        borderRadius: 'var(--radius)',
        fontFamily: 'var(--font-mono)',
        fontSize: 12,
        color: confirmed ? 'var(--teal)' : 'var(--text-muted)',
        marginBottom: 12,
      }}>
        {confirmed ? '✓ Action confirmed and executed.' : '✗ Action cancelled.'}
      </div>
    )
  }

  return (
    <div style={{
      background: 'var(--orange-dim)',
      border: '1px solid rgba(249,115,22,0.3)',
      borderRadius: 'var(--radius)',
      padding: '16px 20px',
      marginBottom: 12,
      animation: 'flagPop 0.3s ease both',
    }}>
      <div style={{
        fontFamily: 'var(--font-mono)',
        fontSize: 11, letterSpacing: 1,
        color: 'var(--orange)', marginBottom: 8,
      }}>
        ⚡ CONFIRMATION REQUIRED
      </div>
      <div style={{
        fontFamily: 'var(--font-body)',
        fontSize: 14, color: 'var(--text-primary)',
        marginBottom: 16,
      }}>
        {result.summary}
      </div>
      <div style={{ display: 'flex', gap: 10 }}>
        <button onClick={() => setConfirmed(true)} style={{
          background: 'var(--orange)',
          color: '#fff',
          border: 'none', borderRadius: 'var(--radius)',
          padding: '8px 20px',
          fontFamily: 'var(--font-mono)', fontSize: 12,
          fontWeight: 700, letterSpacing: 1,
          cursor: 'pointer',
        }}>CONFIRM</button>
        <button onClick={() => setConfirmed(false)} style={{
          background: 'transparent',
          color: 'var(--text-muted)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius)',
          padding: '8px 20px',
          fontFamily: 'var(--font-mono)', fontSize: 12,
          letterSpacing: 1, cursor: 'pointer',
        }}>CANCEL</button>
      </div>
    </div>
  )
}

function RawTable({ records }) {
  if (!records.length) return null
  const cols = Object.keys(records[0])

  return (
    <table style={{
      width: '100%', borderCollapse: 'collapse',
      fontFamily: 'var(--font-mono)', fontSize: 12,
    }}>
      <thead>
        <tr style={{ background: 'var(--bg-raised)' }}>
          {cols.map(c => (
            <th key={c} style={{
              padding: '8px 14px',
              textAlign: 'left',
              color: 'var(--text-muted)',
              letterSpacing: 1,
              fontSize: 10,
              borderBottom: '1px solid var(--border)',
              whiteSpace: 'nowrap',
            }}>{c.toUpperCase()}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {records.map((row, i) => (
          <tr key={i} style={{
            borderBottom: '1px solid var(--border)',
            background: i % 2 === 0 ? 'transparent' : 'var(--bg-raised)',
          }}>
            {cols.map(c => (
              <td key={c} style={{
                padding: '7px 14px',
                color: c.includes('status') && row[c] === 'CRITICAL'
                  ? 'var(--red)'
                  : c.includes('status') && row[c] === 'COMPLETED'
                    ? 'var(--teal)'
                    : 'var(--text-secondary)',
                whiteSpace: 'nowrap',
                maxWidth: 200,
                overflow: 'hidden',
                textOverflow: 'ellipsis',
              }}>
                {row[c] ?? '—'}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  )
}
