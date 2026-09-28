FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN python3 -m pip install --no-cache-dir -r requirements.txt

COPY elm_client.py .

EXPOSE 35000