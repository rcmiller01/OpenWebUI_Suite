FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y bash && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8109

# Health check using Python socket
HEALTHCHECK --interval=60s --timeout=10s --retries=3 \
  CMD python -c "import socket,sys; s=socket.socket(); s.settimeout(3); s.connect(('localhost',8109)); s.close()" || exit 1

# Start the application using start.sh (keeps parity with your repo)
CMD ["bash", "start.sh"]
