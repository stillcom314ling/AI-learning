# AI-Playground Project Tasks (C# + Raylib + WebAssembly)

This file contains all task specifications for building the AI-playground with C#, Raylib, and WebAssembly deployment to GitHub Pages.

---

## TASK MANIFEST

| Task | Branch | Dependencies | Status |
|------|--------|--------------|--------|
| 0 | Manual Setup | None | Not Started |
| 1 | feature/shared-libraries | Task 0 | Not Started |
| 2 | feature/github-actions-wasm | Task 1 | Not Started |
| 3 | feature/grid-placement-prototype | Task 1, 2 | Not Started |
| 4 | feature/launcher-page | Task 3 | Not Started |

---

# TASK 0: Manual Repository Setup

## Type
Manual - User Action Required

## Instructions for User

1. Create new repository on GitHub named "AI-playground"
2. Go to repository Settings → Pages
3. Under "Build and deployment" → Source: select "GitHub Actions"
4. Clone repository to your device (or just work through GitHub web interface)
5. Mark this task as complete in manifest

## Verification
- Repository exists on GitHub
- GitHub Pages is enabled with Actions source
- Ready to start Task 1

---

# TASK 1: Shared Libraries Foundation

## Branch
`feature/shared-libraries`

## Objective
Set up shared C# class libraries for common functionality (logging, input, UI helpers) that all prototypes can reference.

## Files to Create

### `SharedLibraries/RaylibHelpers/RaylibHelpers.csproj`
```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
    <Nullable>enable</Nullable>
    <AllowUnsafeBlocks>true</AllowUnsafeBlocks>
  </PropertyGroup>

  <ItemGroup>
    <PackageReference Include="Raylib-cs" Version="6.0.0" />
  </ItemGroup>
</Project>
```

### `SharedLibraries/RaylibHelpers/Logger.cs`
```csharp
using System;
using System.Collections.Generic;
using Raylib_cs;

namespace RaylibHelpers
{
    public static class Logger
    {
        private static List<string> _logs = new List<string>();
        private static int _maxLogs = 10;
        private static bool _showLogs = true;

        public static void Log(string message)
        {
            string timestamped = $"[{DateTime.Now:HH:mm:ss}] {message}";
            _logs.Add(timestamped);
            Console.WriteLine(timestamped);
            
            if (_logs.Count > _maxLogs)
                _logs.RemoveAt(0);
        }

        public static void Error(string message)
        {
            Log($"ERROR: {message}");
        }

        public static void Info(string message)
        {
            Log($"INFO: {message}");
        }

        public static void ToggleDisplay()
        {
            _showLogs = !_showLogs;
        }

        public static void Draw(int x, int y)
        {
            if (!_showLogs) return;

            int startY = y;
            Raylib.DrawRectangle(x - 5, startY - 5, 400, (_logs.Count * 20) + 10, new Color(0, 0, 0, 200));
            
            for (int i = 0; i < _logs.Count; i++)
            {
                Raylib.DrawText(_logs[i], x, startY + (i * 20), 14, Color.White);
            }
        }
    }
}
```

### `SharedLibraries/RaylibHelpers/InputHelper.cs`
```csharp
using System.Numerics;
using Raylib_cs;

namespace RaylibHelpers
{
    public static class InputHelper
    {
        public static Vector2 GetMousePosition()
        {
            return Raylib.GetMousePosition();
        }

        public static bool IsMouseButtonPressed(MouseButton button = MouseButton.Left)
        {
            return Raylib.IsMouseButtonPressed(button);
        }

        public static bool IsMouseButtonDown(MouseButton button = MouseButton.Left)
        {
            return Raylib.IsMouseButtonDown(button);
        }

        public static bool IsMouseButtonReleased(MouseButton button = MouseButton.Left)
        {
            return Raylib.IsMouseButtonReleased(button);
        }

        public static bool IsKeyPressed(KeyboardKey key)
        {
            return Raylib.IsKeyPressed(key);
        }
    }
}
```

