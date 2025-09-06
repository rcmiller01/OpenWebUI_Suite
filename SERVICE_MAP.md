# OpenWebUI Suite — Service Map

## 00-pipelines-gateway
- Path: `/tmp/tmp79lwspxj/OpenWebUI_Suite-main/00-pipelines-gateway`
- Dockerfile: present
- Entrypoints: start.py
- Requirements files: 1
- AGENT.md: yes
- Notable refs (heuristic):
  - B
  - O
  - R
  - http://127.0.0.1:8088
  - http://localhost
  - http://localhost:11434
  - http://localhost:8088/health
  - http://localhost:8088/metrics
  - http://localhost:8088/tasks/dlq
  - http://localhost:8088/tasks/enqueue

## 01-intent-router
- Path: `/tmp/tmp79lwspxj/OpenWebUI_Suite-main/01-intent-router`
- Dockerfile: present
- Entrypoints: start.py
- Requirements files: 1
- AGENT.md: yes
- Notable refs (heuristic):
  - B
  - http://127.0.0.1:8101
  - http://localhost:8101/classify
  - localhost:<port>

## 02-memory-2.0
- Path: `/tmp/tmp79lwspxj/OpenWebUI_Suite-main/02-memory-2.0`
- Entrypoints: start.py
- Requirements files: 1
- AGENT.md: yes
- Notable refs (heuristic):
  - B
  - P
  - V
  - http://localhost:8102
  - http://localhost:8102/mem/candidates
  - http://localhost:8102/mem/retrieve?user_id=user123&intent=hobby&k=4
  - http://localhost:8102/mem/summary?user_id=user123
  - localhost:<port>

## 03-feeling-engine
- Path: `/tmp/tmp79lwspxj/OpenWebUI_Suite-main/03-feeling-engine`
- Entrypoints: start.py
- Requirements files: 1
- AGENT.md: yes
- Notable refs (heuristic):
  - B
  - http://localhost:8103
  - localhost:<port>

## 04-hidden-multi-expert-merger
- Path: `/tmp/tmp79lwspxj/OpenWebUI_Suite-main/04-hidden-multi-expert-merger`
- Entrypoints: start.py
- Requirements files: 1
- AGENT.md: yes
- Notable refs (heuristic):
  - http://127.0.0.1:8104/compose
  - http://127.0.0.1:8104/health
  - http://localhost:8104/compose
  - localhost:<port>

## 05-drive-state
- Path: `/tmp/tmp79lwspxj/OpenWebUI_Suite-main/05-drive-state`
- Entrypoints: start.py
- Requirements files: 1
- AGENT.md: yes
- Notable refs (heuristic):
  - http://127.0.0.1:8105/drive/get?user_id=test_user
  - http://127.0.0.1:8105/drive/policy?user_id=test_user
  - http://127.0.0.1:8105/drive/update?user_id=test_user
  - http://127.0.0.1:8105/health
  - http://localhost:8105/drive/get?user_id=user123
  - http://localhost:8105/drive/policy?user_id=user123
  - http://localhost:8105/drive/update?user_id=user123
  - localhost:<port>

## 06-byof-tool-hub
- Path: `/tmp/tmp79lwspxj/OpenWebUI_Suite-main/06-byof-tool-hub`
- Entrypoints: start.py
- Requirements files: 1
- AGENT.md: yes
- Notable refs (heuristic):
  - 09:<port>
  - 14:<port>
  - https://example.com/result
  - https://github.com/example

## 07-tandoor-sidecar
- Path: `/tmp/tmp79lwspxj/OpenWebUI_Suite-main/07-tandoor-sidecar`
- Entrypoints: start.py
- Requirements files: 1
- AGENT.md: yes
- Notable refs (heuristic):
  - 8107:<port>
  - B
  - T
  - http://127.0.0.1:8107
  - http://localhost:8080
  - http://tandoor:8080
  - https://tandoor.example.com/media/recipe_123.jpg
  - https://your-tandoor-instance.com
  - https://your-tandoor.com
  - localhost:<port>

## 08-openbb-sidecar
- Path: `/tmp/tmp79lwspxj/OpenWebUI_Suite-main/08-openbb-sidecar`
- Dockerfile: present
- Requirements files: 1
- AGENT.md: no

## 09-proactive-daemon
- Path: `/tmp/tmp79lwspxj/OpenWebUI_Suite-main/09-proactive-daemon`
- Entrypoints: start.py
- Requirements files: 1
- AGENT.md: yes
- Notable refs (heuristic):
  - 08:<port>
  - 18:<port>
  - http://127.0.0.1:8088

