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
