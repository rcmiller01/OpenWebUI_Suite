/**
 * Avatar Overlay Application
 * Real-time 2D avatar with lip-sync and emotional expressions
 */

import { Rive } from '@rive-app/canvas';
import ReconnectingWebSocket from 'reconnecting-websocket';

// Configuration
const CONFIG = {
    WS_HOST: 'localhost',
    WS_PORT: 8080,
    RECONNECT_INTERVAL: 3000,
    TARGET_FPS: 60,
    VISUAL_QUALITY: 'high', // high, medium, low
    ENABLE_DEBUG: false,
    ENABLE_TEST_CONTROLS: false
};

// Global state
let rive = null;
let ws = null;
let animationFrame = null;
let lastFrameTime = 0;
let frameCount = 0;
let fps = 0;

// Animation state machine inputs
let visemeInput = null;
let emotionInput = null;
let energyInput = null;
let blinkInput = null;
let speakingInput = null;

// DOM elements
const canvas = document.getElementById('avatar-canvas');
const debugOverlay = document.getElementById('debug-overlay');
const connectionStatus = document.getElementById('connection-status');
const statusText = document.getElementById('status-text');
const loadingOverlay = document.getElementById('loading-overlay');
const errorOverlay = document.getElementById('error-overlay');
const errorText = document.getElementById('error-text');
const retryButton = document.getElementById('retry-button');

// Debug elements
const debugFps = document.getElementById('debug-fps');
const debugViseme = document.getElementById('debug-viseme');
const debugEmotion = document.getElementById('debug-emotion');
const debugEnergy = document.getElementById('debug-energy');
const debugWs = document.getElementById('debug-ws');
const debugQuality = document.getElementById('debug-quality');

// Test controls
const testControls = document.getElementById('test-controls');

/**
 * Initialize the avatar application
 */
async function init() {
    try {
        showLoading(true);
        setupDebugMode();
        setupTestControls();
        await loadRiveAnimation();
        setupWebSocket();
        setupPerformanceMonitoring();
        setupEventListeners();
        showLoading(false);
    } catch (error) {
        console.error('Failed to initialize avatar:', error);
        showError('Failed to load avatar animation');
    }
}

/**
 * Load Rive animation
 */
async function loadRiveAnimation() {
    try {
        rive = new Rive({
            src: '/rive/avatar.riv',
            canvas: canvas,
            autoplay: true,
            stateMachines: 'AvatarStateMachine',
            onLoad: () => {
                console.log('Rive animation loaded successfully');
                setupStateMachineInputs();
                startRenderLoop();
            },
            onError: (error) => {
                console.error('Rive loading error:', error);
                showError('Failed to load avatar animation file');
            }
        });
    } catch (error) {
        console.error('Failed to create Rive instance:', error);
        throw error;
    }
}

/**
 * Setup state machine inputs
 */
function setupStateMachineInputs() {
    if (!rive) return;

    try {
        const inputs = rive.stateMachineInputs('AvatarStateMachine');

        visemeInput = inputs.find(input => input.name === 'viseme');
        emotionInput = inputs.find(input => input.name === 'emotion');
        energyInput = inputs.find(input => input.name === 'energy');
        blinkInput = inputs.find(input => input.name === 'blink');
        speakingInput = inputs.find(input => input.name === 'speaking');

        console.log('State machine inputs initialized:', {
            viseme: !!visemeInput,
            emotion: !!emotionInput,
            energy: !!energyInput,
            blink: !!blinkInput,
            speaking: !!speakingInput
        });

        // Set default values
        if (visemeInput) visemeInput.value = 'neutral';
        if (emotionInput) emotionInput.value = 'neutral';
        if (energyInput) energyInput.value = 0.5;
        if (blinkInput) blinkInput.value = false;
        if (speakingInput) speakingInput.value = false;

    } catch (error) {
        console.error('Failed to setup state machine inputs:', error);
    }
}

/**
 * Setup WebSocket connection
 */
function setupWebSocket() {
    const wsUrl = `ws://${CONFIG.WS_HOST}:${CONFIG.WS_PORT}/avatar`;

    ws = new ReconnectingWebSocket(wsUrl, [], {
        reconnectionDelayGrowFactor: 1.3,
        minReconnectionDelay: 1000,
        maxReconnectionDelay: 30000,
        maxRetries: 10
    });

    ws.onopen = () => {
        console.log('WebSocket connected');
        updateConnectionStatus('connected', 'Connected');
        updateDebugInfo('ws', 'connected');
    };

    ws.onclose = () => {
        console.log('WebSocket disconnected');
        updateConnectionStatus('disconnected', 'Disconnected');
        updateDebugInfo('ws', 'disconnected');
    };

    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            handleAvatarUpdate(data);
        } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
        }
    };

    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        updateConnectionStatus('error', 'Connection Error');
    };
}

