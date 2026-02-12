using UnityEngine;

/// <summary>
/// Runtime bootstrapper for the Match-3 prototype.
/// Uses [RuntimeInitializeOnLoadMethod] so it runs automatically on any scene
/// without depending on scene-serialized MonoBehaviour references.
/// This guarantees the game starts on Android even if the scene's script
/// GUIDs don't resolve correctly in the build.
/// </summary>
public static class Match3Bootstrap
{
    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
    private static void AutoStart()
    {
        // Only bootstrap if no Board already exists (prevents double-init)
        if (Object.FindFirstObjectByType<Board>() != null) return;

        var go = new GameObject("Match3Bootstrap");
        go.AddComponent<Match3SceneSetup>();
    }
}
