import Phaser from 'phaser';

class DemoScene extends Phaser.Scene {
    constructor() {
        super({ key: 'DemoScene' });
    }

    create() {
        const { width, height } = this.scale;

        // Background gradient via graphics
        const bg = this.add.graphics();
        bg.fillGradientStyle(0x1a0033, 0x1a0033, 0x000d1a, 0x000d1a, 1);
        bg.fillRect(0, 0, width, height);

        // Title
        this.add.text(width / 2, 60, 'Phaser Demo', {
            fontSize: '42px',
            color: '#ffffff',
            fontStyle: 'bold',
        }).setOrigin(0.5);

        this.add.text(width / 2, 110, 'Build is working!', {
            fontSize: '20px',
            color: '#aaddff',
        }).setOrigin(0.5);

        // Bouncing balls
        this.balls = [];
        const colors = [0xff4466, 0x44aaff, 0xffcc00, 0x44ff99, 0xff8800];

        for (let i = 0; i < 8; i++) {
            const g = this.add.graphics();
            const color = colors[i % colors.length];
            g.fillStyle(color, 0.9);
            g.fillCircle(0, 0, 20 + (i % 3) * 10);

            const ball = {
                gfx: g,
                x: Phaser.Math.Between(80, width - 80),
                y: Phaser.Math.Between(160, height - 80),
                vx: Phaser.Math.FloatBetween(-150, 150),
                vy: Phaser.Math.FloatBetween(-150, 150),
                radius: 20 + (i % 3) * 10,
            };
            // Ensure non-zero velocity
            if (Math.abs(ball.vx) < 30) ball.vx = 80;
            if (Math.abs(ball.vy) < 30) ball.vy = 80;

            this.balls.push(ball);
        }

        // Instructions
        this.add.text(width / 2, height - 30, 'Click anywhere to add a ball', {
            fontSize: '14px',
            color: '#888888',
        }).setOrigin(0.5);

        this.input.on('pointerdown', (pointer) => {
            const g = this.add.graphics();
            const color = colors[Math.floor(Math.random() * colors.length)];
            g.fillStyle(color, 0.9);
            g.fillCircle(0, 0, 25);
            this.balls.push({
                gfx: g,
                x: pointer.x,
                y: pointer.y,
                vx: Phaser.Math.FloatBetween(-200, 200),
                vy: Phaser.Math.FloatBetween(-200, 200),
                radius: 25,
            });
        });
    }

    update(time, delta) {
        const dt = delta / 1000;
        const { width, height } = this.scale;

        for (const ball of this.balls) {
            ball.x += ball.vx * dt;
            ball.y += ball.vy * dt;

            if (ball.x - ball.radius < 0) { ball.x = ball.radius; ball.vx = Math.abs(ball.vx); }
            if (ball.x + ball.radius > width) { ball.x = width - ball.radius; ball.vx = -Math.abs(ball.vx); }
            if (ball.y - ball.radius < 140) { ball.y = 140 + ball.radius; ball.vy = Math.abs(ball.vy); }
            if (ball.y + ball.radius > height) { ball.y = height - ball.radius; ball.vy = -Math.abs(ball.vy); }

            ball.gfx.setPosition(ball.x, ball.y);
        }
    }
}

const game = new Phaser.Game({
    type: Phaser.AUTO,
    width: window.innerWidth,
    height: window.innerHeight,
    backgroundColor: '#000d1a',
    scene: DemoScene,
    scale: {
        mode: Phaser.Scale.RESIZE,
        autoCenter: Phaser.Scale.CENTER_BOTH,
    },
    parent: 'app',
});
