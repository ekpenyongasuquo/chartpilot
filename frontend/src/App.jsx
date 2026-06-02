/* App.jsx — ChartPilot Clinical Record Retrieval Agent */
import { useState, useCallback } from 'react'
import Header from './components/Header.jsx'
import QueryBar from './components/QueryBar.jsx'
import ResultCard from './components/ResultCard.jsx'
import QueryHistory from './components/QueryHistory.jsx'

const DOCTOR_ID = 'DR001'   // In production: from auth session
const API_BASE  = '/api'    // Proxied to FastAPI via vite.config.js

// ── Demo mode: returns realistic mock data when backend is offline ───────────
const DEMO_RESPONSES = {
  default: {
    success: true,
    query_interpreted: "Show last 2 malaria RDT results for patient with name containing 'Emeka'",
    summary: "Two malaria RDT results retrieved for Chukwuemeka Okeke (FMC-00402).\n\n" +
      "• 12-Mar-2026 — RDT: ⚠️ POSITIVE (P. falciparum). No ACT prescription recorded on this date.\n" +
      "• 04-Jan-2026 — RDT: Negative.\n\n" +
      "Note: Positive result in March had no corresponding treatment recorded — please verify.",
    records: [
      { result_id: "LR00142", patient_id: "FMC-00402", test_name: "Malaria RDT",
        result_value: "Positive", status: "CRITICAL", collected_date: "2026-03-12" },
      { result_id: "LR00089", patient_id: "FMC-00402", test_name: "Malaria RDT",
        result_value: "Negative", status: "COMPLETED", collected_date: "2026-01-04" },
    ],
    critical_flags: [
      {
        field: "Malaria RDT",
        value: "Positive",
        threshold: "Positive result",
        severity: "CRITICAL",
        message: "🚨 Malaria RDT: POSITIVE — treatment required",
      }
    ],
    record_count: 2,
    response_time_ms: 1247,
    requires_confirmation: false,
  },
  bp: {
    success: true,
    query_interpreted: "Show BP trend for patient FMC-00451 across last 3 visits",
    summary: "BP trend for FMC-00451 (Adaeze Balogun) — 3 visits reviewed:\n\n" +
      "• 18-May-2026 — BP: 🚨 195/122 mmHg (Hypertensive crisis)\n" +
      "• 02-Apr-2026 — BP: ⚠️ 168/105 mmHg (Stage 2 hypertension)\n" +
      "• 14-Feb-2026 — BP: 148/94 mmHg (Stage 1 hypertension)\n\n" +
      "Trend: Worsening. Currently on Amlodipine 5mg OD — consider escalation or referral to Cardiology.",
    records: [
      { vital_id: "VT00311", patient_id: "FMC-00451", bp_systolic: 195, bp_diastolic: 122,
        pulse: 98, recorded_date: "2026-05-18" },
      { vital_id: "VT00228", patient_id: "FMC-00451", bp_systolic: 168, bp_diastolic: 105,
        pulse: 88, recorded_date: "2026-04-02" },
      { vital_id: "VT00144", patient_id: "FMC-00451", bp_systolic: 148, bp_diastolic: 94,
        pulse: 82, recorded_date: "2026-02-14" },
    ],
    critical_flags: [
      {
        field: "Systolic BP",
        value: "195 mmhg",
        threshold: "> 180 mmhg",
        severity: "CRITICAL",
        message: "🚨 Systolic BP critically high: 195.0",
      },
      {
        field: "Diastolic BP",
        value: "122 mmhg",
        threshold: "> 120 mmhg",
        severity: "CRITICAL",
        message: "🚨 Diastolic BP critically high: 122.0",
      }
    ],
    record_count: 3,
    response_time_ms: 983,
    requires_confirmation: false,
  },
}

function getDemoResponse(query) {
  const q = query.toLowerCase()
  if (q.includes('bp') || q.includes('blood pressure') || q.includes('00451')) return DEMO_RESPONSES.bp
  return DEMO_RESPONSES.default
}

