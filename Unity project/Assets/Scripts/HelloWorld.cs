using UnityEngine;

/// <summary>
/// Simple Hello World script that displays a message on the screen.
/// </summary>
public class HelloWorld : MonoBehaviour
{
    [SerializeField] private string message = "Hello, World!";
    [SerializeField] private Color textColor = Color.white;
    [SerializeField] private int fontSize = 48;

    private GUIStyle guiStyle;

    private void Start()
    {
        Debug.Log(message);
    }

    private void OnGUI()
    {
        if (guiStyle == null)
        {
            guiStyle = new GUIStyle(GUI.skin.label)
            {
                fontSize = fontSize,
                alignment = TextAnchor.MiddleCenter,
                normal = { textColor = textColor }
            };
        }

        // Center the text on screen
        float width = Screen.width;
        float height = Screen.height;
        Rect rect = new Rect(0, 0, width, height);

        GUI.Label(rect, message, guiStyle);
    }
}
