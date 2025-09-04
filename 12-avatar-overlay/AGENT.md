# 12-Avatar-Overlay Agent

## Overview

The Avatar Overlay provides a lightweight browser-based 2D avatar with real-time lip-sync animation and emotional expressions. It integrates with the Feeling Engine and Drive State services to create dynamic, responsive character animations that synchronize with speech and emotional context.

## Architecture

- **Animation Engine**: Rive 2D runtime for smooth, lightweight animations
- **WebSocket Interface**: Real-time communication with backend services
- **Lip-sync System**: Viseme-based mouth shape animation with precise timing
- **Expression System**: Dynamic facial expressions based on emotional state
- **Performance**: Optimized for 60fps on mobile devices with minimal draw calls
- **Deployment**: Static web application served via Vite development server

## WebSocket Interface

### Connection

```javascript
const ws = new WebSocket('ws://localhost:8080/avatar');
```

### Message Format

The avatar receives real-time updates via WebSocket messages:

```json
{
  "visemes": [
    {"t": 0.12, "v": "AA"},
    {"t": 0.25, "v": "OH"},
    {"t": 0.38, "v": "EE"}
  ],
  "emotion": "warm",
  "drive": {
    "energy": 0.6,
    "focus": 0.8,
    "confidence": 0.7
  }
}
```

### Viseme Format

- **t**: Timestamp in seconds (relative to message time)
- **v**: Viseme phoneme (AA, OH, EE, etc.)

### Emotion States

- `neutral` - Default expression
- `warm` - Friendly, approachable
- `excited` - Energetic, enthusiastic
- `calm` - Relaxed, composed
- `focused` - Attentive, concentrated
- `confused` - Uncertain, puzzled

## File Structure

```
12-avatar-overlay/
├── web/
│   ├── index.html          # Main HTML page
│   ├── app.js             # Main application logic
│   ├── style.css          # CSS styling
│   └── rive/
│       ├── avatar.riv     # Main avatar animation file
│       ├── expressions/   # Expression-specific animations
│       └── visemes/       # Viseme mouth shapes
├── package.json           # Node.js dependencies
├── vite.config.js         # Vite configuration
├── test_avatar.html       # Test interface
├── AGENT.md              # This documentation
└── README.md             # Usage instructions
```

## Dependencies

### Runtime Dependencies

- **@rive-app/canvas**: Rive 2D animation runtime
- **reconnecting-websocket**: Robust WebSocket connection handling

### Development Dependencies

- **vite**: Fast development server and build tool
- **@vitejs/plugin-legacy**: Legacy browser support

## Configuration

### Environment Variables

```javascript
// WebSocket connection settings
const WS_HOST = 'localhost';
const WS_PORT = 8080;
const RECONNECT_INTERVAL = 3000;

// Animation settings
const TARGET_FPS = 60;
const VISUAL_QUALITY = 'high'; // high, medium, low
const ENABLE_DEBUG = false;
```

### Rive Animation States

```javascript
// State machine inputs
const animationInputs = {
  viseme: 'neutral',     // Current mouth shape
  emotion: 'neutral',    // Current emotion
  energy: 0.5,          // Energy level (0-1)
  blink: false,         // Blink trigger
  speaking: false       // Speaking state
};
```

## Performance Optimization

### Draw Call Optimization

- **Batched Rendering**: Combine multiple animation updates
- **LOD System**: Reduce detail at smaller sizes
- **Texture Atlasing**: Minimize texture switches
- **State Caching**: Cache frequently used animation states

### Mobile Optimization

- **Touch Events**: Optimized for touch interactions
- **Battery Awareness**: Reduce animation quality when battery low
- **Memory Management**: Aggressive cleanup of unused assets
- **Network Efficiency**: Compressed WebSocket messages

## Development

### Local Setup

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Rive Animation Setup

```javascript
import { Rive } from '@rive-app/canvas';

// Load avatar animation
const rive = new Rive({
  src: '/rive/avatar.riv',
  canvas: canvas,
  autoplay: true,
  stateMachines: 'AvatarStateMachine'
});

// Set up state machine inputs
const inputs = rive.stateMachineInputs('AvatarStateMachine');
const visemeInput = inputs.find(i => i.name === 'viseme');
const emotionInput = inputs.find(i => i.name === 'emotion');
```

### WebSocket Integration

```javascript
import ReconnectingWebSocket from 'reconnecting-websocket';

const ws = new ReconnectingWebSocket(`ws://${WS_HOST}:${WS_PORT}/avatar`);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  updateAvatar(data);
};