/**
 * Handle avatar update from WebSocket
 */
function handleAvatarUpdate(data) {
    console.log('Received avatar update:', data);

    // Update visemes with timing
    if (data.visemes && Array.isArray(data.visemes)) {
        playVisemes(data.visemes);
    }

    // Update emotion
    if (data.emotion && emotionInput) {
        emotionInput.value = data.emotion;
        updateDebugInfo('emotion', data.emotion);
    }

    // Update drive parameters
    if (data.drive && typeof data.drive === 'object') {
        if (data.drive.energy !== undefined && energyInput) {
            energyInput.value = Math.max(0, Math.min(1, data.drive.energy));
            updateDebugInfo('energy', data.drive.energy.toFixed(2));
        }

        // Handle other drive parameters as needed
        if (data.drive.focus !== undefined) {
            // Could map to additional animation parameters
        }

        if (data.drive.confidence !== undefined) {
            // Could map to additional animation parameters
        }
    }
}

/**
 * Play visemes with timing
 */
function playVisemes(visemes) {
    if (!visemeInput) return;

    visemes.forEach(viseme => {
        const delay = (viseme.t || 0) * 1000; // Convert to milliseconds

        setTimeout(() => {
            if (visemeInput) {
                visemeInput.value = viseme.v || 'neutral';
                updateDebugInfo('viseme', viseme.v || 'neutral');

                // Trigger speaking state
                if (speakingInput) {
                    speakingInput.value = true;
                    // Reset speaking state after viseme duration
                    setTimeout(() => {
                        if (speakingInput) speakingInput.value = false;
                    }, 100); // Brief speaking pulse
                }
            }
        }, delay);
    });
}

/**
 * Start render loop for performance monitoring
 */
function startRenderLoop() {
    function render(currentTime) {
        // Calculate FPS
        frameCount++;
        if (currentTime - lastFrameTime >= 1000) {
            fps = Math.round((frameCount * 1000) / (currentTime - lastFrameTime));
            frameCount = 0;
            lastFrameTime = currentTime;

            updateDebugInfo('fps', fps.toString());
        }

        // Continue render loop
        animationFrame = requestAnimationFrame(render);
    }

    lastFrameTime = performance.now();
    animationFrame = requestAnimationFrame(render);
}

/**
 * Setup performance monitoring
 */
function setupPerformanceMonitoring() {
    // Monitor for frame drops
    let lastFrameTime = 0;
    const frameThreshold = 1000 / CONFIG.TARGET_FPS; // ~16.67ms for 60fps

    function monitorPerformance(currentTime) {
        const deltaTime = currentTime - lastFrameTime;

        if (deltaTime > frameThreshold * 1.5) { // 50% over target
            console.warn(`Frame drop detected: ${deltaTime.toFixed(2)}ms`);
        }

        lastFrameTime = currentTime;
        requestAnimationFrame(monitorPerformance);
    }

    requestAnimationFrame(monitorPerformance);
}

/**
 * Setup debug mode
 */
function setupDebugMode() {
    if (CONFIG.ENABLE_DEBUG) {
        debugOverlay.classList.remove('debug-hidden');
        updateDebugInfo('quality', CONFIG.VISUAL_QUALITY);
    }
}

/**
 * Setup test controls
 */
