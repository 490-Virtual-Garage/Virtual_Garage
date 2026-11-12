FROM python:3.12-slim-bookworm
WORKDIR /app
COPY obd_backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY obd_backend/ .
COPY rule_engine/ ./rule_engine/
CMD ["fastapi", "run", "main.py", "--port", "8000"]