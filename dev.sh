#!/bin/sh
cd /app
uvicorn api:app --host 0.0.0.0 --port 8000 --reload &
pid=$!
trap 'kill "$pid"' EXIT INT TERM
cd /app/frontend
exec npm run dev -- --host 0.0.0.0
