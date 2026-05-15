import TreadGauge from './TreadGauge.jsx'

const metricCard = {
  background: '#f8f9fa',
  border: '1px solid #e5e7eb',
  borderRadius: 10,
  padding: '14px 10px',
  textAlign: 'center',
}

export default function ResultCard({ result }) {
  const { remainingMiles, remainingYears, remainingTread, pctLeft, status, color, ageFactor } = result

  const metrics = [
    { label: 'Miles Left',   value: Math.round(remainingMiles).toLocaleString(), unit: 'mi'  },
    { label: 'Years Left',   value: remainingYears.toFixed(1),                   unit: 'yrs' },
    { label: 'Tread Depth',  value: remainingTread.toFixed(1),                   unit: 'mm'  },
  ]

  return (
    <div style={{ marginTop: '2rem' }}>
      {/* Gauge + status badge */}
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', marginBottom: '1.5rem' }}>
        <TreadGauge pct={pctLeft} color={color} />
        <div style={{
          marginTop: '0.5rem',
          padding: '4px 18px',
          background: color + '22',
          border: `1.5px solid ${color}`,
          borderRadius: 999,
          color,
          fontWeight: 700,
          fontSize: 13,
          letterSpacing: '0.08em',
        }}>
          {status}
        </div>
      </div>

      {/* Metric cards */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 10 }}>
        {metrics.map(m => (
          <div key={m.label} style={metricCard}>
            <div style={{ fontSize: 11, color: '#9ca3af', marginBottom: 4, letterSpacing: '0.07em', textTransform: 'uppercase' }}>
              {m.label}
            </div>
            <div style={{ fontSize: 22, fontWeight: 700, color: '#111', fontFamily: "'JetBrains Mono', monospace" }}>
              {m.value}
            </div>
            <div style={{ fontSize: 11, color: '#9ca3af' }}>{m.unit}</div>
          </div>
        ))}
      </div>

      {/* Age warning */}
      {ageFactor && (
        <div style={{
          marginTop: '1rem',
          padding: '10px 14px',
          background: '#fef3c7',
          border: '1px solid #fcd34d',
          borderRadius: 8,
          fontSize: 12,
          color: '#92400e',
        }}>
          {ageFactor}
        </div>
      )}
    </div>
  )
}
