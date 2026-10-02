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

## Put it online (Google Cloud Run)

The `Dockerfile` in the repo root builds the website and the server into one container.
Cloud Run builds it from GitHub and redeploys on every push to `main`. Low use fits in
Google Cloud's free tier, but Google needs a billing account (card) on file.

1. Go to https://console.cloud.google.com, create a project (e.g. `policylens`) and
   set up billing when asked.
2. Open **Cloud Run** and click **Deploy container**, then choose
   **Continuously deploy from a repository**, then **Set up with Cloud Build**.
3. Connect GitHub, pick this repository and branch `main`, choose **Dockerfile**
   as the build type (path `/Dockerfile`), and save.
4. Settings:
   - **Region:** one near your users, e.g. `europe-west1`.
   - **Authentication:** **Allow public access** (the extension and website need to reach it).
   - **Scaling:** minimum instances `0`, **maximum instances `1`**. The rate limits are
     kept in memory, so one instance keeps them accurate, and it also caps the cost.
   - **Variables & secrets:** add `ANTHROPIC_API_KEY` (your key) and
     `DAILY_ANALYSIS_LIMIT` (`100`, the most analyses per day for everyone combined).
5. Click **Create**. When the build finishes, the app's address is shown at the top,
   like `https://policylens-xxxx.europe-west1.run.app`.

As safety nets, set a budget alert under **Billing > Budgets & alerts** in Google Cloud,
and a monthly spend limit in the Anthropic Console.

**Browser extension:** see [extension/README.md](extension/README.md).

## Tests

```bash
cd server
python -m unittest                                                   # free, no API calls
POLICYLENS_LIVE_TESTS=1 python -m unittest tests.test_real_policies -v   # real API calls on 5 real policies
```

See `PLAN.md` for the build stages and decisions, and `CLAUDE.md` for project conventions.
