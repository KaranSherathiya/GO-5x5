# app.py
import streamlit as st
import copy, math
from datetime import datetime

BOARD_SIZE = 5
DEFAULT_SEARCH_DEPTH = 2

st.set_page_config(page_title="Mini-Go AI", page_icon="⚫", layout="wide")
st.title("⚫ Mini-Go (5×5) — Alpha-Beta AI")

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
    if board[r][c] != ".": return None
    new_b = copy.deepcopy(board)
    new_b[r][c] = player
    opp = "B" if player=="W" else "W"
    remove_dead(new_b, opp)
    if not has_liberty(new_b, r, c): return None
    return new_b

# ------------------------
# Heuristic & Alpha-Beta
# ------------------------
def heuristic(board, player="B"):
    opp = "B" if player=="W" else "W"
    return sum(row.count(player) for row in board) - sum(row.count(opp) for row in board)

def minimax(board, depth, alpha, beta, maximizing, player):
    opp = "B" if player=="W" else "W"
    if depth == 0:
        return heuristic(board, player), None
    best_move = None
    if maximizing:
        max_eval = -math.inf
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                new_b = apply_move(board, r, c, player)
                if not new_b: continue
                eval_val, _ = minimax(new_b, depth-1, alpha, beta, False, player)
                if eval_val > max_eval:
                    max_eval, best_move = eval_val, (r,c)
                alpha = max(alpha, eval_val)
                if beta <= alpha: break
        return max_eval, best_move
    else:
        min_eval = math.inf
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                new_b = apply_move(board, r, c, opp)
                if not new_b: continue
                eval_val, _ = minimax(new_b, depth-1, alpha, beta, True, player)
                if eval_val < min_eval:
                    min_eval, best_move = eval_val, (r,c)
                beta = min(beta, eval_val)
                if beta <= alpha: break
        return min_eval, best_move

# ------------------------
# Session state
# ------------------------
if "board" not in st.session_state: st.session_state.board = new_board()
if "turn" not in st.session_state: st.session_state.turn = "W"
if "history" not in st.session_state: st.session_state.history = []
if "ai_thinking" not in st.session_state: st.session_state.ai_thinking = False
if "game_over" not in st.session_state: st.session_state.game_over = False

# ------------------------
# Game state helpers
# ------------------------
def is_board_full(board):
    return all(cell != "." for row in board for cell in row)

def check_game_over():
    if is_board_full(st.session_state.board):
        st.session_state.game_over = True

def declare_winner():
    val = heuristic(st.session_state.board, "B")
    if val > 0:
        st.success("🏆 Black (AI) wins!")
    elif val < 0:
        st.success("🏆 White (You) win!")
    else:
        st.info("🤝 It's a draw!")

# ------------------------
# Moves
# ------------------------
def play_human(r,c):
    if st.session_state.turn != "W" or st.session_state.game_over: return
    new_b = apply_move(st.session_state.board,r,c,"W")
    if new_b:
        st.session_state.board = new_b
        st.session_state.history.append(("W",(r,c),datetime.utcnow().isoformat()))
        st.session_state.turn = "B"
        check_game_over()

def ai_move(depth):
    if st.session_state.turn != "B" or st.session_state.game_over: return
    st.session_state.ai_thinking = True
    score, mv = minimax(st.session_state.board, depth, -math.inf, math.inf, True, "B")
    if mv:
        new_b = apply_move(st.session_state.board,mv[0],mv[1],"B")
        if new_b:
            st.session_state.board = new_b
            st.session_state.history.append(("B",mv,datetime.utcnow().isoformat()))
    st.session_state.turn = "W"
    st.session_state.ai_thinking = False
    check_game_over()

# ------------------------
# Layout
# ------------------------
col_board, col_sidebar = st.columns([3,1])

with col_sidebar:
    st.subheader("📊 Advantage Meter")
    val = heuristic(st.session_state.board,"B")
    pct = int((val + BOARD_SIZE*BOARD_SIZE) / (2*BOARD_SIZE*BOARD_SIZE) * 100)
    st.progress(pct)
    if val > 0:
        st.write(f"Black Advantage: {val}")
    elif val < 0:
        st.write(f"White Advantage: {-val}")
    else:
        st.write("Balanced")

    if st.session_state.game_over:
        declare_winner()

with col_board:
    # Turn Indicator
    if st.session_state.turn=="W" and not st.session_state.game_over:
        st.markdown("<div style='background:#e6ffe6;padding:8px;border-radius:6px'>⚪ Your Turn</div>",unsafe_allow_html=True)
    elif st.session_state.turn=="B" and not st.session_state.game_over:
        st.markdown("<div style='background:#e6f0ff;padding:8px;border-radius:6px'>⚫ AI is thinking...</div>",unsafe_allow_html=True)

    # Depth selector + reset
    col1,col2 = st.columns([2,1])
    depth = col1.slider("AI depth",1,4,DEFAULT_SEARCH_DEPTH)
    if col2.button("🔄 Reset"):
        st.session_state.board = new_board()
        st.session_state.turn = "W"
        st.session_state.history = []
        st.session_state.ai_thinking = False
        st.session_state.game_over = False

    # Board UI
    for r in range(BOARD_SIZE):
        cols = st.columns(BOARD_SIZE)
        for c in range(BOARD_SIZE):
            cell = st.session_state.board[r][c]
            label = "⚪" if cell=="W" else "⚫" if cell=="B" else "➕"
            if cell=="." and st.session_state.turn=="W" and not st.session_state.game_over:
                if cols[c].button(label,key=f"{r}-{c}"):
                    play_human(r,c)
            else:
                cols[c].button(label,key=f"{r}-{c}",disabled=True)

    # AI move automatically if it's Black's turn
    if st.session_state.turn=="B" and not st.session_state.ai_thinking and not st.session_state.game_over:
        ai_move(depth)
