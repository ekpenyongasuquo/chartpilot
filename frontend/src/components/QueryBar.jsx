/* QueryBar.jsx — Terminal-style clinical query input */
import { useState, useRef, useEffect } from 'react'

const EXAMPLE_QUERIES = [
  "Show me Emeka's last two malaria RDT results",
  "What was the BP trend for patient FMC-00451 in the last 3 visits?",
  "Any pending lab results for patients admitted yesterday?",
  "List all diabetic patients with HbA1c above 9 this month",
  "Show Ngozi's ANC visit history",
]

export default function QueryBar({ onSubmit, loading }) {
  const [query, setQuery] = useState('')
  const [exampleIdx, setExampleIdx] = useState(0)
  const [placeholder, setPlaceholder] = useState('')
  const inputRef = useRef(null)

  // Animated placeholder cycling
  useEffect(() => {
    const target = EXAMPLE_QUERIES[exampleIdx]
    let i = 0
    setPlaceholder('')
    const interval = setInterval(() => {
      setPlaceholder(target.slice(0, i))
      i++
      if (i > target.length) {
        clearInterval(interval)
        setTimeout(() => {
          setExampleIdx(idx => (idx + 1) % EXAMPLE_QUERIES.length)
        }, 2800)
      }
    }, 38)
    return () => clearInterval(interval)
  }, [exampleIdx])

  const handleSubmit = () => {
    if (!query.trim() || loading) return
    onSubmit(query.trim())
  }

  const handleKey = (e) => {
    if (e.key === 'Enter') handleSubmit()
  }

  const useExample = (q) => {
    setQuery(q)
    inputRef.current?.focus()
  }

  return (
    <div style={{ marginBottom: 32 }}>
      {/* Query input box */}
      <div style={{
        background: 'var(--bg-surface)',
        border: '1px solid var(--border-amber)',
        borderRadius: 16,
        padding: '4px 4px 4px 20px',
        display: 'flex',
        alignItems: 'center',
        gap: 12,
        boxShadow: '0 0 40px rgba(245,158,11,0.06)',
        transition: 'box-shadow 0.2s',
      }}
        onFocus={() => {}}
      >
        {/* Prompt symbol */}
        <span style={{
          fontFamily: 'var(--font-mono)',
          fontSize: 16,
          color: 'var(--amber)',
          flexShrink: 0,
          userSelect: 'none',
        }}>›</span>

        <input
          ref={inputRef}
          value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={handleKey}
          placeholder={placeholder + (placeholder.length < EXAMPLE_QUERIES[exampleIdx].length ? '|' : '')}
          disabled={loading}
          style={{
            flex: 1,
            background: 'transparent',
            border: 'none',
            outline: 'none',
            fontFamily: 'var(--font-mono)',
            fontSize: 15,
            color: 'var(--text-primary)',
            caretColor: 'var(--amber)',
            padding: '14px 0',
          }}
        />

        {/* Submit button */}
        <button
          onClick={handleSubmit}
          disabled={!query.trim() || loading}
          style={{
            background: query.trim() && !loading ? 'var(--amber)' : 'var(--bg-raised)',
            color: query.trim() && !loading ? '#0c0f14' : 'var(--text-muted)',
            border: 'none',
            borderRadius: 10,
            padding: '12px 24px',
            fontFamily: 'var(--font-mono)',
            fontSize: 13,
            fontWeight: 700,
            letterSpacing: 1,
            cursor: query.trim() && !loading ? 'pointer' : 'default',
            transition: 'all 0.15s',
            flexShrink: 0,
            minWidth: 110,
          }}
        >
          {loading ? (
            <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <LoadingDots /> QUERYING
            </span>
          ) : 'RETRIEVE →'}
        </button>
      </div>

      {/* Example chips */}
      <div style={{
        display: 'flex', gap: 8, marginTop: 12,
        flexWrap: 'wrap',
      }}>
        <span style={{
          fontFamily: 'var(--font-mono)',
          fontSize: 10,
          color: 'var(--text-muted)',
          letterSpacing: 1,
          alignSelf: 'center',
          flexShrink: 0,
        }}>TRY:</span>
        {EXAMPLE_QUERIES.slice(0, 3).map((q, i) => (
          <button key={i} onClick={() => useExample(q)} style={{
            background: 'var(--bg-raised)',
            border: '1px solid var(--border)',
            borderRadius: 20,
            padding: '4px 12px',
            fontFamily: 'var(--font-body)',
            fontSize: 12,
            color: 'var(--text-secondary)',
            cursor: 'pointer',
            transition: 'all 0.15s',
            textAlign: 'left',
          }}
            onMouseEnter={e => {
              e.target.style.borderColor = 'var(--amber-dim)'
              e.target.style.color = 'var(--amber)'
            }}
            onMouseLeave={e => {
              e.target.style.borderColor = 'var(--border)'
              e.target.style.color = 'var(--text-secondary)'
            }}
          >
            {q.length > 45 ? q.slice(0, 45) + '…' : q}
          </button>
        ))}
      </div>
    </div>
  )
}

function LoadingDots() {
  return (
    <span style={{ display: 'flex', gap: 3 }}>
      {[0, 1, 2].map(i => (
        <span key={i} style={{
          width: 4, height: 4, borderRadius: '50%',
          background: 'var(--text-muted)',
          animation: `pulse 1s ${i * 0.2}s infinite`,
          display: 'inline-block',
        }} />
      ))}
    </span>
  )
}