### `SharedLibraries/RaylibHelpers/SimpleUI.cs`
```csharp
using System;
using System.Numerics;
using Raylib_cs;

namespace RaylibHelpers
{
    public static class SimpleUI
    {
        public static bool Button(string text, int x, int y, int width, int height)
        {
            Rectangle rect = new Rectangle(x, y, width, height);
            Vector2 mousePos = Raylib.GetMousePosition();
            bool isHovered = Raylib.CheckCollisionPointRec(mousePos, rect);
            bool isClicked = isHovered && Raylib.IsMouseButtonPressed(MouseButton.Left);

            Color bgColor = isHovered ? new Color(100, 100, 100, 255) : new Color(60, 60, 60, 255);
            
            Raylib.DrawRectangleRec(rect, bgColor);
            Raylib.DrawRectangleLinesEx(rect, 2, Color.White);
            
            int textWidth = Raylib.MeasureText(text, 20);
            Raylib.DrawText(text, x + (width - textWidth) / 2, y + (height - 20) / 2, 20, Color.White);

            return isClicked;
        }

        public static bool Toggle(string text, int x, int y, int width, int height, bool currentValue)
        {
            Rectangle rect = new Rectangle(x, y, width, height);
            Vector2 mousePos = Raylib.GetMousePosition();
            bool isHovered = Raylib.CheckCollisionPointRec(mousePos, rect);
            bool wasClicked = isHovered && Raylib.IsMouseButtonPressed(MouseButton.Left);

            Color bgColor = currentValue ? new Color(50, 150, 50, 255) : new Color(60, 60, 60, 255);
            if (isHovered)
                bgColor = new Color(bgColor.R + 30, bgColor.G + 30, bgColor.B + 30, 255);
            
            Raylib.DrawRectangleRec(rect, bgColor);
            Raylib.DrawRectangleLinesEx(rect, 2, Color.White);
            
            int textWidth = Raylib.MeasureText(text, 20);
            Raylib.DrawText(text, x + (width - textWidth) / 2, y + (height - 20) / 2, 20, Color.White);

            if (wasClicked)
                return !currentValue;
            
            return currentValue;
        }

        public static void Label(string text, int x, int y, int fontSize = 20, Color? color = null)
        {
            Raylib.DrawText(text, x, y, fontSize, color ?? Color.White);
        }
    }
}
```

### `SharedLibraries/RaylibHelpers/GameLoop.cs`
```csharp
using System;
using Raylib_cs;

namespace RaylibHelpers
{
    public abstract class GameLoop
    {
        protected int ScreenWidth { get; set; } = 800;
        protected int ScreenHeight { get; set; } = 600;
        protected string Title { get; set; } = "Raylib Game";
        protected int TargetFPS { get; set; } = 60;

        public void Run()
        {
            Logger.Info($"Initializing {Title}");
            Raylib.InitWindow(ScreenWidth, ScreenHeight, Title);
            Raylib.SetTargetFPS(TargetFPS);

            try
            {
                Initialize();
                Logger.Info("Game initialized successfully");

                while (!Raylib.WindowShouldClose())
                {
                    Update();
                    
                    Raylib.BeginDrawing();
                    Raylib.ClearBackground(Color.Black);
                    
                    Draw();
                    
                    // Draw logs in corner
                    Logger.Draw(10, ScreenHeight - 220);
                    
                    Raylib.EndDrawing();
                }
            }
            catch (Exception ex)
            {
                Logger.Error($"Runtime error: {ex.Message}");
                Logger.Error($"Stack trace: {ex.StackTrace}");
            }
            finally
            {
                Cleanup();
                Raylib.CloseWindow();
                Logger.Info("Game closed");
            }
        }

        protected abstract void Initialize();
        protected abstract void Update();
        protected abstract void Draw();
        protected virtual void Cleanup() { }
    }
}
```

