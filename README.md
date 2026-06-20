# CodeLensAI

**Read code like a map.** Paste a function and CodeLensAI gives you three things at once:

1. A **plain-English, line-by-line breakdown** of what the code does.
2. An **AI-written summary** plus a **time-complexity estimate** (Big-O).
3. A **flowchart** of the control flow, rendered with Mermaid.

It supports **Python, JavaScript, and TypeScript**, runs entirely on free
infrastructure, and needs no API key to work.

Live: https://codelensai-zeta.vercel.app

---

## How it works

```
frontend/ (React + Vite)  ──fetch──>  api/explain.py  (Vercel Python function)
                                            │
                                            ├─ _lib/parser.py     Python -> IR (via ast)
                                            ├─ _lib/parser_js.py  JS/TS  -> IR (lightweight)
                                            ├─ _lib/explainer.py  IR -> plain-English steps
                                            ├─ _lib/graph.py      IR -> Mermaid flowchart
                                            └─ _lib/ai.py         IR + code -> AI summary + Big-O
```

The whole thing deploys to **one Vercel project**: the React app is served as
static files and the Python analyzer runs as a serverless function at
`/api/explain`. The backend uses **only the Python standard library**, so there
are no dependencies to install and cold starts stay quick.

### The AI part

`_lib/ai.py` asks a language model to summarize the code and estimate its
complexity. It tries providers in order and always degrades gracefully:

1. **Google Gemini** — used if `GEMINI_API_KEY` is set (free tier, no card).
2. **Pollinations** — a free, keyless endpoint used when no Gemini key exists.
3. **Built-in heuristic** — if both are unavailable, a deterministic Big-O
   estimate (from loop nesting) is returned so the app never breaks.

Because of the fallback chain, **CodeLensAI works out of the box for free.**
Adding a Gemini key just makes the AI summaries faster and more reliable.

---

## Running locally

You need **Node 18+** and **Python 3.10+**.

The simplest way to run the full stack (frontend + serverless API) locally is the
Vercel CLI, which mirrors production exactly:

```bash
npm i -g vercel
vercel dev
```

Or run just the frontend against the deployed API:

```bash
cd frontend
npm install
npm run dev   # set VITE_API_BASE to your API origin if needed
```

Run the tests (no network required):

```bash
python tests/test_parser.py
```

---

## Optional: add a free Gemini key

1. Create a key at https://aistudio.google.com/apikey (free, no credit card).
2. Add it to your Vercel project as an environment variable named
   `GEMINI_API_KEY`, then redeploy.

That's it — the app will automatically prefer Gemini for summaries.

---

## Author

Built by **Ishraq Basher** — Computer Science @ NYU Tandon.
