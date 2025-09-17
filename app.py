import streamlit as st
import copy, math, random, time
from datetime import datetime

BOARD_SIZE = 5
DEFAULT_SEARCH_DEPTH = 2
INSTANT_WIN_THRESHOLD = 15  # points lead for instant win

st.set_page_config(page_title="Mini-Go AI", page_icon="⚫", layout="wide")

st.markdown(
    """
    <style>
    .turn-banner {
        padding: 10px;
        border-radius: 8px;
        font-weight: bold;
        text-align: center;
        margin-bottom: 12px;
        font-size: 18px;
    }
    .white-turn { background: linear-gradient(90deg, #e8fff5, #d1fae5); color:#065f46; }
    .black-turn { background: linear-gradient(90deg, #eef2ff, #e0e7ff); color:#3730a3; }
    .winner { background: linear-gradient(90deg, #fff7ed, #fde68a); color:#78350f; padding:12px; border-radius:10px; text-align:center; font-weight:bold; font-size:20px; margin:10px 0; }
    .draw { background:#f3f4f6; color:#374151; padding:12px; border-radius:10px; text-align:center; font-weight:bold; font-size:20px; margin:10px 0; }
    </style>
    """,
    unsafe_allow_html=True
)

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
        if board[nr][nc] == color and has_liberty(board,nr,nc,visited): return True
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

def heuristic(board, player="B"):
    opp = "B" if player=="W" else "W"
    return sum(row.count(player) for row in board) - sum(row.count(opp) for row in board)

def minimax(board, depth, alpha, beta, maximizing, player):
    opp = "B" if player=="W" else "W"
    if depth == 0: return heuristic(board, player), None
    best_move = None
    if maximizing:
        max_eval = -math.inf
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                new_b = apply_move(board, r, c, player)
                if not new_b: continue
                eval_val, _ = minimax(new_b, depth-1, alpha, beta, False, player)
                if eval_val > max_eval: max_eval, best_move = eval_val, (r,c)
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
                if eval_val < min_eval: min_eval, best_move = eval_val, (r,c)
                beta = min(beta, eval_val)
                if beta <= alpha: break
        return min_eval, best_move

if "board" not in st.session_state: st.session_state.board = new_board()
if "turn" not in st.session_state: st.session_state.turn = "W"
if "history" not in st.session_state: st.session_state.history = []
if "ai_thinking" not in st.session_state: st.session_state.ai_thinking = False
if "game_over" not in st.session_state: st.session_state.game_over = False
if "forced_winner" not in st.session_state: st.session_state.forced_winner = None

def no_moves_left(board, player):
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if apply_move(board,r,c,player): return False
    return True

def end_game_with_forced_rule():
    roll = random.random()
    st.session_state.forced_winner = "B" if roll < 0.1 else "W"
    st.session_state.game_over = True

def check_instant_win():
    val = heuristic(st.session_state.board,"B")
    if abs(val) >= INSTANT_WIN_THRESHOLD:
        st.session_state.game_over = True
        st.session_state.forced_winner = "B" if val > 0 else "W"

def auto_pass_turn():
    if st.session_state.game_over: return
    cur = st.session_state.turn
    if no_moves_left(st.session_state.board, cur):
        st.session_state.turn = "B" if cur=="W" else "W"
        if no_moves_left(st.session_state.board, st.session_state.turn):
            end_game_with_forced_rule()

def declare_winner():
    if st.session_state.forced_winner:
        if st.session_state.forced_winner == "B":
            st.markdown("<div class='winner'>🏆 Black (AI) wins!</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='winner'>🏆 White (You) win!</div>", unsafe_allow_html=True)
        return
    val = heuristic(st.session_state.board,"B")
    if val > 0: st.markdown(f"<div class='winner'>🏆 Black (AI) wins by {val} stones!</div>", unsafe_allow_html=True)
    elif val < 0: st.markdown(f"<div class='winner'>🏆 White (You) win by {-val} stones!</div>", unsafe_allow_html=True)
    else: st.markdown("<div class='draw'>🤝 It's a draw!</div>", unsafe_allow_html=True)

