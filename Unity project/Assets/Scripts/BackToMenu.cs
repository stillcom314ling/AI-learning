using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.UI;

/// <summary>
/// Drop this on any GameObject in a child scene to get a "Back to Menu" button.
/// It creates its own Canvas and button at runtime so you don't need to set up UI manually.
/// </summary>
public class BackToMenu : MonoBehaviour
{
    [SerializeField] private string rootSceneName = "RootScene";
    [SerializeField] private KeyCode backKey = KeyCode.Escape;

    private void Start()
    {
        CreateBackButton();
    }

    private void Update()
    {
        if (Input.GetKeyDown(backKey))
        {
            ReturnToMenu();
        }
    }

    private void CreateBackButton()
    {
        // Canvas
        var canvasObj = new GameObject("BackToMenuCanvas");
        canvasObj.transform.SetParent(transform);
        var canvas = canvasObj.AddComponent<Canvas>();
        canvas.renderMode = RenderMode.ScreenSpaceOverlay;
        canvas.sortingOrder = 999;
        canvasObj.AddComponent<CanvasScaler>();
        canvasObj.AddComponent<GraphicRaycaster>();

        // Button
        var btnObj = new GameObject("BackButton", typeof(RectTransform));
        btnObj.transform.SetParent(canvasObj.transform, false);

        var btnRect = btnObj.GetComponent<RectTransform>();
        btnRect.anchorMin = new Vector2(0, 1);
        btnRect.anchorMax = new Vector2(0, 1);
        btnRect.pivot = new Vector2(0, 1);
        btnRect.anchoredPosition = new Vector2(10, -10);
        btnRect.sizeDelta = new Vector2(160, 50);

        var image = btnObj.AddComponent<Image>();
        image.color = new Color(0.2f, 0.2f, 0.3f, 0.9f);

        var button = btnObj.AddComponent<Button>();
        button.onClick.AddListener(ReturnToMenu);

        // Text
        var textObj = new GameObject("Text", typeof(RectTransform));
        textObj.transform.SetParent(btnObj.transform, false);

        var text = textObj.AddComponent<Text>();
        text.text = "< Back to Menu";
        text.font = Resources.GetBuiltinResource<Font>("LegacySRuntime.ttf");
        if (text.font == null)
            text.font = Resources.GetBuiltinResource<Font>("Arial.ttf");
        text.fontSize = 20;
        text.color = Color.white;
        text.alignment = TextAnchor.MiddleCenter;

        var textRect = textObj.GetComponent<RectTransform>();
        textRect.anchorMin = Vector2.zero;
        textRect.anchorMax = Vector2.one;
        textRect.offsetMin = Vector2.zero;
        textRect.offsetMax = Vector2.zero;
    }

    public void ReturnToMenu()
    {
        SceneManager.LoadScene(rootSceneName);
    }
}
