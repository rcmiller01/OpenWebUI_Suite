ARG BASE_IMAGE=owui/base:py311
FROM ${BASE_IMAGE} as runtime
WORKDIR /app
COPY requirements.txt ./requirements.txt
RUN pip install -r requirements.txt -c /app/constraints.txt
COPY src ./src
EXPOSE 8110
HEALTHCHECK --interval=30s --timeout=7s --start-period=5s --retries=4 \
	CMD python -c "import urllib.request,sys;\nurl='http://localhost:8110/healthz';\n\ntry:\n urllib.request.urlopen(url,timeout=4).read();\nexcept Exception:\n sys.exit(1)" || exit 1
CMD ["uvicorn","src.app:app","--host","0.0.0.0","--port","8110"]
