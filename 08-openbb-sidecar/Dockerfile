ARG BASE_IMAGE=owui/base:py311
FROM ${BASE_IMAGE} as runtime

WORKDIR /app
COPY requirements.txt ./requirements.txt
RUN pip install -r requirements.txt -c /app/constraints.txt
COPY src ./src
EXPOSE 8108
HEALTHCHECK --interval=45s --timeout=8s --start-period=10s --retries=5 \
	CMD python -c "import urllib.request,sys;\nurl='http://localhost:8108/healthz';\n\ntry:\n urllib.request.urlopen(url,timeout=5).read();\nexcept Exception:\n sys.exit(1)" || exit 1
CMD ["uvicorn","src.app:app","--host","0.0.0.0","--port","8108"]
