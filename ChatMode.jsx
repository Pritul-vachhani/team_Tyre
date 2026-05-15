import { useState } from 'react'

const starterMessage =
  "Describe your tyre condition in plain English. Include tread depth, distance driven, age, and pressure if you know them."

function apiUrl(path) {
  const base = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')
  return base ? `${base}${path}` : path
}

function formatInt(value) {
  return Number(value || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })
}

function PredictionCard({ prediction }) {
  if (!prediction) return null

  return (
    <div style={{
      marginTop: 8,
      border: '1px solid #d1d5db',
      background: '#f8fafc',
      borderRadius: 10,
      padding: 12,
    }}>
      <div style={{ fontSize: 12, color: '#6b7280', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
        Predicted Remaining Life
      </div>
      <div style={{ marginTop: 4, fontSize: 24, fontWeight: 700, color: '#111' }}>
        {formatInt(prediction.predicted_rul_km)} km
      </div>
      <div style={{ marginTop: 2, fontSize: 13, color: '#6b7280' }}>
        {formatInt(prediction.predicted_rul_miles)} miles | model: {prediction.model}
      </div>
      <div style={{ marginTop: 6, fontSize: 12, color: '#6b7280' }}>
        Defaults used: {prediction.defaults_used_count}
      </div>
    </div>
  )
}

export default function ChatMode() {
  const [model, setModel] = useState('lightgbm')
  const [sessionId, setSessionId] = useState(null)
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [messages, setMessages] = useState([
    { role: 'assistant', text: starterMessage, prediction: null },
  ])
  const [missingFields, setMissingFields] = useState([])

  async function sendMessage(rawMessage, forcePredict = false) {
    const message = rawMessage.trim()
    if (!message || loading) return

    setMessages(m => [...m, { role: 'user', text: message, prediction: null }])
    setInput('')
    setLoading(true)

    try {
      const resp = await fetch(apiUrl('/api/chat'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          message,
          model,
          force_predict: forcePredict,
        }),
      })

      const data = await resp.json()
      if (!resp.ok) {
        throw new Error(data?.detail || 'Failed to call backend chat API')
      }

      setSessionId(data.session_id)
      setMissingFields(data.missing_fields || [])
      setMessages(m => [
        ...m,
        {
          role: 'assistant',
          text: data.assistant_message,
          prediction: data.prediction || null,
        },
      ])
    } catch (err) {
      setMessages(m => [
        ...m,
        {
          role: 'assistant',
          text: `Backend error: ${err.message}`,
          prediction: null,
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  function onSubmit(e) {
    e.preventDefault()
    sendMessage(input)
  }

  function resetChat() {
    setSessionId(null)
    setMissingFields([])
    setMessages([{ role: 'assistant', text: starterMessage, prediction: null }])
    setInput('')
  }

  return (
    <div>
      <div style={{ display: 'flex', gap: 8, marginBottom: 10 }}>
        <select
          value={model}
          onChange={e => setModel(e.target.value)}
          style={{
            flex: 1,
            border: '1px solid #d1d5db',
            borderRadius: 8,
            padding: '8px 10px',
            fontSize: 13,
            background: '#fff',
          }}
        >
          <option value="lightgbm">LightGBM (recommended)</option>
          <option value="deeplearning_test">Deep Learning Test (MLP)</option>
        </select>
        <button
          type="button"
          onClick={resetChat}
          style={{
            border: '1px solid #d1d5db',
            borderRadius: 8,
            background: '#fff',
            padding: '8px 12px',
            fontSize: 13,
            cursor: 'pointer',
          }}
        >
          Reset
        </button>
      </div>

      <div style={{
        border: '1px solid #e5e7eb',
        background: '#fff',
        borderRadius: 12,
        padding: 12,
        maxHeight: 380,
        overflowY: 'auto',
      }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {messages.map((m, idx) => (
            <div
              key={idx}
              style={{
                alignSelf: m.role === 'user' ? 'flex-end' : 'flex-start',
                maxWidth: '92%',
              }}
            >
              <div
                style={{
                  borderRadius: 10,
                  padding: '9px 11px',
                  fontSize: 14,
                  lineHeight: 1.5,
                  whiteSpace: 'pre-wrap',
                  background: m.role === 'user' ? '#111827' : '#f3f4f6',
                  color: m.role === 'user' ? '#fff' : '#111827',
                }}
              >
                {m.text}
              </div>
              <PredictionCard prediction={m.prediction} />
            </div>
          ))}
          {loading && (
            <div style={{ fontSize: 12, color: '#6b7280', animation: 'pulse 1.2s ease-in-out infinite' }}>
              Thinking...
            </div>
          )}
        </div>
      </div>

      {missingFields.length > 0 && (
        <button
          type="button"
          onClick={() => sendMessage('use defaults', true)}
          disabled={loading}
          style={{
            marginTop: 10,
            width: '100%',
            border: '1px solid #d1d5db',
            borderRadius: 8,
            background: '#f8fafc',
            padding: '9px 10px',
            fontSize: 13,
            cursor: loading ? 'not-allowed' : 'pointer',
          }}
        >
          Predict Now With Defaults
        </button>
      )}

      <form onSubmit={onSubmit} style={{ marginTop: 10, display: 'flex', gap: 8 }}>
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          placeholder="Example: tread is 4.5 mm, driven 28000 km, pressure 32 psi, tyre age 3 years"
          style={{
            flex: 1,
            border: '1px solid #d1d5db',
            borderRadius: 8,
            padding: '10px 12px',
            fontSize: 14,
          }}
        />
        <button
          type="submit"
          disabled={loading}
          style={{
            border: 'none',
            borderRadius: 8,
            padding: '10px 14px',
            fontSize: 14,
            fontWeight: 600,
            background: '#111',
            color: '#fff',
            cursor: loading ? 'not-allowed' : 'pointer',
          }}
        >
          Send
        </button>
      </form>
    </div>
  )
}
