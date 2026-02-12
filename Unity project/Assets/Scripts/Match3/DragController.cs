using UnityEngine;

/// <summary>
/// Handles touch/mouse drag input for PAD-style orb movement.
/// Pick up an orb, drag across the board, orbs swap as you pass through.
/// </summary>
public class DragController : MonoBehaviour
{
    [SerializeField] private Board board;
    [SerializeField] private Camera mainCamera;

    private bool isDragging;
    private Orb draggedOrb;
    private int currentRow;
    private int currentCol;

    private void Update()
    {
        if (board.IsBusy) return;

        if (Input.GetMouseButtonDown(0) || (Input.touchCount > 0 && Input.GetTouch(0).phase == TouchPhase.Began))
        {
            TryStartDrag(GetWorldPointerPos());
        }
        else if (isDragging && (Input.GetMouseButton(0) || (Input.touchCount > 0 && Input.GetTouch(0).phase == TouchPhase.Moved)))
        {
            ContinueDrag(GetWorldPointerPos());
        }
        else if (isDragging && (Input.GetMouseButtonUp(0) || (Input.touchCount > 0 && Input.GetTouch(0).phase == TouchPhase.Ended)))
        {
            EndDrag();
        }

        // Follow finger while dragging
        if (isDragging && draggedOrb != null)
        {
            Vector3 worldPos = GetWorldPointerPos();
            draggedOrb.transform.position = new Vector3(worldPos.x, worldPos.y, -1f);
        }
    }

    private Vector3 GetWorldPointerPos()
    {
        Vector3 screenPos;
        if (Input.touchCount > 0)
            screenPos = Input.GetTouch(0).position;
        else
            screenPos = Input.mousePosition;

        screenPos.z = Mathf.Abs(mainCamera.transform.position.z);
        return mainCamera.ScreenToWorldPoint(screenPos);
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

        // Lift the dragged orb visually
        draggedOrb.SetSortingOrder(10);
        draggedOrb.SetScale(1.2f);
        draggedOrb.SetAlpha(0.85f);
    }

    private void ContinueDrag(Vector3 worldPos)
    {
        if (!board.WorldToGrid(worldPos, out int row, out int col)) return;
        if (row == currentRow && col == currentCol) return;

        // Only swap with adjacent cells (including diagonal)
        int dr = row - currentRow;
        int dc = col - currentCol;
        if (Mathf.Abs(dr) > 1 || Mathf.Abs(dc) > 1) return;

        // Swap on the board
        board.SwapOrbs(row, col, currentRow, currentCol);

        currentRow = row;
        currentCol = col;
    }

    private void EndDrag()
    {
        if (draggedOrb != null)
        {
            // Snap the orb back to its grid cell
            draggedOrb.SetSortingOrder(0);
            draggedOrb.SetScale(1f);
            draggedOrb.SetAlpha(1f);
            draggedOrb.SetTargetPosition(board.GridToWorld(currentRow, currentCol));
        }

        isDragging = false;
        draggedOrb = null;

        // Resolve matches after the player releases
        board.ResolveBoard();
    }
}
