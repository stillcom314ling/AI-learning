using System.Collections;
using System.Collections.Generic;
using UnityEngine;

/// <summary>
/// Core match-3 board. Handles grid state, match detection, gravity, and refill.
/// 6 columns x 7 rows, Puzzles & Dragons style.
/// </summary>
public class Board : MonoBehaviour
{
    public const int Cols = 6;
    public const int Rows = 7;

    [SerializeField] private float cellSize = 1.1f;

    private GameObject orbPrefab;
    private Orb[,] grid = new Orb[Rows, Cols];
    private Vector3 boardOrigin;
    private bool initialized;

    public float CellSize => cellSize;
    public bool IsBusy { get; private set; }

    /// <summary>
    /// Called by Match3SceneSetup to provide the runtime-generated orb prefab.
    /// </summary>
    public void Init(GameObject prefab)
    {
        orbPrefab = prefab;

        boardOrigin = new Vector3(
            -(Cols - 1) * cellSize / 2f,
            -(Rows - 1) * cellSize / 2f,
            0f
        );

        initialized = true;
        FillBoard();
    }

    public Vector3 GridToWorld(int row, int col)
    {
        return boardOrigin + new Vector3(col * cellSize, (Rows - 1 - row) * cellSize, 0f);
    }

    public bool WorldToGrid(Vector3 worldPos, out int row, out int col)
    {
        Vector3 local = worldPos - boardOrigin;
        col = Mathf.RoundToInt(local.x / cellSize);
        int flippedRow = Mathf.RoundToInt(local.y / cellSize);
        row = (Rows - 1) - flippedRow;

        return row >= 0 && row < Rows && col >= 0 && col < Cols;
    }

    public Orb GetOrb(int row, int col)
    {
        if (row < 0 || row >= Rows || col < 0 || col >= Cols) return null;
        return grid[row, col];
    }

    public void SwapOrbs(int r1, int c1, int r2, int c2)
    {
        var tmp = grid[r1, c1];
        grid[r1, c1] = grid[r2, c2];
        grid[r2, c2] = tmp;

        if (grid[r1, c1] != null)
        {
            grid[r1, c1].Row = r1;
            grid[r1, c1].Col = c1;
            grid[r1, c1].SetTargetPosition(GridToWorld(r1, c1));
        }

        if (grid[r2, c2] != null)
        {
            grid[r2, c2].Row = r2;
            grid[r2, c2].Col = c2;
        }
    }

    public void ResolveBoard()
    {
        StartCoroutine(ResolveCoroutine());
    }

    private IEnumerator ResolveCoroutine()
    {
        IsBusy = true;
        int combo = 0;

        while (true)
        {
            yield return new WaitForSeconds(0.15f);

            var matches = FindMatches();
            if (matches.Count == 0) break;

            combo++;
            Debug.Log($"Combo {combo}! Matched {matches.Count} orbs.");

            foreach (var pos in matches)
            {
                var orb = grid[pos.x, pos.y];
                if (orb != null)
                    orb.SetAlpha(0.3f);
            }

            yield return new WaitForSeconds(0.3f);

            foreach (var pos in matches)
            {
                var orb = grid[pos.x, pos.y];
                if (orb != null)
                {
                    Destroy(orb.gameObject);
                    grid[pos.x, pos.y] = null;
                }
            }

            yield return new WaitForSeconds(0.1f);

            DropOrbs();
            yield return new WaitForSeconds(0.25f);

            RefillBoard();
            yield return new WaitForSeconds(0.3f);
        }

        if (combo > 0)
            Debug.Log($"Total combo: {combo}");

        IsBusy = false;
    }

    private HashSet<Vector2Int> FindMatches()
    {
        var matched = new HashSet<Vector2Int>();

        // Horizontal
        for (int r = 0; r < Rows; r++)
        {
            int run = 1;
            for (int c = 1; c < Cols; c++)
            {
                if (grid[r, c] != null && grid[r, c - 1] != null &&
                    grid[r, c].Color == grid[r, c - 1].Color)
                {
                    run++;
                }
                else
                {
                    if (run >= 3)
                    {
                        for (int k = c - run; k < c; k++)
                            matched.Add(new Vector2Int(r, k));
                    }
                    run = 1;
                }
            }
            if (run >= 3)
            {
                for (int k = Cols - run; k < Cols; k++)
                    matched.Add(new Vector2Int(r, k));
            }
        }

        // Vertical
        for (int c = 0; c < Cols; c++)
        {
            int run = 1;
            for (int r = 1; r < Rows; r++)
            {
                if (grid[r, c] != null && grid[r - 1, c] != null &&
                    grid[r, c].Color == grid[r - 1, c].Color)
                {
                    run++;
                }
                else
                {
                    if (run >= 3)
                    {
                        for (int k = r - run; k < r; k++)
                            matched.Add(new Vector2Int(k, c));
                    }
                    run = 1;
                }
            }
            if (run >= 3)
            {
                for (int k = Rows - run; k < Rows; k++)
                    matched.Add(new Vector2Int(k, c));
            }
        }

        return matched;
    }

    private void DropOrbs()
    {
        for (int c = 0; c < Cols; c++)
        {
            int writeRow = Rows - 1;
            for (int r = Rows - 1; r >= 0; r--)
            {
                if (grid[r, c] != null)
                {
                    if (r != writeRow)
                    {
                        grid[writeRow, c] = grid[r, c];
                        grid[r, c] = null;
                        grid[writeRow, c].Row = writeRow;
                        grid[writeRow, c].Col = c;
                        grid[writeRow, c].SetTargetPosition(GridToWorld(writeRow, c));
                    }
                    writeRow--;
                }
            }
        }
    }

    private void RefillBoard()
    {
        for (int c = 0; c < Cols; c++)
        {
            int blanks = 0;
            for (int r = 0; r < Rows; r++)
            {
                if (grid[r, c] == null)
                    blanks++;
            }

            int spawnIndex = 0;
            for (int r = 0; r < Rows; r++)
            {
                if (grid[r, c] == null)
                {
                    var orb = SpawnOrb(r, c);
                    Vector3 spawnPos = GridToWorld(-1 - spawnIndex, c);
                    orb.SetPositionImmediate(spawnPos);
                    orb.SetTargetPosition(GridToWorld(r, c));
                    spawnIndex++;
                }
            }
        }
    }

    private void FillBoard()
    {
        for (int r = 0; r < Rows; r++)
        {
            for (int c = 0; c < Cols; c++)
            {
                SpawnOrb(r, c);
            }
        }
    }

    private Orb SpawnOrb(int row, int col)
    {
        var color = (Orb.OrbColor)Random.Range(0, 6);
        var go = Instantiate(orbPrefab, GridToWorld(row, col), Quaternion.identity, transform);
        go.SetActive(true);
        var orb = go.GetComponent<Orb>();
        orb.Init(color, row, col);
        orb.SetPositionImmediate(GridToWorld(row, col));
        grid[row, col] = orb;
        return orb;
    }
}
