# Imagen de la API REST (FastAPI + Uvicorn)
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    REPORTING_DIR=/app/data/08_reporting

WORKDIR /app

COPY api/requirements.txt ./api/requirements.txt
RUN pip install -r api/requirements.txt

COPY api ./api

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/health').status==200 else 1)"

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
