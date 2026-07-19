import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="지렁이 게임 🐛", page_icon="🐛", layout="centered")

st.title("🐛 지렁이 게임")
st.caption("방향키(← ↑ → ↓) 또는 W A S D로 조작하세요. 스마트폰은 스와이프로도 가능합니다.")

GAME_HTML = """
<div id="game-wrap" style="display:flex;flex-direction:column;align-items:center;font-family:sans-serif;">
  <div style="display:flex;justify-content:space-between;width:420px;margin-bottom:8px;">
    <div style="font-size:18px;font-weight:bold;color:#333;">점수: <span id="score">0</span></div>
    <div style="font-size:18px;font-weight:bold;color:#333;">최고 점수: <span id="best">0</span></div>
  </div>
  <canvas id="board" width="400" height="400" style="background:#1b1f27;border-radius:12px;border:4px solid #3a3f4b;touch-action:none;"></canvas>
  <div style="margin-top:12px;">
    <button id="restartBtn" style="padding:8px 20px;font-size:15px;border-radius:8px;border:none;background:#4CAF50;color:white;cursor:pointer;">다시 시작</button>
  </div>
  <div id="status" style="margin-top:10px;font-size:16px;color:#d33;font-weight:bold;height:20px;"></div>
</div>

<script>
(function() {
  const canvas = document.getElementById("board");
  const ctx = canvas.getContext("2d");
  const scoreEl = document.getElementById("score");
  const bestEl = document.getElementById("best");
  const statusEl = document.getElementById("status");
  const restartBtn = document.getElementById("restartBtn");

  const GRID = 20;
  const CELLS = canvas.width / GRID;

  let snake, dir, nextDir, food, score, best, alive, loopId;

  function loadBest() {
    try {
      return parseInt(localStorage.getItem("worm_game_best") || "0", 10);
    } catch (e) { return 0; }
  }
  function saveBest(v) {
    try { localStorage.setItem("worm_game_best", String(v)); } catch (e) {}
  }

  function randomFood() {
    let pos;
    do {
      pos = {
        x: Math.floor(Math.random() * CELLS),
        y: Math.floor(Math.random() * CELLS)
      };
    } while (snake.some(s => s.x === pos.x && s.y === pos.y));
    return pos;
  }

  function init() {
    snake = [{x: 8, y: 10}, {x: 7, y: 10}, {x: 6, y: 10}];
    dir = {x: 1, y: 0};
    nextDir = {x: 1, y: 0};
    score = 0;
    best = loadBest();
    alive = true;
    food = randomFood();
    scoreEl.textContent = score;
    bestEl.textContent = best;
    statusEl.textContent = "";
    if (loopId) clearInterval(loopId);
    loopId = setInterval(tick, 110);
    draw();
  }

  function tick() {
    if (!alive) return;
    dir = nextDir;
    const head = {x: snake[0].x + dir.x, y: snake[0].y + dir.y};

    if (head.x < 0 || head.y < 0 || head.x >= CELLS || head.y >= CELLS ||
        snake.some(s => s.x === head.x && s.y === head.y)) {
      gameOver();
      return;
    }

    snake.unshift(head);

    if (head.x === food.x && head.y === food.y) {
      score += 10;
      scoreEl.textContent = score;
      if (score > best) {
        best = score;
        bestEl.textContent = best;
        saveBest(best);
      }
      food = randomFood();
    } else {
      snake.pop();
    }
    draw();
  }

  function gameOver() {
    alive = false;
    clearInterval(loopId);
    statusEl.textContent = "게임 오버! 다시 시작 버튼을 눌러주세요.";
  }

  function draw() {
    ctx.fillStyle = "#1b1f27";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    ctx.fillStyle = "#ff5b5b";
    ctx.beginPath();
    ctx.arc(food.x * GRID + GRID/2, food.y * GRID + GRID/2, GRID/2 - 2, 0, Math.PI * 2);
    ctx.fill();

    snake.forEach((s, i) => {
      ctx.fillStyle = i === 0 ? "#7CFC00" : "#4CAF50";
      ctx.fillRect(s.x * GRID + 1, s.y * GRID + 1, GRID - 2, GRID - 2);
    });
  }

  function setDir(nx, ny) {
    if (dir.x === -nx && dir.y === -ny) return;
    nextDir = {x: nx, y: ny};
  }

  document.addEventListener("keydown", (e) => {
    switch (e.key) {
      case "ArrowUp": case "w": case "W": setDir(0, -1); e.preventDefault(); break;
      case "ArrowDown": case "s": case "S": setDir(0, 1); e.preventDefault(); break;
      case "ArrowLeft": case "a": case "A": setDir(-1, 0); e.preventDefault(); break;
      case "ArrowRight": case "d": case "D": setDir(1, 0); e.preventDefault(); break;
    }
  });

  let touchStart = null;
  canvas.addEventListener("touchstart", (e) => {
    touchStart = {x: e.touches[0].clientX, y: e.touches[0].clientY};
  });
  canvas.addEventListener("touchend", (e) => {
    if (!touchStart) return;
    const dx = e.changedTouches[0].clientX - touchStart.x;
    const dy = e.changedTouches[0].clientY - touchStart.y;
    if (Math.abs(dx) > Math.abs(dy)) {
      setDir(dx > 0 ? 1 : -1, 0);
    } else {
      setDir(0, dy > 0 ? 1 : -1);
    }
    touchStart = null;
  });

  restartBtn.addEventListener("click", init);

  init();
})();
</script>
"""

components.html(GAME_HTML, height=560, scrolling=False)

st.markdown("---")
st.markdown(
    "🎮 **조작법**: 방향키 / WASD (PC), 스와이프 (모바일)  \n"
    "🍎 빨간 먹이를 먹으면 점수가 오르고 몸이 길어져요.  \n"
    "💀 벽이나 자기 몸에 부딪히면 게임 오버!"
)
