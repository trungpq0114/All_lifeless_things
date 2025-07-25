import streamlit as st
from page_setup import *
import pandas as pd
import plotly.graph_objects as go
from streamlit_echarts import st_echarts
from functions.dataset import get_commit_activity, get_airflow_stats, get_airflow_dagrun
import mysql.connector
from streamlit_shortcuts import shortcut_button, add_shortcuts
import random

# -------------------- HELPER --------------------
def _reset_per_card_state(ss, flashcard_modes):
    ss.selected_mode = random.choice(flashcard_modes)
    ss.show_definition = False
    ss.mcq_selected = None
    ss.mcq_is_correct = None
    ss.mcq_options = None
    ss.text_input_answer = None
    ss.current_card_id = None
    ss.auto_next = False
    ss.clear_input_flag = True   # dọn input cho mode Nhập từ

def render_flashcard(card, examples_html, audio_btn, show_definition=False):
    """
    A reusable function to render the flashcard HTML structure for both 'Nhớ nghĩa' and 'Chọn nghĩa'.
    """
    card_html = f"""
    <style>
    .flashcard-center {{
      display: flex;
      justify-content: center;
      align-items: center;
      width: 100%;
      min-height: 340px;
      margin-top: 24px;
      margin-bottom: 24px;
    }}
    .flashcard {{
      background: var(--fc-bg, #fff);
      color: var(--fc-text, #222);
      border-radius: 8px;
      box-shadow: 0 2px 6px rgba(0,0,0,0.08);
      display: flex;
      padding: 24px;
      width: 740px;
      height: 340px;
      align-items: flex-start;
      gap: 24px;
      border: 1px solid var(--fc-border, #e5e7eb);
      box-sizing: border-box;
    }}
    .flashcard-content {{ flex: 1 1 0%; }}
    .term {{ font-size:24px;font-weight:700; }}
    .pos {{ font-size:18px;font-weight:400;margin-left:6px; }}
    .phonetic {{ font-size:18px;font-style:italic;margin-left:4px; }}
    .audio-btn {{ width:24px;height:24px;border:none;background:none;cursor:pointer;vertical-align:middle;margin-left:4px;padding:0; }}
    .section-title {{ font-weight:700;margin-top:16px; }}
    ul {{ margin:0 0 0 20px;padding:0; }}
    .flashcard-image {{ width:180px;height:120px;border-radius:4px;object-fit:cover; }}
    @media (prefers-color-scheme: dark) {{
      .flashcard {{
        --fc-bg: #22272e;
        --fc-text: #f3f5f7;
        --fc-border: #444c56;
      }}
      .flashcard-content, .term, .pos, .phonetic, .section-title {{ color: #f3f5f7 !important; }}
    }}
    </style>
    <div class='flashcard-center'>
      <div class='flashcard'>
        <div class='flashcard-content'>
          <div>
            <span class='term'>{card['term']}</span>
            <span class='pos'>({card['part_of_speech'] or ''})</span>
            <span class='phonetic'>{card['phonetic'] or ''}</span>
            {audio_btn}
          </div>
          <div class='section-title'>Định nghĩa:</div>
          <div>{card['definition'] if show_definition else '<i style="color:gray">(Nhấn nút để Nhớ nghĩa)</i>'}</div>
          <div class='section-title'>Ví dụ:</div>
          {examples_html}
        </div>
        {f"<img class='flashcard-image' src='{card['image_url']}' alt='Hình minh hoạ từ {card['term']}' />" if card['image_url'] else ''}
      </div>
    </div>
    """
    return card_html
