// ─── Match-3 PAD Prototype ───────────────────────────────────────────
// Puzzles & Dragons style: pick up an orb, drag it around the board,
// orbs swap as you pass through them. After releasing, matches are
// resolved, matched orbs are cleared, the board drops & refills.

const COLS = 6;
const ROWS = 7;
const NUM_COLORS = 6;

const COLORS = [
  '#e74c3c', // red
  '#3498db', // blue
  '#2ecc71', // green
  '#f1c40f', // yellow
  '#9b59b6', // purple
  '#e67e22', // orange
];

const COLOR_NAMES = ['Red', 'Blue', 'Green', 'Yellow', 'Purple', 'Orange'];

// ─── Canvas setup ────────────────────────────────────────────────────
const canvas = document.getElementById('game');
const ctx = canvas.getContext('2d');

let cellSize, boardX, boardY, orbRadius;

function resize() {
  const dpr = window.devicePixelRatio || 1;
  const w = window.innerWidth;
  const h = window.innerHeight;

  // Size cells to fit the smaller dimension
  const maxCellW = Math.floor(w / COLS);
  const maxCellH = Math.floor((h * 0.85) / ROWS); // leave some top/bottom margin
  cellSize = Math.min(maxCellW, maxCellH);
  orbRadius = cellSize * 0.4;

  canvas.style.width = w + 'px';
  canvas.style.height = h + 'px';
  canvas.width = w * dpr;
  canvas.height = h * dpr;
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

  boardX = Math.floor((w - cellSize * COLS) / 2);
  boardY = Math.floor((h - cellSize * ROWS) / 2);
}

window.addEventListener('resize', resize);
resize();

// ─── Board state ─────────────────────────────────────────────────────
// board[row][col] = color index (0..NUM_COLORS-1)
let board = [];

function randomColor() {
  return Math.floor(Math.random() * NUM_COLORS);
}

function initBoard() {
  board = [];
  for (let r = 0; r < ROWS; r++) {
    board[r] = [];
    for (let c = 0; c < COLS; c++) {
      board[r][c] = randomColor();
    }
  }
}

initBoard();

// ─── Coordinate helpers ──────────────────────────────────────────────
function cellCenter(r, c) {
  return {
    x: boardX + c * cellSize + cellSize / 2,
    y: boardY + r * cellSize + cellSize / 2,
  };
}

function pixelToCell(px, py) {
  const c = Math.floor((px - boardX) / cellSize);
  const r = Math.floor((py - boardY) / cellSize);
  if (r >= 0 && r < ROWS && c >= 0 && c < COLS) return { r, c };
  return null;
}

// ─── Drag state ──────────────────────────────────────────────────────
let dragging = false;
let dragRow = -1;
let dragCol = -1;
let dragX = 0;
let dragY = 0;

// ─── Animation state ─────────────────────────────────────────────────
const STATE_IDLE = 0;
const STATE_DRAGGING = 1;
const STATE_MATCHING = 2;   // flash matched orbs
const STATE_DROPPING = 3;   // gravity + refill

let gameState = STATE_IDLE;
let matchTimer = 0;
let matchedCells = [];       // [{r, c}, ...]
let dropAnimations = [];     // [{col, row, fromY, toY, color, t}, ...]
let comboCount = 0;

const MATCH_FLASH_DURATION = 0.35; // seconds
const DROP_DURATION = 0.18;        // seconds per cell

// ─── Input handling (touch + mouse) ──────────────────────────────────
function getPos(e) {
  if (e.touches) {
    return { x: e.touches[0].clientX, y: e.touches[0].clientY };
  }
  return { x: e.clientX, y: e.clientY };
}

function onStart(e) {
  if (gameState !== STATE_IDLE) return;
  e.preventDefault();
  const pos = getPos(e);
  const cell = pixelToCell(pos.x, pos.y);
  if (!cell) return;

  dragging = true;
  dragRow = cell.r;
  dragCol = cell.c;
  dragX = pos.x;
  dragY = pos.y;
  gameState = STATE_DRAGGING;
}

function onMove(e) {
  if (!dragging) return;
  e.preventDefault();
  const pos = getPos(e);
  dragX = pos.x;
  dragY = pos.y;

  // Check if pointer entered a different cell – swap
  const cell = pixelToCell(pos.x, pos.y);
  if (cell && (cell.r !== dragRow || cell.c !== dragCol)) {
    // Only swap with adjacent cells (including diagonal for smoother feel)
    const dr = cell.r - dragRow;
    const dc = cell.c - dragCol;
    if (Math.abs(dr) <= 1 && Math.abs(dc) <= 1) {
      // Swap on the board
      const tmp = board[cell.r][cell.c];
      board[cell.r][cell.c] = board[dragRow][dragCol];
      board[dragRow][dragCol] = tmp;

      dragRow = cell.r;
      dragCol = cell.c;
    }
  }
}

function onEnd(e) {
  if (!dragging) return;
  e.preventDefault();
  dragging = false;
  gameState = STATE_IDLE;
  comboCount = 0;
  // Kick off match resolution
  resolveMatches();
}

