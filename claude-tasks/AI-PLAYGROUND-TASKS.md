# AI-Playground Project Tasks

This file contains all task specifications for building the AI-playground monorepo with PixiJS and 2D SDF rendering.

---

## TASK MANIFEST

| Task | Branch | Dependencies | Status |
|------|--------|--------------|--------|
| 0 | Manual Setup | None | Complete |
| 1 | feature/monorepo-foundation | Task 0 | Complete |
| 2 | feature/github-actions-workflow | Task 1 | Complete |
| 3 | feature/sdf-core-library | Task 1 | Not Started |
| 4 | feature/input-system | Task 1 | Not Started |
| 5 | feature/pixi-ui-toggle | Task 3 | Not Started |
| 6 | feature/sdf-playground-prototype | Task 3, 4, 5 | Not Started |
| 7 | feature/launcher-page | Task 6 | Not Started |

---

# TASK 0: Manual Repository Setup

## Type
Manual - User Action Required

## Instructions for User

1. Create new repository on GitHub named "AI-playground"
2. Go to repository Settings → Pages
3. Under "Build and deployment" → Source: select "GitHub Actions"
4. Clone repository to your device
5. Mark this task as complete in manifest

## Verification
- Repository exists on GitHub
- GitHub Pages is enabled with Actions source
- Repository is cloned locally

---

# TASK 1: Monorepo Foundation

## Branch
`feature/monorepo-foundation`

## Objective
Set up the monorepo structure with npm workspaces and Vite build configuration.

## Files to Create

### `package.json` (root)
```json
{
  "name": "ai-playground",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "workspaces": [
    "packages/*",
    "prototypes/*",
    "launcher"
  ],
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "devDependencies": {
    "vite": "^5.0.0"
  }
}
```

### `.gitignore`
```
node_modules/
dist/
.DS_Store
*.log
.vite/
```

### `vite.config.js`
```javascript
import { defineConfig } from 'vite';
import { resolve } from 'path';

export default defineConfig({
  build: {
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'launcher/index.html'),
        'sdf-playground': resolve(__dirname, 'prototypes/sdf-playground/index.html'),
      },
    },
  },
  base: '/AI-playground/',
  server: {
    host: '0.0.0.0',
    port: 5173,
  },
});
```

### `README.md`
```markdown
# AI-Playground

A monorepo for prototyping games and interactive experiences using PixiJS and 2D SDF shaders.

## Development

```bash
npm install
npm run dev
```

## Build

Comment `/build` on any PR to trigger a build and deployment.

## Local Testing (Termux)

```bash
npm install
npm run dev
```

Then visit `http://localhost:5173` in your browser.
```

### Directory Structure
Create these empty directories:
- `packages/sdf-core/`
- `packages/input-system/`
- `prototypes/sdf-playground/`
- `launcher/`

### `packages/sdf-core/package.json`
```json
{
  "name": "@ai-playground/sdf-core",
  "version": "1.0.0",
  "type": "module",
  "main": "src/index.js"
}
```

### `packages/input-system/package.json`
```json
{
  "name": "@ai-playground/input-system",
  "version": "1.0.0",
  "type": "module",
  "main": "src/index.js"
}
```

### `prototypes/sdf-playground/package.json`
```json
{
  "name": "sdf-playground",
  "version": "1.0.0",
  "type": "module",
  "dependencies": {
    "@ai-playground/sdf-core": "*",
    "@ai-playground/input-system": "*",
    "pixi.js": "^8.0.0"
  }
}
```

## Git Operations
```bash
git checkout -b feature/monorepo-foundation
git add .
git commit -m "feat: monorepo foundation with npm workspaces"
git push -u origin feature/monorepo-foundation
```

Then create PR with title: "Task 1: Monorepo Foundation"

## Verification
- Run `npm install` - should complete without errors
- Check that workspaces are linked
- PR is created on GitHub
- Comment `/build` on PR to verify workflow (will fail until Task 2)

---

# TASK 2: GitHub Actions Workflow

## Branch
`feature/github-actions-workflow`

## Objective
Create GitHub Actions workflow that builds and deploys on `/build` PR comment.

## Files to Create

### `.github/workflows/build-deploy.yml`
```yaml
name: Build and Deploy