function updateAvatar(data) {
  // Update visemes with timing
  data.visemes.forEach(viseme => {
    setTimeout(() => {
      visemeInput.value = viseme.v;
    }, viseme.t * 1000);
  });

  // Update emotion
  emotionInput.value = data.emotion;

  // Update drive parameters
  energyInput.value = data.drive.energy;
}
```

## Testing

### Automated Tests

```javascript
// Test viseme timing accuracy
function testVisemeTiming() {
  const testVisemes = [
    { t: 0.1, v: 'AA' },
    { t: 0.2, v: 'OH' },
    { t: 0.3, v: 'EE' }
  ];

  const startTime = performance.now();
  playVisemes(testVisemes);

  // Verify timing accuracy
  setTimeout(() => {
    const endTime = performance.now();
    const accuracy = Math.abs((endTime - startTime) - 300) < 10;
    console.assert(accuracy, 'Viseme timing within 10ms');
  }, 350);
}

// Test expression transitions
function testExpressionTransitions() {
  const emotions = ['neutral', 'warm', 'excited', 'calm'];
  emotions.forEach(emotion => {
    setEmotion(emotion);
    // Verify smooth transition
  });
}
```

### Performance Tests

```javascript
// Test 60fps target
function testFrameRate() {
  let frameCount = 0;
  const startTime = performance.now();

  function countFrames() {
    frameCount++;
    if (frameCount < 360) { // 6 seconds at 60fps
      requestAnimationFrame(countFrames);
    } else {
      const duration = (performance.now() - startTime) / 1000;
      const fps = frameCount / duration;
      console.log(`Average FPS: ${fps}`);
      console.assert(fps > 55, 'Maintains 55+ FPS');
    }
  }

  requestAnimationFrame(countFrames);
}
```

## Integration Points

### Feeling Engine Integration

```javascript
// Receive emotional state updates
ws.onmessage = (event) => {
  const feelingData = JSON.parse(event.data);
  updateEmotion(feelingData.emotion);
  updateEnergy(feelingData.intensity);
};
```

### Drive State Integration

```javascript
// Receive drive state updates
function updateDriveState(driveData) {
  // Map drive parameters to animation inputs
  energyInput.value = driveData.energy;
  focusInput.value = driveData.focus;
  confidenceInput.value = driveData.confidence;
}
```

### Pipelines Gateway Integration

```javascript
// Receive speech synthesis timing
function onSpeechSynthesis(audioData, timestamps) {
  // Sync visemes with audio playback
  playVisemesWithAudio(timestamps.visemes, audioData);
}
```

## Browser Compatibility

### Supported Browsers

- Chrome 88+
- Firefox 85+
- Safari 14+
- Edge 88+
- Mobile Safari 14+
- Chrome Android 88+

### Fallback Handling

```javascript
// Detect WebGL support
const hasWebGL = (() => {
  try {
    const canvas = document.createElement('canvas');
    return !!(window.WebGLRenderingContext &&
      canvas.getContext('webgl'));
  } catch (e) {
    return false;
  }
})();

// Fallback to CSS animations if WebGL unavailable
if (!hasWebGL) {
  console.warn('WebGL not available, using CSS fallback');
  useCSSAnimations();
}
```

## Deployment

### Development Server

```javascript
// vite.config.js
export default {
  server: {
    port: 5173,
    host: 'localhost'
  },
  build: {
    target: 'es2015',
    minify: 'terser'
  }
};
```

### Production Build

```javascript
// Optimized production build
npm run build

// Serve static files
npx serve dist -p 5173
```

## Monitoring and Debugging

### Performance Monitoring

```javascript
// Monitor frame rate
let lastTime = 0;
function monitorPerformance() {
  const currentTime = performance.now();
  const deltaTime = currentTime - lastTime;

  if (deltaTime > 16.67) { // > 60fps
    console.warn('Frame drop detected');
  }

  lastTime = currentTime;
  requestAnimationFrame(monitorPerformance);
}
```

### Debug Mode

```javascript
// Enable debug overlays
if (ENABLE_DEBUG) {
  showDebugInfo();
  enablePerformanceLogging();
}

function showDebugInfo() {
  const debugDiv = document.createElement('div');
  debugDiv.id = 'debug-info';
  debugDiv.innerHTML = `
    <div>FPS: <span id="fps">0</span></div>
    <div>Viseme: <span id="current-viseme">neutral</span></div>
    <div>Emotion: <span id="current-emotion">neutral</span></div>
  `;
  document.body.appendChild(debugDiv);
}
```

## Future Enhancements

- **3D Avatar Support**: WebGL-based 3D character rendering
- **Custom Avatar Creation**: User-generated avatar assets
- **Gesture Animation**: Hand and body gesture synchronization
- **Multi-character Scenes**: Support for multiple avatars
- **Voice Cloning Integration**: Personalized voice synthesis
- **AR/VR Support**: WebXR avatar integration
