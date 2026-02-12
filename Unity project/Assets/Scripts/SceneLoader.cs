using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.UI;

/// <summary>
/// Populates a ScrollView with buttons for every scene in Build Settings (except the root scene).
/// Attach this to a GameObject in the root scene and assign the content transform of a ScrollView.
/// </summary>
public class SceneLoader : MonoBehaviour
{
    [Header("UI References")]
    [SerializeField] private Transform contentParent;
    [SerializeField] private GameObject buttonPrefab;

    [Header("Settings")]
    [SerializeField] private string rootSceneName = "RootScene";

    private void Start()
    {
        PopulateSceneList();
    }

    private void PopulateSceneList()
    {
        int sceneCount = SceneManager.sceneCountInBuildSettings;

        for (int i = 0; i < sceneCount; i++)
        {
            string scenePath = SceneUtility.GetScenePathByBuildIndex(i);
            string sceneName = System.IO.Path.GetFileNameWithoutExtension(scenePath);

            // Skip the root scene itself
            if (sceneName == rootSceneName)
                continue;

            CreateSceneButton(sceneName);
        }
    }

    private void CreateSceneButton(string sceneName)
    {
        GameObject buttonObj;

        if (buttonPrefab != null)
        {
            buttonObj = Instantiate(buttonPrefab, contentParent);
        }
        else
        {
            // Create a button from scratch if no prefab assigned
            buttonObj = new GameObject(sceneName + "_Button", typeof(RectTransform));
            buttonObj.transform.SetParent(contentParent, false);

            var layoutElement = buttonObj.AddComponent<LayoutElement>();
            layoutElement.minHeight = 60;
            layoutElement.preferredHeight = 60;

            var image = buttonObj.AddComponent<Image>();
            image.color = new Color(0.25f, 0.25f, 0.35f, 1f);

            var button = buttonObj.AddComponent<Button>();
            var colors = button.colors;
            colors.highlightedColor = new Color(0.35f, 0.35f, 0.55f, 1f);
            colors.pressedColor = new Color(0.15f, 0.15f, 0.25f, 1f);
            button.colors = colors;

            // Text child
            var textObj = new GameObject("Text", typeof(RectTransform));
            textObj.transform.SetParent(buttonObj.transform, false);

            var text = textObj.AddComponent<Text>();
            text.text = sceneName;
            text.font = Resources.GetBuiltinResource<Font>("LegacySRuntime.ttf");
            if (text.font == null)
                text.font = Resources.GetBuiltinResource<Font>("Arial.ttf");
            text.fontSize = 24;
            text.color = Color.white;
            text.alignment = TextAnchor.MiddleCenter;

            var textRect = textObj.GetComponent<RectTransform>();
            textRect.anchorMin = Vector2.zero;
            textRect.anchorMax = Vector2.one;
            textRect.offsetMin = Vector2.zero;
            textRect.offsetMax = Vector2.zero;
        }

        var btn = buttonObj.GetComponent<Button>();
        if (btn != null)
        {
            string nameCapture = sceneName;
            btn.onClick.AddListener(() => LoadScene(nameCapture));
        }
    }

    public void LoadScene(string sceneName)
    {
        SceneManager.LoadScene(sceneName);
    }

    public void LoadRootScene()
    {
        SceneManager.LoadScene(rootSceneName);
    }
}
