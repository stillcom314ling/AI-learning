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