on:
  issue_comment:
    types: [created]

jobs:
  build-deploy:
    if: github.event.issue.pull_request && contains(github.event.comment.body, '/build')
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pull-requests: write
      pages: write
      id-token: write

    steps:
      - name: Get PR branch
        uses: actions/github-script@v7
        id: get-branch
        with:
          script: |
            const pr = await github.rest.pulls.get({
              owner: context.repo.owner,
              repo: context.repo.repo,
              pull_number: context.issue.number
            });
            return pr.data.head.ref;
          result-encoding: string

      - name: Checkout PR branch
        uses: actions/checkout@v4
        with:
          ref: ${{ steps.get-branch.outputs.result }}

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Build
        run: npm run build

      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: ./dist

      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4

      - name: Comment on PR
        uses: actions/github-script@v7
        with:
          script: |
            github.rest.issues.createComment({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.issue.number,
              body: '✅ Build complete! Preview: https://${{ github.repository_owner }}.github.io/AI-playground/'
            });
```

## Git Operations
```bash
git checkout -b feature/github-actions-workflow
git add .github/
git commit -m "feat: GitHub Actions build on /build command"
git push -u origin feature/github-actions-workflow
```

Then create PR with title: "Task 2: GitHub Actions Workflow"

## Verification
- After PR is created, comment `/build` on it
- Check Actions tab for workflow run
- Verify deployment completes
- Check that PR gets a comment with the preview URL

---

# TASK 3: SDF Core Library

## Branch
`feature/sdf-core-library`

## Objective
Build the SDF shader system with composable JS API for 2D signed distance fields.

## Files to Create

### `packages/sdf-core/shaders/sdf.frag`
```glsl
precision mediump float;

varying vec2 vTextureCoord;
uniform vec2 uResolution;
uniform float uTime;

// SDF primitives
float sdCircle(vec2 p, float r) {
    return length(p) - r;
}

float sdBox(vec2 p, vec2 b) {
    vec2 d = abs(p) - b;
    return length(max(d, 0.0)) + min(max(d.x, d.y), 0.0);
}

// SDF operations
float opUnion(float d1, float d2) {
    return min(d1, d2);
}

float opSubtraction(float d1, float d2) {
    return max(-d1, d2);
}

float opIntersection(float d1, float d2) {
    return max(d1, d2);
}

// Uniforms for shapes
uniform vec2 uShape1Pos;
uniform float uShape1Radius;
uniform vec2 uShape2Pos;
uniform float uShape2Radius;
uniform int uOperation; // 0=union, 1=subtract, 2=intersect
uniform int uVisualizationMode; // 0=solid, 1=distance field

void main() {
    vec2 uv = (gl_FragCoord.xy - 0.5 * uResolution.xy) / uResolution.y;

    float d1 = sdCircle(uv - uShape1Pos, uShape1Radius);
    float d2 = sdCircle(uv - uShape2Pos, uShape2Radius);

    float d;
    if (uOperation == 0) {
        d = opUnion(d1, d2);
    } else if (uOperation == 1) {
        d = opSubtraction(d1, d2);
    } else {
        d = opIntersection(d1, d2);
    }

    vec3 color;
    if (uVisualizationMode == 0) {
        // Solid fill
        color = d < 0.0 ? vec3(0.2, 0.6, 1.0) : vec3(0.1, 0.1, 0.1);
    } else {
        // Distance field visualization
        color = vec3(1.0 - exp(-abs(d) * 3.0));
        if (d < 0.0) color *= vec3(0.2, 0.6, 1.0);
    }

    gl_FragColor = vec4(color, 1.0);
}
```

### `packages/sdf-core/shaders/sdf.vert`
```glsl
attribute vec2 aVertexPosition;
varying vec2 vTextureCoord;

