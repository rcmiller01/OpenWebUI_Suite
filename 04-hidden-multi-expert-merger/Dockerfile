ARG BASE_IMAGE=owui/base:py311
FROM ${BASE_IMAGE} as runtime

WORKDIR /app

COPY requirements.txt ./requirements.txt
RUN pip install -r requirements.txt -c /app/constraints.txt

COPY src/ ./src/

EXPOSE 8104

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request,sys;\nurl='http://localhost:8104/healthz';\n\ntry:\n urllib.request.urlopen(url,timeout=3).read();\nexcept Exception:\n sys.exit(1)" || exit 1

CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8104"]