export default function App() {
  const [results, setResults]   = useState([])   // [{query, result}]
  const [loading, setLoading]   = useState(false)
  const [history, setHistory]   = useState([])
  const [error, setError]       = useState(null)
  const [demoMode, setDemoMode] = useState(false)

  const handleQuery = useCallback(async (query) => {
    setLoading(true)
    setError(null)

    try {
      const response = await fetch(`${API_BASE}/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, doctor_id: DOCTOR_ID }),
      })

      if (!response.ok) throw new Error(`Server error: ${response.status}`)
      const data = await response.json()

      addResult(query, data)
    } catch (err) {
      // Fall back to demo mode if backend is offline
      console.warn('Backend offline — using demo mode:', err.message)
      setDemoMode(true)
      const demoData = getDemoResponse(query)
      addResult(query, demoData)
    } finally {
      setLoading(false)
    }
  }, [])

  const addResult = (query, data) => {
    const now = new Date().toLocaleTimeString('en-NG', { hour: '2-digit', minute: '2-digit' })
    setResults(prev => [{ query, result: data, time: now }, ...prev])
    setHistory(prev => [{
      query,
      time: now,
      records: data.record_count || 0,
      flags: data.critical_flags?.length || 0,
      critical: data.critical_flags?.some(f => f.severity === 'CRITICAL'),
    }, ...prev].slice(0, 20))
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Header doctorId={DOCTOR_ID} />

      <div style={{
        flex: 1,
        display: 'grid',
        gridTemplateColumns: '240px 1fr',
        maxWidth: 1280,
        margin: '0 auto',
        width: '100%',
        padding: '0',
      }}>

        {/* Left sidebar — query history */}
        <aside style={{
          borderRight: '1px solid var(--border)',
          overflowY: 'auto',
          height: 'calc(100vh - 60px)',
          position: 'sticky',
          top: 60,
        }}>
          <QueryHistory history={history} onReplay={handleQuery} />
        </aside>

        {/* Main content */}
        <main style={{ padding: '32px 40px', overflowY: 'auto' }}>

          {/* Page heading */}
          <div style={{ marginBottom: 28 }}>
            <h1 style={{
              fontFamily: 'var(--font-display)',
              fontSize: 28,
              color: 'var(--text-primary)',
              marginBottom: 4,
              fontWeight: 400,
            }}>
              Clinical Record Retrieval
            </h1>
            <p style={{
              fontFamily: 'var(--font-body)',
              fontSize: 14, color: 'var(--text-muted)',
            }}>
              Ask naturally — patient name, ID, test, or date range.
              ChartPilot retrieves from HMIS in under 5 seconds.
            </p>
          </div>

          {/* Demo mode banner */}
          {demoMode && (
            <div style={{
              background: 'var(--amber-glow)',
              border: '1px solid var(--border-amber)',
              borderRadius: 'var(--radius)',
              padding: '10px 16px',
              marginBottom: 20,
              fontFamily: 'var(--font-mono)',
              fontSize: 11, letterSpacing: 1,
              color: 'var(--amber)',
              display: 'flex', alignItems: 'center', gap: 8,
            }}>
              <span>⚡</span>
              DEMO MODE — Backend offline. Showing simulated HMIS data.
              Start FastAPI server to connect to live database.
            </div>
          )}

          {/* Query input */}
          <QueryBar onSubmit={handleQuery} loading={loading} />

          {/* Loading state */}
          {loading && (
            <div style={{
              display: 'flex', alignItems: 'center', gap: 12,
              padding: '20px 0',
              fontFamily: 'var(--font-mono)',
              fontSize: 12, color: 'var(--text-muted)',
              letterSpacing: 1,
            }}>
              <span style={{ color: 'var(--amber)', animation: 'pulse 1s infinite' }}>●</span>
              QUERYING HMIS DATABASE VIA QWEN-MAX…
            </div>
          )}

          {/* Results */}
          {results.map((item, i) => (
            <div key={i}>
              {/* Query label */}
              <div style={{
                fontFamily: 'var(--font-mono)',
                fontSize: 11, color: 'var(--text-muted)',
                letterSpacing: 1, marginBottom: 10,
                display: 'flex', gap: 8, alignItems: 'center',
              }}>
                <span style={{ color: 'var(--amber)' }}>›</span>
                <span style={{
                  color: 'var(--text-secondary)',
                  fontFamily: 'var(--font-body)',
                  fontSize: 13,
                  fontStyle: 'italic',
                }}>{item.query}</span>
                <span style={{ marginLeft: 'auto' }}>{item.time}</span>
              </div>
              <ResultCard result={item.result} query={item.query} />
              {i < results.length - 1 && (
                <hr style={{
                  border: 'none',
                  borderTop: '1px solid var(--border)',
                  margin: '24px 0',
                }} />
              )}
            </div>
          ))}

          {/* Empty state */}
          {!results.length && !loading && (
            <EmptyState />
          )}
        </main>
      </div>
    </div>
  )
}

function EmptyState() {
  return (
    <div style={{
      textAlign: 'center',
      padding: '60px 0',
      animation: 'fadeIn 0.5s ease',
    }}>
      {/* Big icon */}
      <div style={{
        fontFamily: 'var(--font-display)',
        fontSize: 64,
        color: 'var(--bg-raised)',
        marginBottom: 24,
        lineHeight: 1,
      }}>
        ✚
      </div>
      <div style={{
        fontFamily: 'var(--font-display)',
        fontSize: 20,
        color: 'var(--text-muted)',
        marginBottom: 8,
        fontStyle: 'italic',
      }}>
        Ready to retrieve
      </div>
      <div style={{
        fontFamily: 'var(--font-body)',
        fontSize: 13,
        color: 'var(--text-muted)',
        maxWidth: 340,
        margin: '0 auto',
        lineHeight: 1.8,
      }}>
        Type a patient name, ID, test name, or date — in plain English,
        medical shorthand, or Nigerian Pidgin.
      </div>

      {/* Quick stat pills */}
      <div style={{
        display: 'flex', gap: 16, justifyContent: 'center',
        marginTop: 32, flexWrap: 'wrap',
      }}>
        {[
          { label: '30 Patients', sub: 'in demo DB' },
          { label: '400 Lab Results', sub: 'seeded' },
          { label: '< 5 Seconds', sub: 'retrieval target' },
        ].map(s => (
          <div key={s.label} style={{
            background: 'var(--bg-surface)',
            border: '1px solid var(--border)',
            borderRadius: 'var(--radius)',
            padding: '12px 20px',
          }}>
            <div style={{
              fontFamily: 'var(--font-mono)',
              fontSize: 14, color: 'var(--amber)',
              fontWeight: 700,
            }}>{s.label}</div>
            <div style={{
              fontFamily: 'var(--font-body)',
              fontSize: 11, color: 'var(--text-muted)',
              marginTop: 2,
            }}>{s.sub}</div>
          </div>
        ))}
      </div>
    </div>
  )
}
