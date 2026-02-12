using UnityEngine;

/// <summary>
/// Handles touch/mouse drag input for PAD-style orb movement.
/// Pick up an orb, drag across the board, orbs swap as you pass through.
/// Touch-first design for Android with mouse fallback for editor testing.
/// </summary>
public class DragController : MonoBehaviour
{
    private Board board;
    private Camera mainCamera;

    private bool isDragging;
    private Orb draggedOrb;
    private int currentRow;
    private int currentCol;
    private bool usingTouch;

    public void Init(Board board, Camera camera)
    {
        this.board = board;
        this.mainCamera = camera;
    }

    private void Update()
    {
        if (board == null || mainCamera == null) return;
        if (board.IsBusy)
        {
            if (isDragging) EndDrag();
            return;
        }

        // Touch input takes priority (Android)
        if (Input.touchCount > 0)
        {
            usingTouch = true;
            HandleTouch();
        }
        else if (!usingTouch)
        {
            // Mouse fallback (editor only — on Android, mouse events are
            // synthesized from touches so we skip them when touch is active)
            HandleMouse();
        }
        else if (Input.touchCount == 0)
        {
            usingTouch = false;
        }

        // Keep the dragged orb under the finger/cursor
        if (isDragging && draggedOrb != null)
        {
            Vector3 worldPos = GetWorldPointerPos();
            draggedOrb.transform.position = new Vector3(worldPos.x, worldPos.y, -1f);
        }
    }

    private void HandleTouch()
    {
        Touch touch = Input.GetTouch(0);

        switch (touch.phase)
        {
            case TouchPhase.Began:
                TryStartDrag(TouchToWorld(touch));
                break;

            case TouchPhase.Moved:
            case TouchPhase.Stationary:
                if (isDragging)
                    ContinueDrag(TouchToWorld(touch));
                break;

            case TouchPhase.Ended:
            case TouchPhase.Canceled:
                if (isDragging)
                    EndDrag();
                break;
        }
    }

    private void HandleMouse()
    {
        if (Input.GetMouseButtonDown(0))
        {
            TryStartDrag(MouseToWorld());
        }
        else if (isDragging && Input.GetMouseButton(0))
        {
            ContinueDrag(MouseToWorld());
        }
        else if (isDragging && Input.GetMouseButtonUp(0))
        {
            EndDrag();
        }
    }

    private Vector3 TouchToWorld(Touch touch)
    {
        Vector3 screenPos = new Vector3(touch.position.x, touch.position.y,
            Mathf.Abs(mainCamera.transform.position.z));
        return mainCamera.ScreenToWorldPoint(screenPos);
    }

    private Vector3 MouseToWorld()
    {
        Vector3 screenPos = Input.mousePosition;
        screenPos.z = Mathf.Abs(mainCamera.transform.position.z);
        return mainCamera.ScreenToWorldPoint(screenPos);
    }

    private Vector3 GetWorldPointerPos()
    {
        if (Input.touchCount > 0)
            return TouchToWorld(Input.GetTouch(0));
        return MouseToWorld();
    }

    private void TryStartDrag(Vector3 worldPos)
    {
        if (!board.WorldToGrid(worldPos, out int row, out int col)) return;

        var orb = board.GetOrb(row, col);
        if (orb == null) return;

        isDragging = true;
        draggedOrb = orb;
        currentRow = row;
        currentCol = col;

        draggedOrb.SetSortingOrder(10);
        draggedOrb.SetScale(1.2f);
        draggedOrb.SetAlpha(0.85f);
    }

    private void ContinueDrag(Vector3 worldPos)
    {
        if (!board.WorldToGrid(worldPos, out int row, out int col)) return;
        if (row == currentRow && col == currentCol) return;

        int dr = row - currentRow;
        int dc = col - currentCol;
        if (Mathf.Abs(dr) > 1 || Mathf.Abs(dc) > 1) return;

        board.SwapOrbs(row, col, currentRow, currentCol);
        currentRow = row;
        currentCol = col;
    }

    private void EndDrag()
    {
        if (draggedOrb != null)
        {
            draggedOrb.SetSortingOrder(0);
            draggedOrb.SetScale(1f);
            draggedOrb.SetAlpha(1f);
            draggedOrb.SetTargetPosition(board.GridToWorld(currentRow, currentCol));
        }

        isDragging = false;
        draggedOrb = null;

        board.ResolveBoard();
    }
}
