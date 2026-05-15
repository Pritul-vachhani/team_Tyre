/**
 * ChatMode — AI-powered chat interface (coming soon)
 *
 * To implement:
 * 1. Create a backend proxy (e.g. Express or Next.js API route) that holds
 *    your ANTHROPIC_API_KEY and forwards requests to https://api.anthropic.com/v1/messages
 * 2. Replace the fetch() call in this component to point at your proxy endpoint
 * 3. Remove this placeholder and wire up the real ChatMode component
 *
 * See README.md for setup instructions.
 */
export default function ChatPlaceholder() {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: 320,
      gap: '1rem',
      color: '#9ca3af',
      textAlign: 'center',
      padding: '2rem',
    }}>
      <div style={{ fontSize: 40 }}>🛠</div>
      <div style={{ fontSize: 16, fontWeight: 600, color: '#6b7280' }}>AI Chat — Coming Soon</div>
      <div style={{ fontSize: 13, maxWidth: 320, lineHeight: 1.6 }}>
        This tab will let you describe your tires in plain English and get an instant RUL estimate.
        A backend API proxy needs to be set up first — see <code>README.md</code> for instructions.
      </div>
      <div style={{
        marginTop: '0.5rem',
        padding: '8px 16px',
        background: '#f3f4f6',
        border: '1px solid #e5e7eb',
        borderRadius: 8,
        fontSize: 12,
        fontFamily: "'JetBrains Mono', monospace",
        color: '#374151',
      }}>
        src/components/ChatMode.jsx  ← add your implementation here
      </div>
    </div>
  )
}