def show_flashcard():
    import time

    ss = st.session_state

    # -------------------- PAGE & TITLE --------------------
    st.set_page_config(layout='wide')
    st.title("Flashcard")

    # -------------------- TOPICS (placeholder) --------------------
    topics = [
        "Từ vựng giao tiếp hàng ngày",
        "Từ vựng công sở",
        "Từ vựng du lịch",
        "Từ vựng học thuật",
        "Từ vựng công nghệ",
        "Từ vựng kinh doanh"
    ]
    selected_topic = st.pills("Chủ đề", topics, selection_mode='single')  # hiện tại chưa lọc DB theo topic

    # -------------------- INIT SESSION STATE --------------------
    flashcard_modes = ["Nhớ nghĩa", "Chọn nghĩa", "Nhập từ"]
    ss.setdefault('selected_mode', random.choice(flashcard_modes))
    ss.setdefault('show_definition', False)
    ss.setdefault('mcq_selected', None)
    ss.setdefault('mcq_is_correct', None)
    ss.setdefault('mcq_options', None)
    ss.setdefault('mcq_correct', None)
    ss.setdefault('current_card_id', None)
    ss.setdefault('auto_next', False)
    ss.setdefault('skip_cards', set())         # chứa id các thẻ không hiển thị lại
    ss.setdefault('clear_input_flag', False)   # flag xóa input ở mode Nhập từ

    # -------------------- DB CONNECTION --------------------
    conn = mysql.connector.connect(
        host=st.secrets["database_airflow"]["host"],
        user=st.secrets["database_airflow"]["username"],
        password=st.secrets["database_airflow"]["password"],
        database=st.secrets["database_airflow"]["database"]
    )

    query = """
        SELECT * FROM flashcard.flashcards
        WHERE definition_lang = 'vi' AND term IS NOT NULL
    """
    df = pd.read_sql(query, conn)

    if df.empty:
        st.warning("Không có flashcard cho chủ đề này.")
        return

    # -------------------- ORDER / INDEX HANDLING --------------------
    # Dùng danh sách ID thay vì index để tránh lệch khi lọc
    if 'flashcard_order' not in ss:
        ss.flashcard_order = df['id'].sample(frac=1).tolist()
        ss.flashcard_idx = 0

    num_cards_total = len(ss.flashcard_order)

    # Nếu tất cả card đã skip
    remaining_ids = [cid for cid in ss.flashcard_order if cid not in ss.skip_cards]
    if not remaining_ids:
        st.success("Bạn đã học hết tất cả các thẻ! 🎉")
        return

    # Đảm bảo flashcard_idx luôn trỏ tới card chưa skip
    def move_to_next_valid(direction=1):
        # direction: 1 -> next, -1 -> prev
        if not ss.flashcard_order:  # safety
            return
        steps = 0
        while steps < len(ss.flashcard_order):
            ss.flashcard_idx = max(0, min(ss.flashcard_idx, len(ss.flashcard_order) - 1))
            current_id = ss.flashcard_order[ss.flashcard_idx]
            if current_id not in ss.skip_cards:
                break
            ss.flashcard_idx += direction
            steps += 1

    move_to_next_valid(direction=1)

    # Clamp once more
    ss.flashcard_idx = max(0, min(ss.flashcard_idx, len(ss.flashcard_order) - 1))

    # -------------------- NAVIGATION BUTTONS --------------------
    col_left, col_prev, col_center, col_skip, col_next, col_right = st.columns([2, 2, 2, 2.6, 2, 1])

    with col_prev:
        if shortcut_button("⬅️ Trước", "arrowleft", False):
            if ss.flashcard_idx > 0:
                ss.flashcard_idx -= 1
                move_to_next_valid(direction=-1)
            else:
                st.warning("Đây là flashcard đầu tiên.")
            # reset state khi đổi thẻ
            _reset_per_card_state(ss, flashcard_modes)
            st.rerun()

    with col_center:
        if shortcut_button("Đáp án 💡", "arrowup", False) and not ss.show_definition:
            ss.show_definition = True
            st.rerun()

    with col_skip:
        if shortcut_button("🚫 Không hiển thị lại", "ctrl+arrowdown", False):
            current_id = ss.flashcard_order[ss.flashcard_idx]
            ss.skip_cards.add(int(current_id))
            # Chuyển sang thẻ tiếp theo
            ss.flashcard_idx += 1
            move_to_next_valid(direction=1)
            _reset_per_card_state(ss, flashcard_modes)
            st.rerun()

    with col_next:
        if shortcut_button("Tiếp ➡️", "arrowright", False) or ss.auto_next:
            ss.auto_next = False
            ss.flashcard_idx += 1
            move_to_next_valid(direction=1)
            _reset_per_card_state(ss, flashcard_modes)
            st.rerun()

    # -------------------- LOAD CURRENT CARD --------------------
    current_id = ss.flashcard_order[ss.flashcard_idx]
    card = df[df['id'] == current_id].iloc[0]
    card_id = int(card['id'])

    # Examples
    ex_query = f"SELECT * FROM flashcard.flashcard_examples WHERE flashcard_id = {card_id} ORDER BY example_order"
    ex_df = pd.read_sql(ex_query, conn)
    examples_html = ""
    if not ex_df.empty:
        examples_html += "<div style='margin-top:16px;'><b>Câu ví dụ:</b><ul style='padding-left:18px;'>"
        for _, ex in ex_df.iterrows():
            examples_html += f"<li><i>{ex['example_text']}</i>"
            if ex['translation']:
                examples_html += f"<br><span style='color:gray'>{ex['translation']}</span>"
            examples_html += "</li>"
        examples_html += "</ul></div>"

    # Audio
    audio_id = f"audio-{card_id}"
    audio_btn = ""
    if card['audio_url']:
        audio_btn = f'''<button class="audio-btn" onclick="document.getElementById('{audio_id}').play()" aria-label="Play pronunciation">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor" aria-hidden="true">
            <path d="M3 10v4h4l5 5V5L7 10H3zm13.5 2c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.74 2.5-2.26 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-8.77s-2.99-7.86-7-8.77z"></path>
          </svg>
        </button><audio id="{audio_id}" src="{card['audio_url']}"></audio>'''

    # -------------------- RESET MCQ WHEN SWITCH CARD --------------------
    if ss.current_card_id != card_id:
        ss.current_card_id = card_id
        ss.mcq_selected = None
        ss.mcq_is_correct = None
        ss.mcq_options = None
        ss.mcq_correct = card['definition']
        ss.text_input_answer = None
        ss.show_definition = False
        ss.auto_next = False
        ss.clear_input_flag = True   # để dọn input nếu ở mode Nhập từ

        if ss.selected_mode == "Chọn nghĩa":
            wrong_defs = df[df['id'] != card_id]['definition'].dropna().sample(n=3, replace=False).tolist()
            opts = wrong_defs + [card['definition']]
            random.shuffle(opts)
            ss.mcq_options = opts

    # -------------------- RENDER BY MODE --------------------
    mode = ss.selected_mode

    if mode == "Chọn nghĩa":
        st.markdown(
            render_flashcard(card, examples_html, audio_btn, show_definition=False),
            unsafe_allow_html=True
        )

        col_ans = st.columns([1, 3, 1], gap="small")
        with col_ans[1]:
            result_placeholder = st.empty()
            r1c1, r1c2 = st.columns(2, gap="small")
            r2c1, r2c2 = st.columns(2, gap="small")
            btn_cols = [r1c1, r1c2, r2c1, r2c2]

            hotkeys = ["1", "2", "3", "4"]  # phím tắt

            for i, opt in enumerate(ss.mcq_options):
                with btn_cols[i]:
                    if ss.mcq_selected is None:
                        clicked = shortcut_button(
                            f"{hotkeys[i]}. {opt}",
                            hotkeys[i],          # phím tắt
                            False                # không phải primary (tuỳ bạn)
                        )
                    else:
                        # Sau khi chọn rồi thì khóa lại (hiển thị nút thường disabled hoặc chỉ text)
                        clicked = False
                        st.button(f"{hotkeys[i]}. {opt}", disabled=True, use_container_width=True)

                if clicked and ss.mcq_selected is None:
                    ss.mcq_selected = opt
                    ss.mcq_is_correct = (opt == ss.mcq_correct)
                    if ss.mcq_is_correct:
                        result_placeholder.success("Chính xác! 🎉")
                        time.sleep(1.5)
                        ss.auto_next = True
                    else:
                        result_placeholder.error(f"Chưa chính xác. Đáp án đúng là: {ss.mcq_correct}")
                        ss.auto_next = False
                    st.rerun()


    elif mode == "Nhập từ":
        # Clear input BEFORE creating the widget
        ti_key = f"text_input_{card_id}"
        if ss.clear_input_flag:
            ss.pop(ti_key, None)
            ss.clear_input_flag = False

        card_no_term = card.copy()
        card_no_term['term'] = '?' if not ss.show_definition else card['term']
        st.markdown(
            render_flashcard(card_no_term, examples_html, audio_btn, show_definition=True),
            unsafe_allow_html=True
        )

        col_ans = st.columns([1, 3, 1], gap="small")
        with col_ans[1]:
            user_answer = st.text_input("Nhập từ tiếng Anh:", key=ti_key)
            result_placeholder = st.empty()

            if ss.show_definition:
                st.info(f"Đáp án: {card['term']}")

            if user_answer:
                if user_answer.strip().lower() == card['term'].strip().lower():
                    result_placeholder.success("Chính xác! 🎉")
                    # set flag to clear and move next
                    ss.clear_input_flag = True
                    if ss.flashcard_idx < len(ss.flashcard_order) - 1:
                        ss.flashcard_idx += 1
                        move_to_next_valid(direction=1)
                    ss.selected_mode = random.choice(flashcard_modes)
                    ss.current_card_id = None
                    ss.show_definition = False
                    ss.auto_next = False
                    st.rerun()
                else:
                    result_placeholder.error("Chưa chính xác. Hãy thử lại!")
                    ss.text_input_answer = False

    else:  # "Nhớ nghĩa"
        st.markdown(
            render_flashcard(card, examples_html, audio_btn, show_definition=ss.show_definition),
            unsafe_allow_html=True
        )

