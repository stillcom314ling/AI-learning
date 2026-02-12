# AI-Playground

A Unity project for prototyping games and interactive experiences.

## Unity Project

Open the `Unity project/` folder in Unity (2021.3 LTS or later recommended).

### Prototypes

- **Match-3 PAD** — Puzzles & Dragons style match-3 with drag-to-swap mechanic. 6x7 board, 6 orb colors, cascade combos, gravity drop and refill. See `Assets/Scripts/Match3/`.

### Getting Started

1. Open `Unity project/` in Unity Hub
2. Open the `Match3` scene (or create a new scene and add a GameObject with the `Match3SceneSetup` component — it bootstraps everything at runtime)
3. Press Play

## Build

Comment `/build` on any PR to trigger a build and deployment.

The CI pipeline supports Android APK and WebGL builds via GameCI.