### `README.md` (root)
```markdown
# AI-Playground

A collection of C# + Raylib game prototypes built for WebAssembly and deployed to GitHub Pages.

## Structure

- `SharedLibraries/` - Common code shared across prototypes
  - `RaylibHelpers/` - Logging, input, UI, and game loop helpers
- `Prototypes/` - Individual game prototypes
  - `GridPlacement/` - Grid-based shape placement prototype
- `Launcher/` - Web launcher page

## Development Workflow

1. Make changes to code
2. Push to feature branch
3. Create Pull Request
4. Comment `/build` on the PR
5. GitHub Actions builds WebAssembly
6. Test at the deployed URL
7. Merge when satisfied

## Local Testing (Not Required)

If you have .NET 8 SDK installed:
```bash
cd Prototypes/GridPlacement
dotnet run
```

## WebAssembly Build (Automated via GitHub Actions)

The build process uses Emscripten to compile C# to WebAssembly.
See `.github/workflows/build-deploy.yml` for details.
```

### `.gitignore`
```
## Ignore Visual Studio temporary files, build results, and
## files generated by popular Visual Studio add-ons.

# User-specific files
*.suo
*.user
*.userosscache
*.sln.docstates

# Build results
[Dd]ebug/
[Dd]ebugPublic/
[Rr]elease/
[Rr]eleases/
x64/
x86/
build/
bld/
[Bb]in/
[Oo]bj/

# Visual Studio cache/options directory
.vs/

# MSTest test Results
[Tt]est[Rr]esult*/
[Bb]uild[Ll]og.*

# NuGet Packages
*.nupkg
*.snupkg
**/packages/*

# WebAssembly output
wwwroot/
dist/
*.wasm
*.js
*.data

# OS files
.DS_Store
Thumbs.db

# Logs
*.log
```

## Git Operations
```bash
git checkout -b feature/shared-libraries
git add SharedLibraries/ README.md .gitignore
git commit -m "feat: shared libraries with logging, input, UI, and game loop"
git push -u origin feature/shared-libraries
```

Then create PR with title: "Task 1: Shared Libraries Foundation"

## Verification
- Files are created in correct structure
- PR is created on GitHub
- Ready for Task 2 (build system)

---

# TASK 2: GitHub Actions WebAssembly Build

## Branch
`feature/github-actions-wasm`

## Objective
Create GitHub Actions workflow that builds C# + Raylib to WebAssembly and deploys to GitHub Pages when `/build` is commented.

## Files to Create

### `.github/workflows/build-deploy.yml`
```yaml
name: Build and Deploy WebAssembly

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
          submodules: true
          
      - name: Setup .NET
        uses: actions/setup-dotnet@v4
        with:
          dotnet-version: '8.0.x'
          
      - name: Setup Emscripten
        uses: mymindstorm/setup-emsdk@v14
        with:
          version: '3.1.51'
          
      - name: Install wasm-tools
        run: dotnet workload install wasm-tools
        
      - name: Build Shared Libraries
        run: |
          cd SharedLibraries/RaylibHelpers
          dotnet build -c Release
          
      - name: Build Prototypes
        run: |
          # Build each prototype that exists
          if [ -d "Prototypes/GridPlacement" ]; then
            cd Prototypes/GridPlacement
            dotnet publish -c Release -o ../../dist/GridPlacement
            cd ../..
          fi
          
      - name: Create launcher index
        run: |
          mkdir -p dist
          cp Launcher/index.html dist/index.html || echo "Launcher not ready yet"
          
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
              body: '✅ Build complete! Preview: https://${{ github.repository_owner }}.github.io/AI-playground/\n\n📦 Prototypes available:\n- GridPlacement: https://${{ github.repository_owner }}.github.io/AI-playground/GridPlacement/'
            });
```

### `global.json` (root)
```json
{
  "sdk": {
    "version": "8.0.0",
    "rollForward": "latestMinor"
  }
}
```

