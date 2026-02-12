using UnityEngine;

/// <summary>
/// Runtime scene bootstrapper for the Match-3 prototype.
/// Creates the orb prefab, board, drag controller, and camera setup.
/// All wiring uses public Init methods (no reflection — safe for IL2CPP / Android).
/// Attach to a GameObject in the Match3 scene.
/// </summary>
public class Match3SceneSetup : MonoBehaviour
{
    private void Awake()
    {
        SetupCamera();
    }

    private void Start()
    {
        GameObject orbPrefab = CreateOrbPrefab();
        Board board = CreateBoard(orbPrefab);
        CreateDragController(board);
        SetupBackground();
    }

    private void SetupCamera()
    {
        var cam = Camera.main;
        if (cam == null)
        {
            var camGo = new GameObject("Main Camera");
            cam = camGo.AddComponent<Camera>();
            camGo.AddComponent<AudioListener>();
            camGo.tag = "MainCamera";
        }

        cam.orthographic = true;
        cam.orthographicSize = 5.5f;
        cam.transform.position = new Vector3(0, 0, -10);
        cam.backgroundColor = new Color(0.10f, 0.10f, 0.18f);
        cam.clearFlags = CameraClearFlags.SolidColor;
    }

    private GameObject CreateOrbPrefab()
    {
        var prefab = new GameObject("OrbPrefab");
        prefab.SetActive(false);

        var sr = prefab.AddComponent<SpriteRenderer>();
        sr.sprite = CreateCircleSprite(64);
        prefab.AddComponent<Orb>();

        return prefab;
    }

    private Board CreateBoard(GameObject orbPrefab)
    {
        var boardGo = new GameObject("Board");
        var board = boardGo.AddComponent<Board>();
        board.Init(orbPrefab);
        return board;
    }

    private void CreateDragController(Board board)
    {
        var dcGo = new GameObject("DragController");
        var dc = dcGo.AddComponent<DragController>();
        dc.Init(board, Camera.main);
    }

    private void SetupBackground()
    {
        var bgGo = new GameObject("BoardBackground");
        var sr = bgGo.AddComponent<SpriteRenderer>();
        sr.sprite = CreateSquareSprite(4);
        sr.color = new Color(0.09f, 0.13f, 0.24f, 0.9f);
        sr.sortingOrder = -10;

        float boardWidth = Board.Cols * 1.1f;
        float boardHeight = Board.Rows * 1.1f;
        bgGo.transform.localScale = new Vector3(boardWidth + 0.3f, boardHeight + 0.3f, 1f);
        bgGo.transform.position = new Vector3(0, 0, 1f);
    }

    private static Sprite CreateCircleSprite(int resolution)
    {
        var tex = new Texture2D(resolution, resolution, TextureFormat.RGBA32, false);
        tex.filterMode = FilterMode.Bilinear;

        float center = resolution / 2f;
        float radius = resolution / 2f - 1f;

        for (int y = 0; y < resolution; y++)
        {
            for (int x = 0; x < resolution; x++)
            {
                float dist = Vector2.Distance(new Vector2(x, y), new Vector2(center, center));
                if (dist <= radius - 1f)
                {
                    float highlight = Mathf.Clamp01(1f - Vector2.Distance(
                        new Vector2(x, y),
                        new Vector2(center - radius * 0.3f, center + radius * 0.3f)
                    ) / (radius * 0.8f));
                    float brightness = 0.85f + highlight * 0.15f;
                    tex.SetPixel(x, y, new Color(brightness, brightness, brightness, 1f));
                }
                else if (dist <= radius)
                {
                    float alpha = Mathf.Clamp01(radius - dist + 1f);
                    tex.SetPixel(x, y, new Color(0.7f, 0.7f, 0.7f, alpha));
                }
                else
                {
                    tex.SetPixel(x, y, Color.clear);
                }
            }
        }

        tex.Apply();
        return Sprite.Create(tex, new Rect(0, 0, resolution, resolution),
            new Vector2(0.5f, 0.5f), resolution);
    }

    private static Sprite CreateSquareSprite(int resolution)
    {
        var tex = new Texture2D(resolution, resolution, TextureFormat.RGBA32, false);
        for (int y = 0; y < resolution; y++)
            for (int x = 0; x < resolution; x++)
                tex.SetPixel(x, y, Color.white);
        tex.Apply();
        return Sprite.Create(tex, new Rect(0, 0, resolution, resolution),
            new Vector2(0.5f, 0.5f), resolution);
    }
}
