# 🛞 TireLife — Remaining Useful Life Estimator

A React app that estimates how many miles and years are left in your tires based on brand, usage, and tread depth.

---

## Getting Started

### Prerequisites
- [Node.js](https://nodejs.org/) v18 or newer
- npm (comes with Node)

### Install & run locally

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/tirelife.git
cd tirelife

# 2. Install dependencies
npm install

# 3. Start the dev server
npm run dev
```

Open http://localhost:5173 in your browser.

---

## Project Structure

```
tirelife/
├── index.html
├── vite.config.js
├── package.json
├── README.md
├── .gitignore
└── src/
    ├── main.jsx                   # React entry point
    ├── App.jsx                    # Root component + tab routing
    ├── index.css                  # Global styles
    ├── constants.js               # Tire brand specs & thresholds
    ├── utils/
    │   └── computeRUL.js          # Core RUL calculation logic
    └── components/
        ├── StructuredForm.jsx     # Manual input form
        ├── ResultCard.jsx         # Results display (gauge + metrics)
        ├── TreadGauge.jsx         # SVG semi-circle gauge
        └── ChatPlaceholder.jsx    # Stub for AI chat (see below)
```

---

## Adding the AI Chat Feature

The Chat tab currently shows a placeholder. To enable it:

### Step 1 — Get an Anthropic API key
Sign up at https://console.anthropic.com and create an API key.

### Step 2 — Create a backend proxy
**Never put your API key in frontend code.** Create a small backend to proxy requests:

#### Option A: Express (Node.js)
```bash
npm install express cors
```

```js
// server.js
import express from 'express'
import cors    from 'cors'

const app = express()
app.use(cors())
app.use(express.json())

app.post('/api/chat', async (req, res) => {
  const response = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': process.env.ANTHROPIC_API_KEY,
      'anthropic-version': '2023-06-01',
    },
    body: JSON.stringify(req.body),
  })
  const data = await response.json()
  res.json(data)
})

app.listen(3001, () => console.log('Proxy running on http://localhost:3001'))
```

Set your key: `ANTHROPIC_API_KEY=sk-... node server.js`

#### Option B: Next.js API Route
If you migrate to Next.js, add `app/api/chat/route.js` and use `ANTHROPIC_API_KEY` from `.env.local`.

### Step 3 — Implement ChatMode
Replace `src/components/ChatPlaceholder.jsx` with a real chat component that POSTs to `http://localhost:3001/api/chat`.

---

## Building for Production

```bash
npm run build
```

Output goes to `dist/`. Deploy to Vercel, Netlify, or any static host.

---

## License
MIT
