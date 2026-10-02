# Container image for PolicyLens: the API and the built website in one service.
# Works on any host that runs a Dockerfile (Railway, Google Cloud Run, Fly.io, ...).
# The host must set ANTHROPIC_API_KEY; it provides PORT itself.

# --- Stage 1: build the React site into client/dist ---
FROM node:22-slim AS client
WORKDIR /app/client
COPY client/package.json client/package-lock.json ./
RUN npm ci
COPY client/ ./
RUN npm run build

# --- Stage 2: the Python server, which also serves client/dist ---
FROM python:3.11-slim
WORKDIR /app/server
COPY server/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY server/ ./
COPY --from=client /app/client/dist /app/client/dist

# Don't run as root inside the container.
RUN useradd --create-home policylens
USER policylens

# Hosts put a proxy in front of the app, so --proxy-headers lets the per-visitor
# rate limit see each visitor's real IP. "sh -c" lets ${PORT} come from the host.
ENV PORT=8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --proxy-headers --forwarded-allow-ips='*'"]
