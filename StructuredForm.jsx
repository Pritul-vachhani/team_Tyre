import { useState } from 'react'
import { TIRE_BRANDS } from '../constants.js'
import { computeRUL } from '../utils/computeRUL.js'
import ResultCard from './ResultCard.jsx'

const labelStyle = {
  fontSize: 12,
  fontWeight: 600,
  color: '#6b7280',
  letterSpacing: '0.07em',
  textTransform: 'uppercase',
  marginBottom: 5,
  display: 'block',
}

function inputStyle(hasError) {
  return {
    width: '100%',
    padding: '9px 12px',
    borderRadius: 8,
    border: `1px solid ${hasError ? '#ef4444' : '#d1d5db'}`,
    fontSize: 14,
    background: '#fff',
    fontFamily: "'JetBrains Mono', monospace",
    boxSizing: 'border-box',
  }
}

export default function StructuredForm() {
  const [form, setForm] = useState({
    brand:        'Michelin Pilot Sport 4S',
    yearsOwned:   '',
    milesPerDay:  '',
    currentTread: '',
  })
  const [errors, setErrors]   = useState({})
  const [result, setResult]   = useState(null)

  const set = (key, value) => setForm(f => ({ ...f, [key]: value }))

  function validate() {
    const e = {}
    if (!form.yearsOwned || isNaN(form.yearsOwned) || +form.yearsOwned < 0)
      e.yearsOwned = 'Enter a valid number of years'
    if (!form.milesPerDay || isNaN(form.milesPerDay) || +form.milesPerDay <= 0)
      e.milesPerDay = 'Enter miles per day (must be > 0)'
    if (form.currentTread !== '' && (isNaN(form.currentTread) || +form.currentTread < 0 || +form.currentTread > 15))
      e.currentTread = 'Enter a value between 0–15 mm, or leave blank'
    return e
  }

  function handleSubmit() {
    const e = validate()
    if (Object.keys(e).length) { setErrors(e); return }
    setErrors({})
    setResult(computeRUL({
      yearsOwned:   +form.yearsOwned,
      milesPerDay:  +form.milesPerDay,
      brand:        form.brand,
      currentTread: form.currentTread,
    }))
  }

  return (
    <div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
        {/* Brand */}
        <div style={{ gridColumn: '1 / -1' }}>
          <label style={labelStyle}>Tire Brand &amp; Model</label>
          <select
            value={form.brand}
            onChange={e => set('brand', e.target.value)}
            style={{ ...inputStyle(false), cursor: 'pointer' }}
          >
            {Object.keys(TIRE_BRANDS).map(b => <option key={b}>{b}</option>)}
          </select>
        </div>

        {/* Years owned */}
        <div>
          <label style={labelStyle}>Years Owned</label>
          <input
            type="number" min="0" placeholder="e.g. 2"
            value={form.yearsOwned}
            onChange={e => set('yearsOwned', e.target.value)}
            style={inputStyle(errors.yearsOwned)}
          />
          {errors.yearsOwned && <div style={{ fontSize: 11, color: '#ef4444', marginTop: 3 }}>{errors.yearsOwned}</div>}
        </div>

        {/* Miles per day */}
        <div>
          <label style={labelStyle}>Miles per Day</label>
          <input
            type="number" min="1" placeholder="e.g. 30"
            value={form.milesPerDay}
            onChange={e => set('milesPerDay', e.target.value)}
            style={inputStyle(errors.milesPerDay)}
          />
          {errors.milesPerDay && <div style={{ fontSize: 11, color: '#ef4444', marginTop: 3 }}>{errors.milesPerDay}</div>}
        </div>

        {/* Tread depth (optional) */}
        <div style={{ gridColumn: '1 / -1' }}>
          <label style={labelStyle}>
            Current Tread Depth (mm){' '}
            <span style={{ fontWeight: 400, textTransform: 'none', color: '#9ca3af' }}>— optional</span>
          </label>
          <input
            type="number" min="0" max="15" step="0.5"
            placeholder="Leave blank to auto-estimate"
            value={form.currentTread}
            onChange={e => set('currentTread', e.target.value)}
            style={inputStyle(errors.currentTread)}
          />
          {errors.currentTread && <div style={{ fontSize: 11, color: '#ef4444', marginTop: 3 }}>{errors.currentTread}</div>}
        </div>
      </div>

      <button
        onClick={handleSubmit}
        style={{
          marginTop: '1.25rem', width: '100%', padding: '11px',
          background: '#111', color: '#fff', border: 'none',
          borderRadius: 9, fontSize: 14, fontWeight: 600,
          cursor: 'pointer', letterSpacing: '0.05em',
        }}
        onMouseOver={e => (e.currentTarget.style.background = '#374151')}
        onMouseOut={e  => (e.currentTarget.style.background = '#111')}
      >
        Calculate Remaining Life →
      </button>

      {result && <ResultCard result={result} />}
    </div>
  )
}
