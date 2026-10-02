# PolicyLens

Paste a privacy policy or terms of service (as a link, text, or PDF) and get:

1. Five plain-language bullets: what's collected, who it's shared with, how long it's kept, your rights, and anything surprising.
2. A Low / Medium / High risk level with a one-line reason.
3. The exact sentence from the policy behind each bullet, checked against the source so it can be trusted.

Also included: a **Compare** tab for two policies side by side, an **App permissions** explainer
for Android and iOS, and a **browser extension** (`extension/`).

This is a summary, not legal advice.

## Run it locally

Needs Python 3.11+, Node 20+, and an Anthropic API key.

**Backend** (terminal 1):
```bash
cd server
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # then put your ANTHROPIC_API_KEY in .env
python -m app.main          # http://127.0.0.1:8000/api/health
```

**Frontend** (terminal 2):
```bash
cd client
npm install
npm run dev                 # http://localhost:5173
```

**One server for production:** run `npm run build` in `client/`, then start the backend;
it serves the built app at http://127.0.0.1:8000 alongside the API.

**Browser extension:** see [extension/README.md](extension/README.md).

## Tests

```bash
cd server
python -m unittest                                                   # free, no API calls
POLICYLENS_LIVE_TESTS=1 python -m unittest tests.test_real_policies -v   # real API calls on 5 real policies
```

See `PLAN.md` for the build stages and decisions, and `CLAUDE.md` for project conventions.
