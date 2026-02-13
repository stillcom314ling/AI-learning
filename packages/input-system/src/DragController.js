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
