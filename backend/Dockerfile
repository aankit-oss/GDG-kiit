FROM python:3.11-slim

WORKDIR /app

# Install system deps (curl for healthcheck, libmagic for file detection)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create data directories
RUN mkdir -p /data/chroma /data/reports/audit

ENV CHROMA_PERSIST_PATH=/data/chroma
ENV REPORTS_DIR=/data/reports
ENV RULES_DIR=/rules

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
