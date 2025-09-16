# app.py
import streamlit as st
import copy, math
from datetime import datetime

# ------------------------
# Config
# ------------------------
BOARD_SIZE = 5
DEFAULT_SEARCH_DEPTH = 2

st.set_page_config(page_title="Mini-Go AI", page_icon="⚫", layout="centered")
st.title("⚫ Mini-Go (5×5) — Alpha-Beta AI")
st.markdown("You play White (⚪). Click an empty cell to place your stone. AI plays Black (⚫).")

# ------------------------
# Game mechanics
# ------------------------
def new_board():
    return [["." for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]

def neighbors(r, c):
    for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
        nr, nc = r+dr, c+dc
        if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
            yield nr, nc

def has_liberty(board, r, c, visited=None):
    if visited is None: visited = set()
    if (r,c) in visited: return False
    visited.add((r,c))
    color = board[r][c]
    for nr, nc in neighbors(r,c):
        if board[nr][nc] == ".": return True
        if board[nr][nc] == color and has_liberty(board,nr,nc,visited):
            return True
    return False

def remove_dead(board, color):
    to_remove = []
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] == color and not has_liberty(board,r,c):
                to_remove.append((r,c))
    for r,c in to_remove: board[r][c] = "."
    return len(to_remove)

def apply_move(board, r, c, player):
    """Return new board if move is valid; otherwise None."""
    if board[r][c] != ".": 
        return None
    new_b = copy.deepcopy(board)
    new_b[r][c] = player
    opp = "B" if player=="W" else "W"
    # remove opponent stones if captured
    remove_dead(new_b, opp)
    # suicide check: if our played stone (or group) has no liberties -> invalid
    if not has_liberty(new_b, r, c):
        return None
    return new_b

# ------------------------
# Heuristic & Alpha-Beta
# ------------------------
def heuristic(board, player):
    """Simple static evaluation: stone difference from player's perspective."""
    opp = "B" if player=="W" else "W"
    return sum(row.count(player) for row in board) - sum(row.count(opp) for row in board)

def minimax(board, depth, alpha, beta, maximizing, player):
    """
    Alpha-Beta: returns (value, best_move).
    `player` is the AI root player (Black in our usage).
    maximizing=True means it's `player`'s move in this node.
    """
    opp = "B" if player=="W" else "W"
    if depth == 0:
        return heuristic(board, player), None

    best_move = None
    if maximizing:
        max_eval = -math.inf
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                new_b = apply_move(board, r, c, player)
                if new_b is None: 
                    continue
                eval_val, _ = minimax(new_b, depth-1, alpha, beta, False, player)
                if eval_val > max_eval:
                    max_eval, best_move = eval_val, (r,c)
                alpha = max(alpha, eval_val)
                if beta <= alpha:
                    break
        return max_eval, best_move
    else:
        min_eval = math.inf
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                new_b = apply_move(board, r, c, opp)
                if new_b is None: 
                    continue
                eval_val, _ = minimax(new_b, depth-1, alpha, beta, True, player)
                if eval_val < min_eval:
                    min_eval, best_move = eval_val, (r,c)
                beta = min(beta, eval_val)
                if beta <= alpha:
                    break
        return min_eval, best_move

# ------------------------
# Session state setup
# ------------------------
if "board" not in st.session_state:
    st.session_state.board = new_board()
if "turn" not in st.session_state:
    st.session_state.turn = "W"  # Human plays White by default
if "history" not in st.session_state:
    st.session_state.history = []
if "ai_thinking" not in st.session_state:
    st.session_state.ai_thinking = False

# ------------------------
# Controls
# ------------------------
col_control, col_info = st.columns([1,2])
with col_control:
    depth = st.slider("AI search depth (higher → stronger but slower)", min_value=1, max_value=4, value=DEFAULT_SEARCH_DEPTH)
    if st.button("🔄 Reset"):
        st.session_state.board = new_board()
        st.session_state.turn = "W"
        st.session_state.history = []
        st.session_state.ai_thinking = False

with col_info:
    st.markdown("**How to play**: Click an empty cell to place a White stone. AI will immediately reply with Black's move.")
    st.markdown("**Note**: This is a simplified Mini-Go (5×5) used for teaching alpha-beta pruning and heuristics.")

# ------------------------
# UI: render board
# ------------------------
board = st.session_state.board
turn = st.session_state.turn

def play_human(r, c):
    # Human is White ("W")
    if st.session_state.turn != "W": 
        return
    new_b = apply_move(st.session_state.board, r, c, "W")
    if new_b is not None:
        st.session_state.history.append(("W", (r,c), datetime.utcnow().isoformat()))
        st.session_state.board = new_b
        st.session_state.turn = "B"

def ai_move():
    st.session_state.ai_thinking = True
    # AI plays Black ("B")
    score, mv = minimax(st.session_state.board, depth=depth, alpha=-math.inf, beta=math.inf, maximizing=True, player="B")
    if mv:
        new_b = apply_move(st.session_state.board, mv[0], mv[1], "B")
        if new_b is not None:
            st.session_state.board = new_b
            st.session_state.history.append(("B", mv, datetime.utcnow().isoformat()))
    st.session_state.turn = "W"
    st.session_state.ai_thinking = False

# draw board as buttons
grid = []
for r in range(BOARD_SIZE):
    cols = st.columns(BOARD_SIZE)
    for c in range(BOARD_SIZE):
        cell = board[r][c]
        if cell == ".":
            # clickable only on player's turn
            if st.session_state.turn == "W":
                if cols[c].button("➕", key=f"{r}-{c}"):
                    play_human(r,c)
            else:
                cols[c].button(" ", key=f"{r}-{c}", disabled=True)
        else:
            label = "⚪" if cell == "W" else "⚫"
            cols[c].button(label, key=f"{r}-{c}", disabled=True)

# If it's AI's turn, let it play
if st.session_state.turn == "B" and not st.session_state.ai_thinking:
    # run ai move (non-blocking in Streamlit context is fine here)
    ai_move()

# ------------------------
# Show small status + history
# ------------------------
st.markdown("")
st.write(f"**Current turn:** {'White (You)' if st.session_state.turn=='W' else 'Black (AI)'}")
if st.session_state.ai_thinking:
    st.info("AI is thinking...")

if st.session_state.history:
    st.markdown("**Move history (latest first)**")
    for who, mv, t in reversed(st.session_state.history[-10:]):
        who_label = "White" if who=="W" else "Black"
        st.write(f"- {who_label} played at {mv}  —  {t}")

# ------------------------
# Simple end-of-game suggestion: allow evaluating the static score
# ------------------------
if st.button("Evaluate board (static heuristic for Black)"):
    val = heuristic(st.session_state.board, "B")
    st.success(f"Static heuristic (Black perspective) = {val}  —  (+ means advantage Black)")

st.markdown("---")
st.caption("Simplified Mini-Go rules: no komi, no passes, small-board demo for AI/teaching purposes.")