## 10-multimodal-router
- Path: `/tmp/tmp79lwspxj/OpenWebUI_Suite-main/10-multimodal-router`
- Dockerfile: present
- Requirements files: 1
- AGENT.md: yes
- Notable refs (heuristic):
  - 8110:<port>
  - O
  - S
  - http://localhost
  - http://localhost:8110
  - http://localhost:8110/healthz
  - http://localhost:8110/mm/audio
  - http://localhost:8110/mm/image
  - http://stt-tts:8111/stt
  - https://example.com/image.jpg

## 11-stt-tts-gateway
- Path: `/tmp/tmp79lwspxj/OpenWebUI_Suite-main/11-stt-tts-gateway`
- Dockerfile: present
- Local compose: docker-compose.yml
- Entrypoints: start.py
- Requirements files: 1
- AGENT.md: yes
- Notable refs (heuristic):
  - 8089:<port>
  - A
  - http://localhost:3000
  - http://localhost:8080
  - http://localhost:8089
  - http://localhost:8089/audio/generated_abc123.wav
  - http://localhost:8089/health
  - http://localhost:8089/stt
  - http://localhost:8089/tts
  - localhost:<port>

## 12-avatar-overlay
- Path: `/tmp/tmp79lwspxj/OpenWebUI_Suite-main/12-avatar-overlay`
- Requirements files: 0
- AGENT.md: yes
- Notable refs (heuristic):
  - V
  - W
  - http://localhost:5173
  - http://localhost:5173/test_avatar.html
  - http://localhost:8080/test_avatar.html
  - https://rive.app/editor/
  - localhost:<port>

## 13-policy-guardrails
- Path: `/tmp/tmp79lwspxj/OpenWebUI_Suite-main/13-policy-guardrails`
- Dockerfile: present
- Entrypoints: start.py
- Requirements files: 1
- AGENT.md: yes
- Notable refs (heuristic):
  - http://localhost:8113/policy/apply
  - http://localhost:8113/policy/validate
  - localhost:<port>

## 14-telemetry-cache
- Path: `/tmp/tmp79lwspxj/OpenWebUI_Suite-main/14-telemetry-cache`
- Dockerfile: present
- Local compose: docker-compose.yml
- Entrypoints: start.py
- Requirements files: 1
- AGENT.md: yes
- Notable refs (heuristic):
  - 2025-09-03T10:<port>
  - 2025-09-03T11:<port>
  - 3000:<port>
  - 3100:<port>
  - 6379:<port>
  - 8000:<port>
  - 8114:<port>
  - 9090:<port>
  - 9121:<port>
  - L

## 15-bytebot-gateway
- Path: `/tmp/tmp79lwspxj/OpenWebUI_Suite-main/15-bytebot-gateway`
- Dockerfile: present
- Local compose: docker-compose.yml
- Entrypoints: start.py
- Requirements files: 1
- AGENT.md: yes
- Notable refs (heuristic):
  - 2024-01-01T12:<port>
  - 8089:<port>
  - B
  - bytebot-vm:<port>
  - http://127.0.0.1:8089
  - http://bytebot-vm:8100
  - http://host.docker.internal:3000
  - http://localhost:3000
  - http://localhost:8080
  - http://localhost:8089/capabilities

## 16-fastvlm-sidecar
- Path: `/tmp/tmp79lwspxj/OpenWebUI_Suite-main/16-fastvlm-sidecar`
- Dockerfile: present
- Requirements files: 1
- AGENT.md: yes
- Notable refs (heuristic):
  - 8115:<port>
  - http://localhost:8115
  - http://localhost:8115/analyze
  - http://localhost:8115/healthz
  - https://upload.wikimedia.org/wikipedia/
  - https://upload.wikimedia.org/wikipedia/commons/3/3f/Fronalpstock_big.jpg
  - localhost:<port>

## openwebui-suite
- Path: `/tmp/tmp79lwspxj/OpenWebUI_Suite-main/openwebui-suite`
- Requirements files: 0
- AGENT.md: no
- Notable refs (heuristic):
  - 1000:<port>
  - 2025-09-03T00:<port>
  - 3000:<port>
  - D
  - O
  - W
  - core2-gpu:<port>
  - http://core2-gpu:11434
  - http://localhost:11434
  - http://localhost:3000
