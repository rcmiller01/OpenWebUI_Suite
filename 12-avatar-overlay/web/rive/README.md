# Rive Animation Assets

This directory contains the Rive 2D animation files for the avatar overlay.

## Required Files

### avatar.riv
Main avatar animation file containing:
- Character artwork and rigging
- State machine for animation control
- Input parameters for real-time control

### State Machine Inputs
The avatar animation should have the following input parameters:

#### Viseme Control
- **Type**: String/Trigger
- **Name**: `viseme`
- **Values**: `neutral`, `AA`, `OH`, `EE`, `MM`, etc.
- **Purpose**: Controls mouth shape for lip-sync

#### Emotion Control
- **Type**: String
- **Name**: `emotion`
- **Values**: `neutral`, `warm`, `excited`, `calm`, `focused`, `confused`
- **Purpose**: Controls facial expressions

#### Energy Control
- **Type**: Number (0-1)
- **Name**: `energy`
- **Values**: 0.0 to 1.0
- **Purpose**: Controls animation intensity and speed

#### Blink Control
- **Type**: Boolean/Trigger
- **Name**: `blink`
- **Purpose**: Triggers eye blink animation

#### Speaking Control
- **Type**: Boolean
- **Name**: `speaking`
- **Purpose**: Indicates active speech state

## Animation States

### Viseme Shapes
Create morph targets for common phonemes:
- **AA**: Open mouth (father, car)
- **OH**: Rounded mouth (go, home)
- **EE**: Wide smile (see, tree)
- **MM**: Closed mouth (mom, gum)
- **Neutral**: Rest position

### Expression States
Create blend shapes for emotions:
- **Neutral**: Default expression
- **Warm**: Slight smile, raised eyebrows
- **Excited**: Wide smile, raised eyebrows, wide eyes
- **Calm**: Soft smile, relaxed features
- **Focused**: Slight frown, narrowed eyes
- **Confused**: Raised eyebrows, tilted head

## Creating Animations

### Using Rive Editor
1. Create new Rive file
2. Import character artwork
3. Set up bones/rigging for face
4. Create morph targets for visemes
5. Create blend shapes for expressions
6. Set up state machine with inputs
7. Export as `.riv` file

### Best Practices
- Use vector graphics for scalability
- Optimize artwork for web (reduce complexity)
- Test animations at 60fps target
- Ensure smooth transitions between states
- Keep file size under 2MB for web performance

## Directory Structure
```
rive/
├── avatar.riv              # Main animation file
├── expressions/            # Expression-specific animations
│   ├── neutral.riv
│   ├── warm.riv
│   ├── excited.riv
│   └── ...
└── visemes/               # Individual viseme shapes
    ├── AA.riv
    ├── OH.riv
    ├── EE.riv
    └── ...
```

## Performance Optimization
- Minimize number of bones/shapes
- Use texture atlasing
- Avoid complex effects
- Test on target devices
- Profile animation performance

## Testing
Use the built-in test controls to verify:
- Viseme transitions are smooth
- Expression changes are natural
- Energy parameter affects animation intensity
- Performance stays above 55fps

## Integration
The animation file is loaded automatically by `app.js` and controlled via WebSocket messages from the backend services.