## Git Operations
```bash
git checkout -b feature/github-actions-wasm
git add .github/ global.json
git commit -m "feat: GitHub Actions WebAssembly build pipeline"
git push -u origin feature/github-actions-wasm
```

Then create PR with title: "Task 2: GitHub Actions WebAssembly Build"

## Verification
- After PR is created, comment `/build` on it
- Check Actions tab for workflow run
- Workflow should complete (may warn about missing prototypes - that's ok)
- PR should get a comment with preview URL

## Notes
This sets up the build pipeline. It won't have anything to build until Task 3, but it's important to test the workflow early.

---

# TASK 3: Grid Placement Prototype

## Branch
`feature/grid-placement-prototype`

## Objective
Create the first prototype: a grid-based shape placement game where you can click to place circles on a grid.

## Files to Create

### `Prototypes/GridPlacement/GridPlacement.csproj`
```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net8.0</TargetFramework>
    <Nullable>enable</Nullable>
    <AllowUnsafeBlocks>true</AllowUnsafeBlocks>
    <RuntimeIdentifier>browser-wasm</RuntimeIdentifier>
    <PublishTrimmed>true</PublishTrimmed>
  </PropertyGroup>

  <ItemGroup>
    <PackageReference Include="Raylib-cs" Version="6.0.0" />
  </ItemGroup>

  <ItemGroup>
    <ProjectReference Include="..\..\SharedLibraries\RaylibHelpers\RaylibHelpers.csproj" />
  </ItemGroup>
</Project>
```

### `Prototypes/GridPlacement/Program.cs`
```csharp
using RaylibHelpers;

namespace GridPlacement
{
    class Program
    {
        static void Main(string[] args)
        {
            var game = new GridPlacementGame();
            game.Run();
        }
    }
}
```

### `Prototypes/GridPlacement/GridPlacementGame.cs`
```csharp
using System;
using System.Numerics;
using Raylib_cs;
using RaylibHelpers;

namespace GridPlacement
{
    public class GridPlacementGame : GameLoop
    {
        private const int GridSize = 8;
        private const int CellSize = 60;
        private GridCell[,] _grid;
        private int _gridOffsetX;
        private int _gridOffsetY;
        private bool _showDebug = true;

        public GridPlacementGame()
        {
            Title = "Grid Placement Prototype";
            ScreenWidth = 800;
            ScreenHeight = 700;
            _grid = new GridCell[GridSize, GridSize];
        }

        protected override void Initialize()
        {
            Logger.Info("Initializing grid placement game");
            
            // Center the grid
            _gridOffsetX = (ScreenWidth - (GridSize * CellSize)) / 2;
            _gridOffsetY = (ScreenHeight - (GridSize * CellSize)) / 2;

            // Initialize empty grid
            for (int x = 0; x < GridSize; x++)
            {
                for (int y = 0; y < GridSize; y++)
                {
                    _grid[x, y] = new GridCell { IsOccupied = false };
                }
            }

            Logger.Info($"Grid initialized: {GridSize}x{GridSize}");
        }

        protected override void Update()
        {
            // Toggle debug display
            if (InputHelper.IsKeyPressed(KeyboardKey.D))
            {
                _showDebug = !_showDebug;
                Logger.ToggleDisplay();
                Logger.Info($"Debug display: {(_showDebug ? "ON" : "OFF")}");
            }

            // Handle mouse clicks on grid
            if (InputHelper.IsMouseButtonPressed())
            {
                Vector2 mousePos = InputHelper.GetMousePosition();
                int gridX = (int)((mousePos.X - _gridOffsetX) / CellSize);
                int gridY = (int)((mousePos.Y - _gridOffsetY) / CellSize);

                if (IsValidGridPosition(gridX, gridY))
                {
                    _grid[gridX, gridY].IsOccupied = !_grid[gridX, gridY].IsOccupied;
                    Logger.Info($"Toggled cell ({gridX}, {gridY}) -> {(_grid[gridX, gridY].IsOccupied ? "Occupied" : "Empty")}");
                }
            }
        }

        protected override void Draw()
        {
            // Draw title
            SimpleUI.Label("Grid Placement - Click cells to place/remove", 20, 20, 24);
            SimpleUI.Label("Press 'D' to toggle debug logs", 20, 50, 16, Color.Gray);

            // Draw grid
            for (int x = 0; x < GridSize; x++)
            {
                for (int y = 0; y < GridSize; y++)
                {
                    int screenX = _gridOffsetX + (x * CellSize);
                    int screenY = _gridOffsetY + (y * CellSize);

                    // Draw cell background
                    Color cellColor = new Color(40, 40, 40, 255);
                    Raylib.DrawRectangle(screenX, screenY, CellSize, CellSize, cellColor);
                    
                    // Draw cell border
                    Raylib.DrawRectangleLines(screenX, screenY, CellSize, CellSize, Color.DarkGray);

                    // Draw occupied cells
                    if (_grid[x, y].IsOccupied)
                    {
                        int centerX = screenX + CellSize / 2;
                        int centerY = screenY + CellSize / 2;
                        int radius = CellSize / 3;
                        Raylib.DrawCircle(centerX, centerY, radius, new Color(100, 200, 255, 255));
                        Raylib.DrawCircleLines(centerX, centerY, radius, Color.White);
                    }

                    // Highlight hovered cell
                    Vector2 mousePos = InputHelper.GetMousePosition();
                    if (mousePos.X >= screenX && mousePos.X < screenX + CellSize &&
                        mousePos.Y >= screenY && mousePos.Y < screenY + CellSize)
                    {
                        Raylib.DrawRectangleLines(screenX, screenY, CellSize, CellSize, Color.White);
                    }
                }
            }

            // Draw stats
            int occupiedCount = 0;
            for (int x = 0; x < GridSize; x++)
                for (int y = 0; y < GridSize; y++)
                    if (_grid[x, y].IsOccupied)
                        occupiedCount++;

            SimpleUI.Label($"Cells occupied: {occupiedCount}/{GridSize * GridSize}", 20, ScreenHeight - 40, 18);
        }

        private bool IsValidGridPosition(int x, int y)
        {
            return x >= 0 && x < GridSize && y >= 0 && y < GridSize;
        }

        private class GridCell
        {
            public bool IsOccupied { get; set; }
        }
    }
}
```

### `Prototypes/GridPlacement/index.html`
```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Grid Placement - AI Playground</title>
    <style>
        body {
            margin: 0;
            padding: 0;
            background: #1a1a1a;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            font-family: Arial, sans-serif;
        }
        #container {
            text-align: center;
        }
        canvas {
            border: 2px solid #444;
            display: block;
            margin: 20px auto;
        }
        .info {
            color: #ccc;
            margin: 20px;
        }
    </style>
</head>
<body>
    <div id="container">
        <div class="info">
            <h1 style="color: white;">Grid Placement Prototype</h1>
            <p>Click cells to place or remove shapes</p>
        </div>
        <canvas id="canvas"></canvas>
        <div class="info">
            <p>Press 'D' to toggle debug logs</p>
            <p><a href="../" style="color: #6af;">← Back to Launcher</a></p>
        </div>
    </div>
    <script src="GridPlacement.js"></script>
</body>
</html>
```

## Git Operations
```bash
git checkout -b feature/grid-placement-prototype
git add Prototypes/GridPlacement/
git commit -m "feat: grid placement prototype game"
git push -u origin feature/grid-placement-prototype
```

Then create PR with title: "Task 3: Grid Placement Prototype"

## Verification
- Comment `/build` on PR
- Wait for GitHub Action to complete
- Visit the deployed URL
- Test clicking on grid cells
- Test pressing 'D' to toggle debug
- Verify logs appear in bottom-left corner

---

# TASK 4: Launcher Page

## Branch
`feature/launcher-page`

## Objective
Create a simple HTML launcher page that links to all available prototypes.

## Files to Create

### `Launcher/index.html`
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Playground - C# + Raylib</title>
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
            max-width: 900px;
            width: 100%;
        }
        
        h1 {
            color: white;
            font-size: 3rem;
            margin-bottom: 0.5rem;
            text-align: center;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .subtitle {
            color: rgba(255,255,255,0.9);
            text-align: center;
            margin-bottom: 3rem;
            font-size: 1.2rem;
        }
        
        .tech-stack {
            background: rgba(255,255,255,0.1);
            padding: 10px 20px;
            border-radius: 20px;
            display: inline-block;
            margin-bottom: 2rem;
        }
        
        .tech-stack span {
            color: white;
            font-size: 0.9rem;
            margin: 0 10px;
        }
        
        .prototypes {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
        }
        
        .prototype-card {
            background: white;
            border-radius: 12px;
            padding: 30px;
            text-decoration: none;
            color: #333;
            transition: transform 0.3s, box-shadow 0.3s;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            position: relative;
            overflow: hidden;
        }
        
        .prototype-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.2);
        }
        
        .prototype-card h2 {
            color: #667eea;
            margin-bottom: 15px;
            font-size: 1.6rem;
        }
        
        .prototype-card p {
            color: #666;
            line-height: 1.6;
            margin-bottom: 15px;
        }
        
        .status {
            display: inline-block;
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: bold;
            margin-top: 10px;
        }
        
        .status.live {
            background: #4CAF50;
            color: white;
        }
        
        .status.coming-soon {
            background: #FF9800;
            color: white;
        }
        
        .footer {
            margin-top: 3rem;
            text-align: center;
            color: rgba(255,255,255,0.8);
            font-size: 0.9rem;
        }
        
        .footer a {
            color: white;
            text-decoration: none;
            font-weight: bold;
        }
        
        .info-box {
            background: rgba(255,255,255,0.95);
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 2rem;
        }
        
        .info-box h3 {
            color: #667eea;
            margin-bottom: 10px;
        }
        
        .info-box p {
            color: #666;
            line-height: 1.6;
        }
    </style>