canvas.addEventListener('mousedown', onStart);
canvas.addEventListener('mousemove', onMove);
canvas.addEventListener('mouseup', onEnd);
canvas.addEventListener('mouseleave', onEnd);
canvas.addEventListener('touchstart', onStart, { passive: false });
canvas.addEventListener('touchmove', onMove, { passive: false });
canvas.addEventListener('touchend', onEnd, { passive: false });
canvas.addEventListener('touchcancel', onEnd, { passive: false });

// ─── Match detection ─────────────────────────────────────────────────
function findMatches() {
  const matched = new Set();

  // Horizontal runs
  for (let r = 0; r < ROWS; r++) {
    let run = 1;
    for (let c = 1; c < COLS; c++) {
      if (board[r][c] === board[r][c - 1]) {
        run++;
      } else {
        if (run >= 3) {
          for (let k = c - run; k < c; k++) matched.add(r * COLS + k);
        }
        run = 1;
      }
    }
    if (run >= 3) {
      for (let k = COLS - run; k < COLS; k++) matched.add(r * COLS + k);
    }
  }

  // Vertical runs
  for (let c = 0; c < COLS; c++) {
    let run = 1;
    for (let r = 1; r < ROWS; r++) {
      if (board[r][c] === board[r - 1][c]) {
        run++;
      } else {
        if (run >= 3) {
          for (let k = r - run; k < r; k++) matched.add(k * COLS + c);
        }
        run = 1;
      }
    }
    if (run >= 3) {
      for (let k = ROWS - run; k < ROWS; k++) matched.add(k * COLS + c);
    }
  }

  return [...matched].map(i => ({ r: Math.floor(i / COLS), c: i % COLS }));
}

function resolveMatches() {
  matchedCells = findMatches();
  if (matchedCells.length > 0) {
    comboCount++;
    gameState = STATE_MATCHING;
    matchTimer = 0;
  }
}

// ─── Gravity & refill ────────────────────────────────────────────────
function dropAndRefill() {
  dropAnimations = [];

  for (let c = 0; c < COLS; c++) {
    // Collect surviving orbs bottom-up
    let write = ROWS - 1;
    const surviving = [];
    for (let r = ROWS - 1; r >= 0; r--) {
      if (board[r][c] !== -1) {
        surviving.push({ color: board[r][c], fromRow: r });
      }
    }
    // Place surviving orbs at the bottom
    surviving.reverse();
    const blanks = ROWS - surviving.length;
    for (let i = 0; i < surviving.length; i++) {
      const targetRow = blanks + i;
      board[targetRow][c] = surviving[i].color;
      if (surviving[i].fromRow !== targetRow) {
        dropAnimations.push({
          col: c,
          row: targetRow,
          fromY: cellCenter(surviving[i].fromRow, c).y,
          toY: cellCenter(targetRow, c).y,
          color: surviving[i].color,
          t: 0,
        });
      }
    }
    // Fill blanks from the top with new orbs
    for (let i = 0; i < blanks; i++) {
      const color = randomColor();
      board[i][c] = color;
      dropAnimations.push({
        col: c,
        row: i,
        fromY: boardY - (blanks - i) * cellSize + cellSize / 2,
        toY: cellCenter(i, c).y,
        color: color,
        t: 0,
      });
    }
  }

  if (dropAnimations.length > 0) {
    gameState = STATE_DROPPING;
  } else {
    // No drops needed, check for cascading matches
    resolveMatches();
  }
}

// ─── Drawing ─────────────────────────────────────────────────────────
function drawOrb(x, y, colorIdx, alpha = 1, scale = 1) {
  const r = orbRadius * scale;
  ctx.globalAlpha = alpha;

  // Outer circle
  ctx.beginPath();
  ctx.arc(x, y, r, 0, Math.PI * 2);
  ctx.fillStyle = COLORS[colorIdx];
  ctx.fill();

  // Highlight
  ctx.beginPath();
  ctx.arc(x - r * 0.25, y - r * 0.25, r * 0.45, 0, Math.PI * 2);
  const grad = ctx.createRadialGradient(
    x - r * 0.25, y - r * 0.25, 0,
    x - r * 0.25, y - r * 0.25, r * 0.45
  );
  grad.addColorStop(0, 'rgba(255,255,255,0.5)');
  grad.addColorStop(1, 'rgba(255,255,255,0)');
  ctx.fillStyle = grad;
  ctx.fill();

  // Outline
  ctx.beginPath();
  ctx.arc(x, y, r, 0, Math.PI * 2);
  ctx.strokeStyle = 'rgba(0,0,0,0.3)';
  ctx.lineWidth = 2;
  ctx.stroke();

  ctx.globalAlpha = 1;
}

