// OpenWebUI Frontend Integration for OpenRouter Gateway
// Add this to your OpenWebUI frontend configuration

// Environment configuration
const OPENROUTER_GATEWAY_URL = process.env.OPENROUTER_GATEWAY_URL || 
    'http://localhost:8000';

// OpenRouter model presets
export const OPENROUTER_PRESETS = [
    {
        id: 'tool-deepseekv3',
        name: 'Tool-DeepSeekV3',
        model: 'deepseek/deepseek-chat',
        description: 'DeepSeek V3 for tool calling and function execution',
        temperature: 0.2,
        capabilities: ['tools', 'function_calling'],
        provider: 'openrouter'
    },
    {
        id: 'vision-glm4v',
        name: 'Vision-GLM4V', 
        model: 'zhipuai/glm-4v-9b',
        description: 'GLM-4V for image analysis and vision tasks',
        temperature: 0.5,
        capabilities: ['vision', 'image_analysis'],
        provider: 'openrouter'
    },
    {
        id: 'venice-uncensored',
        name: 'Venice-Uncensored',
        model: 'venice/uncensored:free',
        description: 'Venice uncensored model for open conversations',
        temperature: 0.8,
        capabilities: ['uncensored', 'creative'],
        provider: 'openrouter'
    },
    {
        id: 'qwen3-coder',
        name: 'Qwen3-Coder',
        model: 'qwen/qwen-2.5-coder-32b-instruct',
        description: 'Qwen 2.5 Coder for programming and development',
        temperature: 0.1,
        capabilities: ['coding', 'programming'],
        provider: 'openrouter'
    }
];

// API client for OpenRouter Gateway
export class OpenRouterGatewayClient {
    constructor(baseUrl = OPENROUTER_GATEWAY_URL) {
        this.baseUrl = baseUrl;
    }

    async chatCompletion(request) {
        const response = await fetch(`${this.baseUrl}/api/v1/chat/completions`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(request)
        });

        if (!response.ok) {
            throw new Error(`Gateway request failed: ${response.status}`);
        }

        return response.json();
    }

    async getModels() {
        const response = await fetch(`${this.baseUrl}/api/v1/models`);
        
        if (!response.ok) {
            throw new Error(`Failed to get models: ${response.status}`);
        }

        return response.json();
    }

    async getHealth() {
        const response = await fetch(`${this.baseUrl}/api/v1/health`);
        
        if (!response.ok) {
            throw new Error(`Health check failed: ${response.status}`);
        }

        return response.json();
    }

    async getRoutingStatus() {
        const response = await fetch(`${this.baseUrl}/api/v1/routing/status`);
        
        if (!response.ok) {
            throw new Error(`Routing status failed: ${response.status}`);
        }

        return response.json();
    }

    async refreshRouting() {
        const response = await fetch(`${this.baseUrl}/api/v1/routing/refresh`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            throw new Error(`Routing refresh failed: ${response.status}`);
        }

        return response.json();
    }
}

// Global client instance
export const gatewayClient = new OpenRouterGatewayClient();

// Model selector integration
export const getOpenRouterModels = async () => {
    try {
        const models = await gatewayClient.getModels();
        
        // Combine with presets for UI display
        const allModels = [
            ...OPENROUTER_PRESETS,
            ...models.openrouter.map(model => ({
                id: model,
                name: model,
                model: model,
                provider: 'openrouter',
                capabilities: []
            })),
            ...models.local_fallback.map(model => ({
                id: `local/${model}`,
                name: `Local: ${model}`,
                model: `local/${model}`,
                provider: 'local_fallback',
                capabilities: ['local', 'offline']
            }))
        ];
        
        return allModels;
    } catch (error) {
        console.error('Failed to load OpenRouter models:', error);
        return OPENROUTER_PRESETS; // Fallback to presets
    }
};

// Chat completion wrapper for OpenWebUI integration
export const sendOpenRouterMessage = async (messages, options = {}) => {
    const request = {
        messages: messages,
        model: options.model,
        temperature: options.temperature || 0.7,
        max_tokens: options.max_tokens || 1200,
        tools: options.tools,
        conversation_id: options.conversation_id,
        stream: options.stream || false
    };

    return gatewayClient.chatCompletion(request);
};

// Health monitoring for UI status indicators
export const checkGatewayHealth = async () => {
    try {
        const health = await gatewayClient.getHealth();
        return {
            status: health.status,
            providers: health.providers,
            routing: health.routing,
            tools: health.tools
        };
    } catch (error) {
        console.error('Gateway health check failed:', error);
        return {
            status: 'unhealthy',
            error: error.message
        };
    }
};

// Routing status for admin interface
export const getRoutingStatus = async () => {
    try {
        return await gatewayClient.getRoutingStatus();
    } catch (error) {
        console.error('Failed to get routing status:', error);
        return { routing_enabled: false, error: error.message };
    }
};

// Utility to get model by preset ID
export const getModelByPreset = (presetId) => {
    return OPENROUTER_PRESETS.find(preset => preset.id === presetId);
};

// Utility to determine if model supports specific capability
export const modelSupportsCapability = (model, capability) => {
    const preset = getModelByPreset(model) || 
        OPENROUTER_PRESETS.find(p => p.model === model);
    
    return preset?.capabilities?.includes(capability) || false;
};