void main() {
    gl_Position = vec4(aVertexPosition, 0.0, 1.0);
    vTextureCoord = aVertexPosition * 0.5 + 0.5;
}
```

### `packages/sdf-core/src/SDFScene.js`
```javascript
import * as PIXI from 'pixi.js';

const vertShaderSource = `
attribute vec2 aVertexPosition;
varying vec2 vTextureCoord;

void main() {
    gl_Position = vec4(aVertexPosition, 0.0, 1.0);
    vTextureCoord = aVertexPosition * 0.5 + 0.5;
}
`;

const fragShaderSource = `
precision mediump float;

varying vec2 vTextureCoord;
uniform vec2 uResolution;
uniform float uTime;

// SDF primitives
float sdCircle(vec2 p, float r) {
    return length(p) - r;
}

float sdBox(vec2 p, vec2 b) {
    vec2 d = abs(p) - b;
    return length(max(d, 0.0)) + min(max(d.x, d.y), 0.0);
}

// SDF operations
float opUnion(float d1, float d2) {
    return min(d1, d2);
}

float opSubtraction(float d1, float d2) {
    return max(-d1, d2);
}

float opIntersection(float d1, float d2) {
    return max(d1, d2);
}

// Uniforms for shapes
uniform vec2 uShape1Pos;
uniform float uShape1Radius;
uniform vec2 uShape2Pos;
uniform float uShape2Radius;
uniform int uOperation;
uniform int uVisualizationMode;

void main() {
    vec2 uv = (gl_FragCoord.xy - 0.5 * uResolution.xy) / uResolution.y;

    float d1 = sdCircle(uv - uShape1Pos, uShape1Radius);
    float d2 = sdCircle(uv - uShape2Pos, uShape2Radius);

    float d;
    if (uOperation == 0) {
        d = opUnion(d1, d2);
    } else if (uOperation == 1) {
        d = opSubtraction(d1, d2);
    } else {
        d = opIntersection(d1, d2);
    }

    vec3 color;
    if (uVisualizationMode == 0) {
        color = d < 0.0 ? vec3(0.2, 0.6, 1.0) : vec3(0.1, 0.1, 0.1);
    } else {
        color = vec3(1.0 - exp(-abs(d) * 3.0));
        if (d < 0.0) color *= vec3(0.2, 0.6, 1.0);
    }

    gl_FragColor = vec4(color, 1.0);
}
`;

export class SDFScene {
    constructor(app) {
        this.app = app;
        this.shapes = [];
        this.operation = 0; // 0=union, 1=subtract, 2=intersect
        this.visualizationMode = 0; // 0=solid, 1=distance

        this.initShader();
    }

    initShader() {
        const geometry = new PIXI.Geometry()
            .addAttribute('aVertexPosition', [-1, -1, 1, -1, 1, 1, -1, -1, 1, 1, -1, 1], 2);

        const shader = PIXI.Shader.from(vertShaderSource, fragShaderSource, {
            uResolution: [this.app.screen.width, this.app.screen.height],
            uTime: 0,
            uShape1Pos: [0, 0],
            uShape1Radius: 0.2,
            uShape2Pos: [0.3, 0],
            uShape2Radius: 0.2,
            uOperation: 0,
            uVisualizationMode: 0,
        });

        this.mesh = new PIXI.Mesh(geometry, shader);
        this.app.stage.addChild(this.mesh);

        // Handle resize
        this.app.renderer.on('resize', (width, height) => {
            this.mesh.shader.uniforms.uResolution = [width, height];
        });
    }

    circle(x, y, radius) {
        const shape = { type: 'circle', x, y, radius, id: this.shapes.length };
        this.shapes.push(shape);
        this.updateUniforms();
        return shape;
    }

    updateShape(shape, props) {
        Object.assign(shape, props);
        this.updateUniforms();
    }

