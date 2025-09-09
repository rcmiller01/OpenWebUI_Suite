# One-liner commands to deploy Memory 2.0 service

## Linux/Docker Host Command (single command):
```bash
curl -sSL https://raw.githubusercontent.com/rcmiller01/OpenWebUI_Suite/main/quick-deploy-memory.sh | bash
```

## Alternative - Manual Steps:
```bash
# Download and extract
cd /tmp
curl -L -o memory-service.zip "https://raw.githubusercontent.com/rcmiller01/OpenWebUI_Suite/main/memory-service.zip"
unzip -o memory-service.zip && cd 02-memory-2.0

# Deploy with Docker
docker build -t owui/memory-2.0:latest .
docker stop memory-service 2>/dev/null || true
docker rm memory-service 2>/dev/null || true
docker run -d --name memory-service --restart unless-stopped -p 8102:8102 owui/memory-2.0:latest

# Test
sleep 10 && curl -f http://localhost:8102/healthz
```

## After Deployment - Test Integration:
```bash
# Run this in your OpenWebUI_Suite directory
python test_openrouter_complete.py
```

## Expected Result:
- Memory service running at http://192.168.50.15:8102
- Integration tests: 7/7 passing (100%)
- OpenRouter refactor: Complete!
