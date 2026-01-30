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
        const labelText = new PIXI.Text({
            text: label,
            style: {
                fontSize: 14,
                fill: 0xffffff
            }
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