    setOperation(op) {
        this.operation = op;
        this.mesh.shader.uniforms.uOperation = op;
    }

    setVisualizationMode(mode) {
        this.visualizationMode = mode;
        this.mesh.shader.uniforms.uVisualizationMode = mode;
    }

    updateUniforms() {
        if (this.shapes[0]) {
            this.mesh.shader.uniforms.uShape1Pos = [this.shapes[0].x, this.shapes[0].y];
            this.mesh.shader.uniforms.uShape1Radius = this.shapes[0].radius;
        }
        if (this.shapes[1]) {
            this.mesh.shader.uniforms.uShape2Pos = [this.shapes[1].x, this.shapes[1].y];
            this.mesh.shader.uniforms.uShape2Radius = this.shapes[1].radius;
        }
    }
}
```

### `packages/sdf-core/src/index.js`
```javascript
export { SDFScene } from './SDFScene.js';
```

## Git Operations
```bash
git checkout -b feature/sdf-core-library
git add packages/sdf-core/
git commit -m "feat: SDF core library with shader system"
git push -u origin feature/sdf-core-library
```

Then create PR with title: "Task 3: SDF Core Library"

## Verification
- Files are created in correct structure
- Shader syntax is valid GLSL
- PR is created
- Comment `/build` to verify it builds without errors

---

# TASK 4: Input System

## Branch
`feature/input-system`

## Objective
Create a reusable touch and mouse drag handling system.

## Files to Create

### `packages/input-system/src/DragController.js`
```javascript
export class DragController {
    constructor(app) {
        this.app = app;
        this.draggables = [];
        this.draggedObject = null;
        this.dragOffset = { x: 0, y: 0 };

        this.initEventListeners();
    }

    initEventListeners() {
        this.app.stage.eventMode = 'static';
        this.app.stage.hitArea = this.app.screen;

        this.app.stage.on('pointerdown', this.onPointerDown.bind(this));
        this.app.stage.on('pointermove', this.onPointerMove.bind(this));
        this.app.stage.on('pointerup', this.onPointerUp.bind(this));
        this.app.stage.on('pointerupoutside', this.onPointerUp.bind(this));
    }

    register(object, options = {}) {
        const draggable = {
            object,
            onDragStart: options.onDragStart || (() => {}),
            onDrag: options.onDrag || (() => {}),
            onDragEnd: options.onDragEnd || (() => {}),
            hitTest: options.hitTest || this.defaultHitTest.bind(this),
        };

        this.draggables.push(draggable);
        return draggable;
    }

    unregister(object) {
        this.draggables = this.draggables.filter(d => d.object !== object);
    }

    defaultHitTest(object, position) {
        const dx = position.x - object.x;
        const dy = position.y - object.y;
        const distance = Math.sqrt(dx * dx + dy * dy);
        return distance < (object.radius || 50);
    }

    screenToWorld(screenX, screenY) {
        // Convert screen coordinates to normalized world space (-1 to 1)
        const x = (screenX / this.app.screen.width) * 2 - 1;
        const y = -((screenY / this.app.screen.height) * 2 - 1);

        // Convert to shader coordinate space (aspect ratio corrected)
        const aspect = this.app.screen.width / this.app.screen.height;
        return {
            x: x * aspect * 0.5,
            y: y * 0.5
        };
    }

    onPointerDown(event) {
        const worldPos = this.screenToWorld(event.global.x, event.global.y);

        // Find the topmost draggable object under the pointer
        for (let i = this.draggables.length - 1; i >= 0; i--) {
            const draggable = this.draggables[i];
            if (draggable.hitTest(draggable.object, worldPos)) {
                this.draggedObject = draggable;
                this.dragOffset = {
                    x: draggable.object.x - worldPos.x,
                    y: draggable.object.y - worldPos.y
                };
                draggable.onDragStart(draggable.object, worldPos);
                break;
            }
        }
    }

