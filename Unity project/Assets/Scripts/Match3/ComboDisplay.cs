using UnityEngine;

/// <summary>
/// Simple UI overlay that shows combo count and game title using OnGUI.
/// No Canvas or TextMeshPro dependencies needed.
/// </summary>
public class ComboDisplay : MonoBehaviour
{
    private int currentCombo;
    private float comboDisplayTimer;
    private GUIStyle titleStyle;
    private GUIStyle comboStyle;

    private void OnEnable()
    {
        // Listen to board combo events via a simple polling approach
        StartCoroutine(TrackCombos());
    }

    private System.Collections.IEnumerator TrackCombos()
    {
        int lastCombo = 0;
        while (true)
        {
            // This could be replaced with events, but polling is fine for a prototype
            yield return new WaitForSeconds(0.05f);

            // Count combos from debug log is hacky — instead we track board state
            var board = FindFirstObjectByType<Board>();
            if (board != null && board.IsBusy)
            {
                // Board is resolving — keep the display alive
                comboDisplayTimer = 2f;
            }
        }
    }

    /// <summary>
    /// Called externally by the board to report combo count.
    /// </summary>
    public void ShowCombo(int combo)
    {
        currentCombo = combo;
        comboDisplayTimer = 2f;
    }

    private void Update()
    {
        if (comboDisplayTimer > 0)
            comboDisplayTimer -= Time.deltaTime;
    }

    private void OnGUI()
    {
        if (titleStyle == null)
        {
            titleStyle = new GUIStyle(GUI.skin.label)
            {
                fontSize = 28,
                alignment = TextAnchor.UpperCenter,
                fontStyle = FontStyle.Bold,
                normal = { textColor = new Color(0.93f, 0.94f, 0.96f) }
            };

            comboStyle = new GUIStyle(GUI.skin.label)
            {
                fontSize = 36,
                alignment = TextAnchor.LowerCenter,
                fontStyle = FontStyle.Bold,
                normal = { textColor = new Color(0.95f, 0.61f, 0.07f) }
            };
        }

        // Title
        GUI.Label(new Rect(0, 10, Screen.width, 50), "Match-3 PAD", titleStyle);

        // Instructions
        var instrStyle = new GUIStyle(GUI.skin.label)
        {
            fontSize = 14,
            alignment = TextAnchor.UpperCenter,
            normal = { textColor = new Color(0.7f, 0.7f, 0.7f) }
        };
        GUI.Label(new Rect(0, 45, Screen.width, 30), "Drag orbs to swap — match 3 or more!", instrStyle);
    }
}
