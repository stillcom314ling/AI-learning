using System.Numerics;
using Raylib_cs;
using ShapeEngine.Core;
using ShapeEngine.Core.Structs;
using ShapeEngine.Lib;
using ShapeEngine.Text;

namespace RaylibCS;

public class RaylibDemo : Game
{
    private float timer = 0f;

    public RaylibDemo(GameSettings settings) : base(settings)
    {
    }

    protected override void OnHandleInputExample(float dt, Vector2 mousePosGame, Vector2 mousePosUI)
    {
    }

    protected override void OnDrawGameExample(ScreenInfo game)
    {
    }

    protected override void OnDrawGameUIExample(ScreenInfo ui)
    {
    }

    protected override void OnDrawUIExample(ScreenInfo ui)
    {
        var area = ui.Area;
        var center = area.GetPoint(new Vector2(0.5f, 0.5f));

        // Pulsing alpha for visual flair
        timer += Raylib.GetFrameTime();
        byte alpha = (byte)(180 + (int)(75 * MathF.Sin(timer * 2f)));

        // Title text
        var titleColor = new Raylib_cs.Color(0, 228, 48, (int)255);
        Raylib.DrawText("RaylibCS + ShapeEngine", (int)center.X - 250, (int)center.Y - 80, 32, titleColor);

        // Subtitle with pulsing effect
        var subColor = new Raylib_cs.Color(200, 200, 200, (int)alpha);
        Raylib.DrawText("Powered by Raylib-cs & ShapeEngine", (int)center.X - 230, (int)center.Y - 30, 20, subColor);

        // Info text
        var infoColor = new Raylib_cs.Color(130, 130, 230, (int)255);
        Raylib.DrawText("Press ESC to exit", (int)center.X - 100, (int)center.Y + 40, 20, infoColor);

        // FPS counter
        Raylib.DrawFPS(10, 10);
    }

    protected override void OnUpdateExample(GameTime time, ScreenInfo game, ScreenInfo ui)
    {
        if (Raylib.IsKeyPressed(KeyboardKey.Escape))
        {
            Quit();
        }
    }
}

public static class Program
{
    public static void Main()
    {
        var settings = new GameSettings()
        {
            Fullscreen = false,
            WindowMinSize = new Dimensions(800, 600),
            WindowSize = new Dimensions(1280, 720),
            Title = "RaylibCS Demo",
            TargetFramerate = 60,
            MultiShaderSupport = false
        };

        var game = new RaylibDemo(settings);
        game.Run();
    }
}