</head>
<body>
    <div class="container">
        <div style="text-align: center;">
            <h1>🎮 AI Playground</h1>
            <p class="subtitle">Game prototypes built with C# and Raylib</p>
            <div class="tech-stack">
                <span>C# 12</span> • <span>Raylib</span> • <span>WebAssembly</span> • <span>GitHub Actions</span>
            </div>
        </div>

        <div class="info-box">
            <h3>About This Project</h3>
            <p>
                This is a collection of game prototypes built with C# and Raylib, compiled to WebAssembly 
                and deployed automatically via GitHub Actions. Each prototype is a separate project exploring 
                different game mechanics and ideas.
            </p>
        </div>
        
        <div class="prototypes">
            <a href="GridPlacement/" class="prototype-card">
                <h2>📐 Grid Placement</h2>
                <p>
                    Interactive grid-based placement system. Click cells to add or remove shapes.
                    A foundation for grid-based strategy games.
                </p>
                <p style="font-size: 0.85rem; color: #999;">
                    <strong>Features:</strong> Click detection, grid rendering, debug logging
                </p>
                <span class="status live">● Live</span>
            </a>
            
            <a href="#" class="prototype-card" style="opacity: 0.6; cursor: not-allowed;">
                <h2>💎 Match-3 Game</h2>
                <p>
                    Classic match-3 puzzle mechanics with gem matching and cascading effects.
                </p>
                <p style="font-size: 0.85rem; color: #999;">
                    <strong>Planned:</strong> Gem swapping, match detection, scoring
                </p>
                <span class="status coming-soon">Coming Soon</span>
            </a>
            
            <a href="#" class="prototype-card" style="opacity: 0.6; cursor: not-allowed;">
                <h2>🎯 Sphere Grid Strategy</h2>
                <p>
                    Strategic board game about placing and connecting spheres on a hex grid.
                </p>
                <p style="font-size: 0.85rem; color: #999;">
                    <strong>Planned:</strong> Hex grid, sphere physics, territory control
                </p>
                <span class="status coming-soon">Coming Soon</span>
            </a>
            
            <a href="#" class="prototype-card" style="opacity: 0.6; cursor: not-allowed;">
                <h2>📚 Wiki RPG</h2>
                <p>
                    Progression-based wiki explorer with unlockable content and discoveries.
                </p>
                <p style="font-size: 0.85rem; color: #999;">
                    <strong>Planned:</strong> Content tree, progression system, UI framework
                </p>
                <span class="status coming-soon">Coming Soon</span>
            </a>
        </div>

        <div class="footer">
            <p>Built with Claude Code • Deployed via GitHub Actions</p>
            <p style="margin-top: 10px;">
                <a href="https://github.com/YOUR-USERNAME/AI-playground">View Source on GitHub →</a>
            </p>
        </div>
    </div>
