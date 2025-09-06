ARG BASE_IMAGE=owui/base:py311
# To enable CUDA, build with: docker build --build-arg BASE_IMAGE=nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04 .
FROM ${BASE_IMAGE} as builder
WORKDIR /app
COPY requirements.txt ./requirements.txt
# Split model/runtime heavy libs for caching
RUN grep -E '^(torch|transformers|accelerate|Pillow)' requirements.txt > ml.txt || true \
 && grep -Ev '^(torch|transformers|accelerate|Pillow)' requirements.txt > base.txt || true \
 && pip install -r base.txt -c /app/constraints.txt \
 && if [ -s ml.txt ]; then pip install -r ml.txt; fi
COPY src ./src

FROM ${BASE_IMAGE} as runtime
WORKDIR /app
ARG PREFETCH_MODELS="false"
COPY --from=builder /app /app
RUN if [ "$PREFETCH_MODELS" = "true" ]; then \
	python - <<'PY'
import os
from transformers import AutoModelForCausalLM, AutoProcessor
model_id=os.getenv('FASTVLM_MODEL','apple/fastvlm-2.7b')
try:
	AutoProcessor.from_pretrained(model_id)
	AutoModelForCausalLM.from_pretrained(model_id)
	print('Prefetched model', model_id)
except Exception as e:
	print('Prefetch failed', e)
PY
	; fi
ENV FASTVLM_MODEL=apple/fastvlm-2.7b DEVICE=cpu TORCH_DTYPE=float32 MAX_TOKENS=192
EXPOSE 8115
HEALTHCHECK --interval=35s --timeout=8s --start-period=5s --retries=4 \
	CMD python -c "import urllib.request,sys;\nurl='http://localhost:8115/healthz';\n\ntry:\n urllib.request.urlopen(url,timeout=4).read();\nexcept Exception:\n sys.exit(1)" || exit 1
CMD ["uvicorn","src.app:app","--host","0.0.0.0","--port","8115"]
