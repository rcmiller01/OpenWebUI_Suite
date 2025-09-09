# OpenRouter Refactor Configuration
# Edit these values to match your setup

# OpenRouter API Configuration
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_REFERER = "https://core3.openwebui.local/"
OPENROUTER_TITLE = "OpenWebUI Homelab"

# Primary Models (Free Tier)
MODEL_TOOLCALL = "deepseek/deepseek-chat"           # DeepSeek V3 tools-capable
MODEL_VISION = "zhipuai/glm-4v-9b"                  # GLM-4V vision model
MODEL_EXPLICIT = "venice/uncensored:free"           # Venice free, no tools
MODEL_CODER = "qwen/qwen-2.5-coder-32b-instruct"   # Qwen coder

# Fallbacks (Paid) - used only after error from free
FALLBACK_TOOLCALL = "deepseek/deepseek-chat"       # Update if OpenRouter splits free/paid
FALLBACK_VISION = "zhipuai/glm-4v-9b"              # Keep same unless paid variant required
FALLBACK_EXPLICIT = "venice/uncensored"            # Paid Venice if present
FALLBACK_CODER = "qwen/qwen-2.5-coder-32b-instruct" # Same slug (OpenRouter handles billing)

# Local Fallback
LOCAL_OFFLINE_BIN = "llama.cpp"                     # Keep llama.cpp (simpler than ollama)
LOCAL_OFFLINE_MODEL = "q4_7b.gguf"                  # Tiny safety fallback only

# Integration Endpoints
N8N_WEBHOOK_URL = "http://192.168.50.145:5678/webhook/openrouter-router"
N8N_SHARED_HEADER = "X-N8N-Key"
N8N_SHARED_SECRET = "SET_THIS"

MCP_ENDPOINT = "http://core3:8765"                  # MCP server endpoint
