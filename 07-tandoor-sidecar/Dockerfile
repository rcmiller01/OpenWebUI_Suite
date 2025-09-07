FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for curl (healthcheck)
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8107

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl -fsS http://localhost:8107/healthz || exit 1

# Start the application
CMD ["python", "start.py"]
