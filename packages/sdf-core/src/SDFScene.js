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
