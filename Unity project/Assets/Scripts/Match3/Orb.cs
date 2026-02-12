using UnityEngine;

/// <summary>
/// Represents a single orb on the match-3 board.
/// Attached to each orb GameObject (a circle sprite).
/// </summary>
public class Orb : MonoBehaviour
{
    public enum OrbColor
    {
        Red,
        Blue,
        Green,
        Yellow,
        Purple,
        Orange
    }

    public OrbColor Color { get; private set; }
    public int Row { get; set; }
    public int Col { get; set; }

    private SpriteRenderer spriteRenderer;
    private Vector3 targetPosition;
    private bool isAnimating;
    private float animSpeed = 12f;

    private static readonly Color[] orbColors = new Color[]
    {
        new Color(0.91f, 0.30f, 0.24f), // Red
        new Color(0.20f, 0.60f, 0.86f), // Blue
        new Color(0.18f, 0.80f, 0.44f), // Green
        new Color(0.95f, 0.77f, 0.06f), // Yellow
        new Color(0.61f, 0.35f, 0.71f), // Purple
        new Color(0.90f, 0.49f, 0.13f), // Orange
    };

    private void Awake()
    {
        spriteRenderer = GetComponent<SpriteRenderer>();
    }

    public void Init(OrbColor color, int row, int col)
    {
        Color = color;
        Row = row;
        Col = col;

        if (spriteRenderer == null)
            spriteRenderer = GetComponent<SpriteRenderer>();

        spriteRenderer.color = orbColors[(int)color];
    }

    public void SetTargetPosition(Vector3 pos)
    {
        targetPosition = pos;
        isAnimating = true;
    }

    public void SetPositionImmediate(Vector3 pos)
    {
        transform.position = pos;
        targetPosition = pos;
        isAnimating = false;
    }

    public bool IsAnimating => isAnimating;

    public void SetScale(float scale)
    {
        transform.localScale = Vector3.one * scale;
    }

    public void SetAlpha(float alpha)
    {
        if (spriteRenderer == null) return;
        var c = spriteRenderer.color;
        c.a = alpha;
        spriteRenderer.color = c;
    }

    public void SetSortingOrder(int order)
    {
        if (spriteRenderer != null)
            spriteRenderer.sortingOrder = order;
    }

    private void Update()
    {
        if (!isAnimating) return;

        transform.position = Vector3.Lerp(transform.position, targetPosition, Time.deltaTime * animSpeed);

        if (Vector3.Distance(transform.position, targetPosition) < 0.01f)
        {
            transform.position = targetPosition;
            isAnimating = false;
        }
    }
}