function setupTestControls() {
    if (!CONFIG.ENABLE_TEST_CONTROLS) return;

    testControls.classList.remove('test-hidden');

    // Viseme test buttons
    document.getElementById('test-viseme-aa')?.addEventListener('click', () => {
        if (visemeInput) visemeInput.value = 'AA';
        updateDebugInfo('viseme', 'AA');
    });

    document.getElementById('test-viseme-oh')?.addEventListener('click', () => {
        if (visemeInput) visemeInput.value = 'OH';
        updateDebugInfo('viseme', 'OH');
    });

    document.getElementById('test-viseme-ee')?.addEventListener('click', () => {
        if (visemeInput) visemeInput.value = 'EE';
        updateDebugInfo('viseme', 'EE');
    });

    document.getElementById('test-viseme-neutral')?.addEventListener('click', () => {
        if (visemeInput) visemeInput.value = 'neutral';
        updateDebugInfo('viseme', 'neutral');
    });

    // Emotion test buttons
    document.getElementById('test-emotion-neutral')?.addEventListener('click', () => {
        if (emotionInput) emotionInput.value = 'neutral';
        updateDebugInfo('emotion', 'neutral');
    });

    document.getElementById('test-emotion-warm')?.addEventListener('click', () => {
        if (emotionInput) emotionInput.value = 'warm';
        updateDebugInfo('emotion', 'warm');
    });

    document.getElementById('test-emotion-excited')?.addEventListener('click', () => {
        if (emotionInput) emotionInput.value = 'excited';
        updateDebugInfo('emotion', 'excited');
    });

    document.getElementById('test-emotion-calm')?.addEventListener('click', () => {
        if (emotionInput) emotionInput.value = 'calm';
        updateDebugInfo('emotion', 'calm');
    });

    document.getElementById('test-emotion-focused')?.addEventListener('click', () => {
        if (emotionInput) emotionInput.value = 'focused';
        updateDebugInfo('emotion', 'focused');
    });

    // Energy slider
    const energySlider = document.getElementById('test-energy-slider');
    const energyValue = document.getElementById('test-energy-value');

    energySlider?.addEventListener('input', (e) => {
        const value = parseFloat(e.target.value);
        if (energyInput) energyInput.value = value;
        energyValue.textContent = value.toFixed(1);
        updateDebugInfo('energy', value.toFixed(2));
    });

    // Sequence test
    document.getElementById('test-sequence')?.addEventListener('click', () => {
        playTestSequence();
    });

    document.getElementById('test-stop')?.addEventListener('click', () => {
        stopTestSequence();
    });
}

/**
 * Play test sequence
 */
function playTestSequence() {
    const sequence = [
        { t: 0.0, v: 'neutral' },
        { t: 0.5, v: 'AA' },
        { t: 1.0, v: 'OH' },
        { t: 1.5, v: 'EE' },
        { t: 2.0, v: 'AA' },
        { t: 2.5, v: 'neutral' }
    ];

    playVisemes(sequence);

    // Also cycle through emotions
    const emotions = ['neutral', 'warm', 'excited', 'calm', 'focused'];
    emotions.forEach((emotion, index) => {
        setTimeout(() => {
            if (emotionInput) {
                emotionInput.value = emotion;
                updateDebugInfo('emotion', emotion);
            }
        }, index * 500);
    });
}

/**
 * Stop test sequence
 */
function stopTestSequence() {
    if (visemeInput) visemeInput.value = 'neutral';
    if (emotionInput) emotionInput.value = 'neutral';
    if (energyInput) energyInput.value = 0.5;

    updateDebugInfo('viseme', 'neutral');
    updateDebugInfo('emotion', 'neutral');
    updateDebugInfo('energy', '0.50');
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
    // Retry button
    retryButton.addEventListener('click', () => {
        showError(null);
        init();
    });

    // Handle page visibility changes
    document.addEventListener('visibilitychange', () => {
        if (document.hidden) {
            // Pause animations when page is hidden
            if (rive) rive.pause();
        } else {
            // Resume animations when page is visible
            if (rive) rive.play();
        }
    });

    // Handle window resize
    window.addEventListener('resize', () => {
        // Rive handles canvas resizing automatically
        console.log('Window resized, canvas should adapt');
    });
}

/**
 * Update connection status
 */
function updateConnectionStatus(status, text) {
    connectionStatus.className = `status-${status}`;
    statusText.textContent = text;
}

/**
 * Update debug information
 */
function updateDebugInfo(key, value) {
    const element = document.getElementById(`debug-${key}`);
    if (element) {
        element.textContent = value;
    }
}

/**
 * Show loading overlay
 */
function showLoading(show) {
    if (show) {
        loadingOverlay.classList.remove('loading-hidden');
    } else {
        loadingOverlay.classList.add('loading-hidden');
    }
}

/**
 * Show error overlay
 */
function showError(message) {
    if (message) {
        errorText.textContent = message;
        errorOverlay.classList.remove('error-hidden');
    } else {
        errorOverlay.classList.add('error-hidden');
    }
}

/**
 * Cleanup function
 */
function cleanup() {
    if (animationFrame) {
        cancelAnimationFrame(animationFrame);
    }

    if (ws) {
        ws.close();
    }

    if (rive) {
        rive.cleanup();
    }
}

// Handle page unload
window.addEventListener('beforeunload', cleanup);

// Initialize application when DOM is ready
document.addEventListener('DOMContentLoaded', init);

// Export for debugging
window.avatarApp = {
    rive,
    ws,
    playVisemes,
    updateDebugInfo,
    cleanup
};