def projected_winner():
    val = heuristic(st.session_state.board,"B")
    if val > 0: st.info(f"📊 Currently Winning: Black (+{val})")
    elif val < 0: st.info(f"📊 Currently Winning: White (+{-val})")
    else: st.info("📊 Currently Balanced")

def play_human(r,c):
    if st.session_state.turn!="W" or st.session_state.game_over: return
    new_b = apply_move(st.session_state.board,r,c,"W")
    if new_b:
        st.session_state.board = new_b
        st.session_state.history.append(("W",(r,c),datetime.utcnow().isoformat()))
        check_instant_win()
        if not st.session_state.game_over:
            st.session_state.turn = "B"
            auto_pass_turn()

def ai_move(depth):
    if st.session_state.turn!="B" or st.session_state.game_over: return
    st.session_state.ai_thinking = True

    check_instant_win()
    if st.session_state.game_over:
        st.session_state.ai_thinking = False
        return

    start_time = time.time()
    best_val, best_move = None, None

    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            new_b = apply_move(st.session_state.board,r,c,"B")
            if not new_b: continue
            val, _ = minimax(new_b, depth-1, -math.inf, math.inf, False, "B")
            if best_val is None or val > best_val:
                best_val, best_move = val, (r,c)
            if time.time() - start_time > 2:  # cap AI time
                break
        if time.time() - start_time > 2:
            break

    if best_move:
        new_b = apply_move(st.session_state.board,best_move[0],best_move[1],"B")
        if new_b:
            st.session_state.board = new_b
            st.session_state.history.append(("B",best_move,datetime.utcnow().isoformat()))

    check_instant_win()
    st.session_state.turn = "W"
    st.session_state.ai_thinking = False
    auto_pass_turn()

col_board, col_sidebar = st.columns([3,1])

with col_sidebar:
    st.subheader("📊 Advantage Meter")
    val = heuristic(st.session_state.board,"B")
    max_range = BOARD_SIZE*BOARD_SIZE
    pct = int((val + max_range) / (2*max_range) * 100)
    st.markdown(
        f"""
        <div style="height:300px;width:40px;border-radius:8px;overflow:hidden;
        background:linear-gradient(to top,#111 0%,#111 {pct}%,#f9fafb {pct}%,#f9fafb 100%);
        margin:auto"></div>
        <p style="text-align:center;font-weight:bold">⚫ {pct}% | ⚪ {100-pct}%</p>
        """,
        unsafe_allow_html=True
    )
    projected_winner()
    if st.session_state.game_over: declare_winner()
    if st.session_state.game_over:
        if st.button("▶️ Play Again"):
            st.session_state.board = new_board()
            st.session_state.turn = "W"
            st.session_state.history = []
            st.session_state.ai_thinking = False
            st.session_state.game_over = False
            st.session_state.forced_winner = None

with col_board:
    if not st.session_state.game_over:
        if st.session_state.turn=="W":
            st.markdown("<div class='turn-banner white-turn'>⚪ Your Turn</div>",unsafe_allow_html=True)
        elif st.session_state.turn=="B":
            st.markdown("<div class='turn-banner black-turn'>⚫ AI is Thinking...</div>",unsafe_allow_html=True)

    col1,col2 = st.columns([2,1])
    depth = col1.slider("AI Depth",1,4,DEFAULT_SEARCH_DEPTH)
    if col2.button("🔄 Reset"):
        st.session_state.board = new_board()
        st.session_state.turn = "W"
        st.session_state.history = []
        st.session_state.ai_thinking = False
        st.session_state.game_over = False
        st.session_state.forced_winner = None

    for r in range(BOARD_SIZE):
        cols = st.columns(BOARD_SIZE)
        for c in range(BOARD_SIZE):
            cell = st.session_state.board[r][c]
            label = "⚪" if cell=="W" else "⚫" if cell=="B" else "➕"
            if cell=="." and st.session_state.turn=="W" and not st.session_state.game_over:
                if cols[c].button(label,key=f"{r}-{c}"): play_human(r,c)
            else:
                cols[c].button(label,key=f"{r}-{c}",disabled=True)

    if st.session_state.turn=="B" and not st.session_state.ai_thinking and not st.session_state.game_over:
        ai_move(depth)