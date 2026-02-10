using System;
using System.Runtime.InteropServices.JavaScript;
using Raylib_cs;

namespace RaylibCS;

public partial class Application
{
    private static float timer = 0f;

    public static void Main()
    {
        Raylib.InitWindow(800, 600, "RaylibCS WASM Demo");
        Raylib.SetTargetFPS(60);
    }

    [JSExport]
    public static void UpdateFrame()
    {
        timer += Raylib.GetFrameTime();
        byte alpha = (byte)(180 + (int)(75 * MathF.Sin(timer * 2f)));

        Raylib.BeginDrawing();
        Raylib.ClearBackground(new Color((byte)30, (byte)30, (byte)46, (byte)255));

        Raylib.DrawFPS(10, 10);

        Raylib.DrawText("RaylibCS + WASM", 200, 180, 40, Color.Green);
        Raylib.DrawText("Powered by Raylib-cs 7.0 & .NET 8", 180, 240, 20, new Color((byte)200, (byte)200, (byte)200, alpha));
        Raylib.DrawText("Running in your browser!", 250, 290, 20, new Color((byte)130, (byte)130, (byte)230, (byte)255));

        Raylib.EndDrawing();
    }
}