</body>
</html>
```

## Git Operations
```bash
git checkout -b feature/launcher-page
git add Launcher/
git commit -m "feat: launcher page for prototype selection"
git push -u origin feature/launcher-page
```

Then create PR with title: "Task 4: Launcher Page"

## Verification
- Comment `/build` on PR
- Visit main deployment URL (should show launcher)
- Click on Grid Placement link
- Verify it navigates to the prototype
- Test back button to return to launcher

---

# WORKFLOW SUMMARY

## For Each Task:

1. **Tell Claude Code:** "Execute Task [NUMBER]"
2. **Review the code** it creates in the Claude app
3. **Iterate if needed:** "Add more grid cells" or "Change colors"
4. **When satisfied:** Claude Code will create the branch, commit, and push
5. **Create PR** on GitHub (in browser)
6. **Review PR** in GitHub
7. **Comment** `/build` on the PR
8. **Wait** for GitHub Action to complete (5-10 minutes)
9. **Test** the deployed WebAssembly build on your Android browser
10. **Merge** when satisfied

## Emscripten Build Notes:

The GitHub Action compiles C# → .NET IL → WebAssembly using:
- .NET 8 SDK
- Emscripten 3.1.51
- wasm-tools workload

The output is:
- `.wasm` files (compiled code)
- `.js` files (runtime/loader)
- `.data` files (embedded resources)
- `index.html` (entry point)

All deployed to `https://YOUR-USERNAME.github.io/AI-playground/`