    onPointerMove(event) {
        if (this.draggedObject) {
            const worldPos = this.screenToWorld(event.global.x, event.global.y);
            const newPos = {
                x: worldPos.x + this.dragOffset.x,
                y: worldPos.y + this.dragOffset.y
            };

            this.draggedObject.onDrag(this.draggedObject.object, newPos);
        }
    }

    onPointerUp(event) {
        if (this.draggedObject) {
            const worldPos = this.screenToWorld(event.global.x, event.global.y);
            this.draggedObject.onDragEnd(this.draggedObject.object, worldPos);
            this.draggedObject = null;
        }
    }
}
```

### `packages/input-system/src/index.js`
```javascript
export { DragController } from './DragController.js';
```

## Git Operations
```bash
git checkout -b feature/input-system
git add packages/input-system/
git commit -m "feat: drag controller for touch and mouse input"
git push -u origin feature/input-system
```

Then create PR with title: "Task 4: Input System"

## Verification
- Files created correctly
- PR is created
- Comment `/build` to verify it builds

---

# TASK 5: PixiJS UI Components

## Branch
`feature/pixi-ui-toggle`

## Objective
Create PixiJS-based UI components for operation and visualization toggles.

## Files to Create

### `packages/sdf-core/src/UIButton.js`
```javascript
import * as PIXI from 'pixi.js';

export class UIButton extends PIXI.Container {
    constructor(text, x, y, width, height) {
        super();

        this.x = x;
        this.y = y;
        this.width = width;
        this.height = height;
        this.isPressed = false;

        // Background
        this.bg = new PIXI.Graphics();
        this.updateBackground(0x333333);
        this.addChild(this.bg);

        // Text
        this.label = new PIXI.Text(text, {
            fontSize: 16,
            fill: 0xffffff,
            align: 'center'
        });
        this.label.anchor.set(0.5);
        this.label.x = width / 2;
        this.label.y = height / 2;
        this.addChild(this.label);

        // Make interactive
        this.eventMode = 'static';
        this.cursor = 'pointer';

        this.on('pointerdown', this.onPress.bind(this));
        this.on('pointerup', this.onRelease.bind(this));
        this.on('pointerupoutside', this.onRelease.bind(this));
    }

    updateBackground(color) {
        this.bg.clear();
        this.bg.beginFill(color);
        this.bg.drawRoundedRect(0, 0, this.width, this.height, 5);
        this.bg.endFill();
    }

    onPress() {
        this.isPressed = true;
        this.updateBackground(0x555555);
    }

    onRelease() {
        if (this.isPressed) {
            this.updateBackground(0x333333);
            this.emit('click');
        }
        this.isPressed = false;
    }

    setText(text) {
        this.label.text = text;
    }
}
```

### `packages/sdf-core/src/UIToggle.js`
```javascript
import * as PIXI from 'pixi.js';
import { UIButton } from './UIButton.js';

export class UIToggle extends PIXI.Container {
    constructor(label, options, x, y) {
        super();

        this.x = x;
        this.y = y;
        this.options = options;
        this.currentIndex = 0;
        this.buttons = [];

        // Label
        const labelText = new PIXI.Text(label, {
            fontSize: 14,
            fill: 0xffffff
        });
        labelText.y = -25;
        this.addChild(labelText);

        // Create buttons
        const buttonWidth = 100;
        const buttonHeight = 30;
        const spacing = 5;

        options.forEach((option, index) => {
            const button = new UIButton(
                option,
                index * (buttonWidth + spacing),
                0,
                buttonWidth,
                buttonHeight
            );

            button.on('click', () => this.selectOption(index));
            this.buttons.push(button);
            this.addChild(button);
        });

        this.selectOption(0);
    }

    selectOption(index) {
        this.currentIndex = index;

        // Update button appearances
        this.buttons.forEach((button, i) => {
            if (i === index) {
                button.updateBackground(0x4444ff);
            } else {
                button.updateBackground(0x333333);
            }
        });

        this.emit('change', index, this.options[index]);
    }

