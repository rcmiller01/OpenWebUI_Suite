# 12-Avatar-Overlay

Real-time 2D avatar overlay with lip-sync animation and emotional expressions for the OpenWebUI Suite.

## Features

- **Real-time Lip-sync**: Precise mouth shape animation synchronized with speech
- **Emotional Expressions**: Dynamic facial expressions based on emotional state
- **WebSocket Integration**: Real-time communication with backend services
- **Rive 2D Animation**: Lightweight, smooth animations optimized for web
- **Mobile Optimized**: Touch-friendly interface with battery awareness
- **Performance Focused**: 60fps target with minimal draw calls
- **Debug Tools**: Built-in testing and performance monitoring

## Quick Start

### Prerequisites
- Node.js 16+
- Modern web browser with WebGL support

### Installation

```bash
# Clone and navigate to the service directory
cd 12-avatar-overlay

# Install dependencies
npm install

# Start development server
npm run dev
```

The avatar overlay will be available at `http://localhost:5173`

### Testing

```bash
# Open test interface
# Visit: http://localhost:5173/test_avatar.html

# Or serve the test file separately
npx serve . -p 8080
# Visit: http://localhost:8080/test_avatar.html
```

## Architecture

### WebSocket Interface

The avatar connects to backend services via WebSocket at `ws://localhost:8080/avatar`:

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

### Animation System

- **Rive Runtime**: Handles 2D animation playback and state management
- **State Machine**: Controls animation transitions and parameter blending
- **Viseme System**: Maps phonemes to mouth shapes with precise timing
- **Expression System**: Blends between emotional states smoothly

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# WebSocket connection
VITE_WS_HOST=localhost
VITE_WS_PORT=8080

# Animation settings
VITE_TARGET_FPS=60
VITE_VISUAL_QUALITY=high
VITE_ENABLE_DEBUG=false
VITE_ENABLE_TEST_CONTROLS=false
```

### Build Configuration

The `vite.config.js` handles:
- Development server on port 5173
- Production build optimization
- Legacy browser support
- Dependency optimization

## Usage

### Basic Integration

```javascript
// Connect to avatar service
const ws = new WebSocket('ws://localhost:8080/avatar');