## Testing on Android:

1. Open Chrome/Firefox on your Android device
2. Navigate to `https://YOUR-USERNAME.github.io/AI-playground/`
3. Click on a prototype
4. The WebAssembly should load and run in the browser
5. Touch events work like mouse clicks

## Debug Tips:

- Press 'D' in any game to toggle debug logs
- Logs appear in bottom-left corner of the canvas
- Check browser console (Chrome DevTools via desktop) for errors
- GitHub Actions logs show build errors

## Common Issues:

**Build fails:**
- Check GitHub Actions logs
- Verify .csproj files are valid XML
- Ensure all project references are correct

**Game doesn't load:**
- Check browser console for errors
- Verify all .wasm, .js, .data files deployed
- Check for CORS issues (shouldn't happen on GitHub Pages)

**Touch not working:**
- Raylib maps touch to mouse events automatically
- Check InputHelper is being used correctly
- Verify canvas element is properly sized

---

# NEXT STEPS AFTER COMPLETION

Once all 4 tasks are complete, you'll have:
- ✅ Shared C# libraries for common functionality
- ✅ Automated WebAssembly build pipeline
- ✅ One working prototype (Grid Placement)
- ✅ Launcher page for navigation

To add more prototypes:
1. Copy `Prototypes/GridPlacement/` folder
2. Rename and modify for new game
3. Update `.github/workflows/build-deploy.yml` to include new prototype
4. Update `Launcher/index.html` to add new card
5. Follow same PR → `/build` → test → merge workflow

---

# END OF TASK SPECIFICATIONS
