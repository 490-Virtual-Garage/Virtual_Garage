FROM python:3.12-slim-bookworm

# Vite 8 needs Node 22. Copy the official binary into this Python image
# so the scanner and the website share one Dockerfile.
COPY --from=node:22-bookworm-slim /usr/local/bin/node /usr/local/bin/node
COPY --from=node:22-bookworm-slim /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -sf ../lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm \
    && ln -sf ../lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN python3 -m pip install --no-cache-dir -r requirements.txt

COPY elm_client.py .

COPY frontend/package.json frontend/package-lock.json frontend/
RUN npm ci --prefix frontend

COPY frontend frontend/

EXPOSE 35000 5173