// Send viseme data
ws.send(JSON.stringify({
  visemes: [
    { t: 0.0, v: 'AA' },
    { t: 0.2, v: 'OH' },
    { t: 0.4, v: 'neutral' }
  ],
  emotion: 'warm',
  drive: { energy: 0.7 }
}));
```

### Integration with OpenWebUI Suite

#### Feeling Engine Integration

```javascript
// Receive emotional state updates
function onFeelingUpdate(feelingData) {
  ws.send(JSON.stringify({
    emotion: feelingData.emotion,
    drive: {
      energy: feelingData.intensity,
      focus: 0.5,
      confidence: 0.5
    }
  }));
}
```

#### Drive State Integration

```javascript
// Receive drive state updates
function onDriveUpdate(driveData) {
  ws.send(JSON.stringify({
    drive: driveData
  }));
}
```

#### STT-TTS Gateway Integration

```javascript
// Receive speech synthesis with timestamps
function onSpeechSynthesis(audioData, visemeData) {
  ws.send(JSON.stringify({
    visemes: visemeData,
    emotion: 'neutral'
  }));
}
```

## Development

### Project Structure

```
12-avatar-overlay/
├── web/
│   ├── index.html          # Main avatar interface
│   ├── app.js             # Core application logic
│   ├── style.css          # Styling and animations
│   └── rive/
│       ├── README.md      # Animation asset documentation
│       └── avatar.riv     # Main animation file (to be created)
├── package.json           # Node.js dependencies
├── vite.config.js         # Build configuration
├── test_avatar.html       # Standalone test interface
├── AGENT.md              # Technical specification
└── README.md             # This file
```

### Creating Rive Animations

1. **Download Rive Editor**: https://rive.app/editor/
2. **Create Avatar Character**: Import or create character artwork
3. **Setup Rigging**: Add bones and morph targets for face
4. **Create Visemes**: Design mouth shapes for phonemes (AA, OH, EE, etc.)
5. **Add Expressions**: Create blend shapes for emotions
6. **State Machine**: Set up animation states and transitions
7. **Export**: Save as `avatar.riv` in the `web/rive/` directory

### Animation Requirements

#### Required State Machine Inputs
- `viseme` (String): Current mouth shape
- `emotion` (String): Current emotional state
- `energy` (Number): Animation intensity (0-1)
- `blink` (Boolean): Eye blink trigger
- `speaking` (Boolean): Speech state indicator

#### Supported Visemes
- `neutral`: Rest position
- `AA`: Open mouth (father, car)
- `OH`: Rounded mouth (go, home)
- `EE`: Wide mouth (see, tree)
- `MM`: Closed mouth (mom, gum)

#### Supported Emotions
- `neutral`: Default expression
- `warm`: Friendly, approachable
- `excited`: Energetic, enthusiastic
- `calm`: Relaxed, composed
- `focused`: Attentive, concentrated
- `confused`: Uncertain, puzzled

## Performance Optimization

### Rendering Optimizations
- **LOD System**: Reduce detail at smaller viewport sizes
- **Texture Atlasing**: Minimize texture switches
- **Batch Rendering**: Combine animation updates
- **Memory Pooling**: Reuse animation objects

### Mobile Considerations
- **Touch Events**: Optimized for touch interactions
- **Battery Awareness**: Reduce quality when battery low
- **Memory Management**: Aggressive cleanup of unused assets
- **Network Efficiency**: Compressed WebSocket messages

### Performance Monitoring

Enable debug mode to monitor:
- Frame rate (target: 60fps)
- Memory usage
- WebSocket latency
- Animation state transitions

## Testing

### Automated Tests

```javascript
// Test viseme timing accuracy
function testVisemeTiming() {
  // Verify visemes play within 10ms of target time
}

// Test expression transitions
function testExpressionTransitions() {
  // Verify smooth blending between emotions
}

// Test performance
function testFrameRate() {
  // Verify 60fps target is maintained
}
```

### Manual Testing

Use the built-in test interface (`test_avatar.html`) to:
- Test individual visemes
- Test emotion transitions
- Test drive state parameters
- Test complex sequences
- Monitor performance metrics

## Browser Support

### Supported Browsers
- Chrome 88+
- Firefox 85+
- Safari 14+
- Edge 88+
- Mobile Safari 14+
- Chrome Android 88+

### Fallback Handling
- **WebGL Unavailable**: Graceful degradation to CSS animations
- **WebSocket Unavailable**: Connection retry with exponential backoff
- **Legacy Browsers**: Polyfills for ES6+ features

## Deployment

### Development
```bash
npm run dev
```

### Production Build
```bash
npm run build
npm run preview
```

### Static Hosting
```bash
# Build for static hosting
npm run build

# Serve built files
npx serve dist -p 5173
```

## Troubleshooting

### Common Issues

1. **WebSocket Connection Failed**
   ```javascript
   // Check if backend service is running
   // Verify WebSocket URL and port
   // Check browser console for errors
   ```

2. **Animation Not Loading**
   ```javascript
   // Verify avatar.riv file exists
   // Check Rive runtime version compatibility
   // Ensure WebGL is enabled in browser
   ```

3. **Performance Issues**
   ```javascript
   // Enable debug mode to monitor FPS
   // Reduce visual quality setting
   // Check for memory leaks
   ```

### Debug Mode

Enable debug features:
```javascript
// In browser console
localStorage.setItem('avatar-debug', 'true');
location.reload();
```

## Contributing

### Code Style
- Use ES6+ features
- Follow standard JavaScript naming conventions
- Add JSDoc comments for functions
- Keep functions small and focused

### Testing
- Add tests for new features
- Test on multiple browsers
- Verify performance impact
- Test with different animation files

## License

This service is part of the OpenWebUI Suite. See project license for details.
