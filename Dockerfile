# Simple, single-stage Dockerfile for the Streamlit app - kept minimal on
# purpose so it's easy for a student to read top to bottom.

FROM python:3.11-slim

WORKDIR /app

# System deps needed by faiss-cpu / pypdf wheels on slim images
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Cloud Run injects $PORT; default to 8080 for local `docker run`.
ENV PORT=8080
EXPOSE 8080

CMD streamlit run streamlit_app/app.py \
    --server.port=${PORT} \
    --server.address=0.0.0.0 \
    --server.headless=true
