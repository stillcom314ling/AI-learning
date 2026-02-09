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