    getValue() {
        return this.currentIndex;
    }
}
```

### Update `packages/sdf-core/src/index.js`
```javascript
export { SDFScene } from './SDFScene.js';
export { UIButton } from './UIButton.js';
export { UIToggle } from './UIToggle.js';
```

## Git Operations
```bash
git checkout -b feature/pixi-ui-toggle
git add packages/sdf-core/src/
git commit -m "feat: PixiJS UI components for toggles and buttons"
git push -u origin feature/pixi-ui-toggle
```

Then create PR with title: "Task 5: PixiJS UI Components"

## Verification
- UI components created
- PR is created
- Comment `/build` to verify

---

# TASK 6: SDF Playground Prototype

## Branch
`feature/sdf-playground-prototype`

## Objective
Create the actual interactive demo with draggable circles and SDF operations.

## Files to Create

### `prototypes/sdf-playground/index.html`
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SDF Playground</title>
    <style>
        body {
            margin: 0;
            padding: 0;
            overflow: hidden;
            background: #000;
            font-family: Arial, sans-serif;
        }
        #app {
            width: 100vw;
            height: 100vh;
        }
    </style>
</head>
<body>
    <div id="app"></div>
    <script type="module" src="/prototypes/sdf-playground/src/main.js"></script>
</body>
</html>
```

### `prototypes/sdf-playground/src/main.js`
```javascript
import * as PIXI from 'pixi.js';
import { SDFScene, UIToggle } from '@ai-playground/sdf-core';
import { DragController } from '@ai-playground/input-system';

// Create PixiJS application
const app = new PIXI.Application();

async function init() {
    await app.init({
        resizeTo: window,
        backgroundColor: 0x000000,
        antialias: true,
    });

    document.getElementById('app').appendChild(app.canvas);

    // Create SDF scene
    const sdfScene = new SDFScene(app);

    // Create two circles
    const circle1 = sdfScene.circle(-0.2, 0, 0.15);
    const circle2 = sdfScene.circle(0.2, 0, 0.15);

    // Setup drag controller
    const dragController = new DragController(app);

    dragController.register(circle1, {
        onDrag: (obj, pos) => {
            sdfScene.updateShape(obj, { x: pos.x, y: pos.y });
        }
    });

    dragController.register(circle2, {
        onDrag: (obj, pos) => {
            sdfScene.updateShape(obj, { x: pos.x, y: pos.y });
        }
    });

    // Create UI
    const operationToggle = new UIToggle(
        'Operation',
        ['Union', 'Subtract', 'Intersect'],
        20,
        20
    );

    operationToggle.on('change', (index) => {
        sdfScene.setOperation(index);
    });

    app.stage.addChild(operationToggle);

    const vizToggle = new UIToggle(
        'Visualization',
        ['Solid', 'Distance Field'],
        20,
        100
    );

    vizToggle.on('change', (index) => {
        sdfScene.setVisualizationMode(index);
    });

    app.stage.addChild(vizToggle);

    // Instructions
    const instructions = new PIXI.Text(
        'Drag the circles to see SDF operations in action!',
        {
            fontSize: 14,
            fill: 0xffffff,
            align: 'center'
        }
    );
    instructions.anchor.set(0.5, 1);
    instructions.x = app.screen.width / 2;
    instructions.y = app.screen.height - 20;
    app.stage.addChild(instructions);

    // Handle resize
    app.renderer.on('resize', () => {
        instructions.x = app.screen.width / 2;
        instructions.y = app.screen.height - 20;
    });
}

init();
```

## Git Operations
```bash
git checkout -b feature/sdf-playground-prototype
git add prototypes/sdf-playground/
git commit -m "feat: SDF playground prototype with draggable circles"
git push -u origin feature/sdf-playground-prototype
```

Then create PR with title: "Task 6: SDF Playground Prototype"