function drawBoard() {
  // Board background
  ctx.fillStyle = '#16213e';
  ctx.fillRect(boardX, boardY, cellSize * COLS, cellSize * ROWS);

  // Grid lines
  ctx.strokeStyle = 'rgba(255,255,255,0.06)';
  ctx.lineWidth = 1;
  for (let r = 0; r <= ROWS; r++) {
    ctx.beginPath();
    ctx.moveTo(boardX, boardY + r * cellSize);
    ctx.lineTo(boardX + COLS * cellSize, boardY + r * cellSize);
    ctx.stroke();
  }
  for (let c = 0; c <= COLS; c++) {
    ctx.beginPath();
    ctx.moveTo(boardX + c * cellSize, boardY);
    ctx.lineTo(boardX + c * cellSize, boardY + ROWS * cellSize);
    ctx.stroke();
  }

  const isFlashing = gameState === STATE_MATCHING;
  const flashOn = isFlashing && Math.floor(matchTimer * 8) % 2 === 0;

  const droppingCells = new Set();
  if (gameState === STATE_DROPPING) {
    for (const a of dropAnimations) {
      droppingCells.add(a.row * COLS + a.col);
    }
  }

  // Draw orbs
  for (let r = 0; r < ROWS; r++) {
    for (let c = 0; c < COLS; c++) {
      if (board[r][c] < 0) continue; // cleared
      if (gameState === STATE_DRAGGING && r === dragRow && c === dragCol) continue; // dragged orb
      if (droppingCells.has(r * COLS + c)) continue; // will be drawn by animation

      const isMatched = isFlashing && matchedCells.some(m => m.r === r && m.c === c);
      const { x, y } = cellCenter(r, c);

      if (isMatched) {
        drawOrb(x, y, board[r][c], flashOn ? 0.3 : 1, flashOn ? 1.15 : 1);
      } else {
        drawOrb(x, y, board[r][c]);
      }
    }
  }

  // Draw drop animations
  if (gameState === STATE_DROPPING) {
    for (const a of dropAnimations) {
      const ease = easeOutBounce(Math.min(a.t, 1));
      const y = a.fromY + (a.toY - a.fromY) * ease;
      const x = boardX + a.col * cellSize + cellSize / 2;
      drawOrb(x, y, a.color);
    }
  }

  // Draw dragged orb on top (follows finger)
  if (gameState === STATE_DRAGGING) {
    // Shadow at cell position
    const { x: cx, y: cy } = cellCenter(dragRow, dragCol);
    ctx.beginPath();
    ctx.arc(cx, cy, orbRadius, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(255,255,255,0.12)';
    ctx.fill();

    // Orb under finger
    drawOrb(dragX, dragY, board[dragRow][dragCol], 0.85, 1.2);
  }
}

function drawHUD() {
  ctx.fillStyle = '#ecf0f1';
  ctx.font = `bold ${Math.round(cellSize * 0.35)}px sans-serif`;
  ctx.textAlign = 'center';
  ctx.fillText('Match-3 PAD', boardX + (COLS * cellSize) / 2, boardY - cellSize * 0.3);

  if (comboCount > 0 && gameState !== STATE_IDLE) {
    ctx.fillStyle = '#f39c12';
    ctx.font = `bold ${Math.round(cellSize * 0.5)}px sans-serif`;
    ctx.fillText(
      `${comboCount} Combo!`,
      boardX + (COLS * cellSize) / 2,
      boardY + ROWS * cellSize + cellSize * 0.6
    );
  }
}

// ─── Easing ──────────────────────────────────────────────────────────
function easeOutBounce(t) {
  if (t < 1 / 2.75) {
    return 7.5625 * t * t;
  } else if (t < 2 / 2.75) {
    t -= 1.5 / 2.75;
    return 7.5625 * t * t + 0.75;
  } else if (t < 2.5 / 2.75) {
    t -= 2.25 / 2.75;
    return 7.5625 * t * t + 0.9375;
  } else {
    t -= 2.625 / 2.75;
    return 7.5625 * t * t + 0.984375;
  }
}

// ─── Game loop ───────────────────────────────────────────────────────
let lastTime = 0;

function frame(timestamp) {
  const dt = Math.min((timestamp - lastTime) / 1000, 0.1);
  lastTime = timestamp;

  // Update
  if (gameState === STATE_MATCHING) {
    matchTimer += dt;
    if (matchTimer >= MATCH_FLASH_DURATION) {
      // Clear matched cells
      for (const m of matchedCells) {
        board[m.r][m.c] = -1;
      }
      matchedCells = [];
      dropAndRefill();
    }
  }

  if (gameState === STATE_DROPPING) {
    let allDone = true;
    for (const a of dropAnimations) {
      const dist = Math.abs(a.toY - a.fromY) / cellSize;
      const dur = DROP_DURATION * Math.max(dist, 1);
      a.t += dt / dur;
      if (a.t < 1) allDone = false;
    }
    if (allDone) {
      dropAnimations = [];
      gameState = STATE_IDLE;
      // Check for cascade matches
      resolveMatches();
    }
  }

  // Draw
  ctx.clearRect(0, 0, canvas.width / (window.devicePixelRatio || 1), canvas.height / (window.devicePixelRatio || 1));
  drawBoard();
  drawHUD();

  requestAnimationFrame(frame);
}

requestAnimationFrame(frame);
