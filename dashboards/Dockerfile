# Imagen del dashboard (Streamlit)
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    API_URL=http://api:8000 \
    REPORTING_DIR=/app/data/08_reporting

WORKDIR /app

COPY dashboards/requirements.txt ./dashboards/requirements.txt
RUN pip install -r dashboards/requirements.txt

COPY dashboards ./dashboards

EXPOSE 8501
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8501/_stcore/health').status==200 else 1)"

CMD ["streamlit", "run", "dashboards/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
