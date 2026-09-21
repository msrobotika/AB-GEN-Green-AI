# AB-GEN Research Demo — diagnostic runtime image
# Public code only. Trusted runtime artifacts are mounted read-only and verified
# against a trusted manifest before any joblib/pickle deserialization occurs.

FROM python:3.11-slim AS builder

WORKDIR /build
COPY requirements_prod.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --prefix=/install -r requirements_prod.txt

FROM python:3.11-slim

RUN useradd -m -s /bin/bash abgen
WORKDIR /app

COPY --from=builder /install /usr/local
COPY engine.py app.py serve.py docker_entrypoint.py runtime_integrity.py ./
COPY tools/ tools/
COPY templates/ templates/
COPY static/ static/

ENV ABGEN_HOST=0.0.0.0 \
    ABGEN_PORT=5000 \
    ABGEN_THREADS=4 \
    ABGEN_BUNDLE_PATH=/artifacts/abgen_bundle.pkl \
    ABGEN_SAMPLE_DATA_PATH=/artifacts/sample_data.pkl \
    ABGEN_TRAINING_MODULE_PATH=/artifacts/training_module.py \
    ABGEN_ARTIFACT_MANIFEST_PATH=/artifacts/runtime-manifest.json \
    ABGEN_REQUIRE_MANIFEST=1 \
    PYTHONUNBUFFERED=1

VOLUME ["/artifacts"]
EXPOSE 5000

USER abgen
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/api/status')"

CMD ["python", "docker_entrypoint.py"]
