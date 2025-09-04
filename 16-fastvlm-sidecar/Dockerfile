FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04
# For CPU-only, switch to python:3.11-slim and remove CUDA bits.
RUN apt-get update && apt-get install -y python3-pip && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt
COPY src ./src
ENV FASTVLM_MODEL=apple/fastvlm-2.7b DEVICE=cuda TORCH_DTYPE=float16 MAX_TOKENS=192
EXPOSE 8115
CMD ["uvicorn","src.app:app","--host","0.0.0.0","--port","8115"]