## Verification
- Comment `/build` on PR
- Visit deployed URL
- Test dragging circles
- Test operation toggles
- Test visualization toggle

---

# TASK 7: Launcher Page

## Branch
`feature/launcher-page`

## Objective
Create an index/launcher page that links to all prototypes.

## Files to Create

### `launcher/index.html`
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Playground</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }

        .container {
            max-width: 800px;
            width: 100%;
        }

        h1 {
            color: white;
            font-size: 3rem;
            margin-bottom: 1rem;
            text-align: center;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }

        .subtitle {
            color: rgba(255,255,255,0.9);
            text-align: center;
            margin-bottom: 3rem;
            font-size: 1.2rem;
        }

        .prototypes {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
        }

        .prototype-card {
            background: white;
            border-radius: 10px;
            padding: 30px;
            text-decoration: none;
            color: #333;
            transition: transform 0.3s, box-shadow 0.3s;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }

        .prototype-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 20px rgba(0,0,0,0.2);
        }

        .prototype-card h2 {
            color: #667eea;
            margin-bottom: 10px;
            font-size: 1.5rem;
        }

        .prototype-card p {
            color: #666;
            line-height: 1.6;
        }

        .status {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            margin-top: 10px;
            background: #4CAF50;
            color: white;
        }

        .status.coming-soon {
            background: #FF9800;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>AI Playground</h1>
        <p class="subtitle">Interactive prototypes built with PixiJS and 2D SDF shaders</p>

        <div class="prototypes">
            <a href="sdf-playground/" class="prototype-card">
                <h2>SDF Playground</h2>
                <p>Explore 2D signed distance fields with interactive circles and boolean operations.</p>
                <span class="status">Live</span>
            </a>

            <a href="#" class="prototype-card" style="opacity: 0.6; cursor: not-allowed;">
                <h2>Match-3 Game</h2>
                <p>Classic match-3 puzzle mechanics with SDF-rendered gems.</p>
                <span class="status coming-soon">Coming Soon</span>
            </a>

            <a href="#" class="prototype-card" style="opacity: 0.6; cursor: not-allowed;">
                <h2>Sphere Grid</h2>
                <p>Strategic board game about placing spheres on a grid.</p>
                <span class="status coming-soon">Coming Soon</span>
            </a>

            <a href="#" class="prototype-card" style="opacity: 0.6; cursor: not-allowed;">
                <h2>Wiki RPG</h2>
                <p>Progression-based wiki explorer with unlockable content.</p>
                <span class="status coming-soon">Coming Soon</span>
            </a>
        </div>
    </div>
</body>
</html>
```

## Git Operations
```bash
git checkout -b feature/launcher-page
git add launcher/
git commit -m "feat: launcher page with prototype links"
git push -u origin feature/launcher-page
```

Then create PR with title: "Task 7: Launcher Page"

## Verification
- Comment `/build` on PR
- Visit main deployment URL
- Verify launcher page loads
- Verify link to SDF playground works

---

# WORKFLOW SUMMARY

## For Each Task:

1. **Tell Claude Code:** "Execute Task [NUMBER]"
2. **Review the code** it creates in the Claude app
3. **Iterate if needed:** "Update the shader to add smooth blending"
4. **When satisfied:** Claude Code will create the branch, commit, and push
5. **Create PR** on GitHub (in browser)
6. **Review PR** in GitHub
7. **Comment** `/build` on the PR
8. **Test** the deployed preview
9. **Merge** when satisfied

## Termux Local Testing:

```bash
# One-time setup
cd AI-playground
npm install

# Every time you want to test
npm run dev
```

Then visit `http://localhost:5173` in your Android browser.

## Tips:

- Tasks 3, 4, and 5 can be done in parallel if you want
- Task 6 depends on 3, 4, and 5 being complete
- Always test with `/build` before merging
- Keep PRs small and focused on one task

---

# END OF TASK SPECIFICATIONS
