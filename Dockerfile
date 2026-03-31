# AB-GEN 80% — Production Docker Image
# Multi-stage build: keeps final image lean (~2-3 GB with torch)

# ── Stage 1: Builder ───────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies
COPY requirements_prod.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --prefix=/install -r requirements_prod.txt

# ── Stage 2: Runtime ───────────────────────────────────────────────────
FROM python:3.11-slim

# Non-root user for security
RUN useradd -m -s /bin/bash abgen
WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY engine.py app.py serve.py ./
COPY templates/ templates/
COPY static/    static/

# Model bundles (must be built before: python export_bundle.py)
COPY abgen_bundle.pkl  ./
COPY sample_data.pkl   ./

# Training script needed for pickle deserialization
# Copy only the renamed production file (AB-GEM + CNN.py already deleted)
COPY ../AB-GEN_80_Accuracy.py /AB-GEN_80_Accuracy.py

# Environment
ENV ABGEN_HOST=0.0.0.0 \
    ABGEN_PORT=5000 \
    ABGEN_THREADS=4 \
    PYTHONUNBUFFERED=1

EXPOSE 5000

USER abgen
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/api/status')"

CMD ["python", "serve.py"]
