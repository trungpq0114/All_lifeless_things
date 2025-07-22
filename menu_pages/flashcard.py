import streamlit as st
from page_setup import *
import pandas as pd
import plotly.graph_objects as go
from streamlit_echarts import st_echarts
from functions.dataset import get_commit_activity, get_airflow_stats, get_airflow_dagrun
import mysql.connector
from streamlit_shortcuts import shortcut_button, add_shortcuts

def show_flashcard():
    st.set_page_config(layout='wide')
    st.title("Flashcard")

    st.markdown("""
        <div style='background: #f1f5f9; border-radius: 8px; padding: 16px 24px; border-left: 4px solid #3b82f6; margin-bottom: 18px;'>
            <h3 style='margin: 0; color: #2563eb;'>Chọn chủ đề tiếng Anh</h3>
        </div>
    """, unsafe_allow_html=True)

    topics = [
        "Từ vựng giao tiếp hàng ngày",
        "Từ vựng công sở",
        "Từ vựng du lịch",
        "Từ vựng học thuật",
        "Từ vựng công nghệ",
        "Từ vựng kinh doanh"
    ]
    selected_topic = st.pills("Chủ đề", topics, selection_mode = 'single')

    flashcard_modes = ["Hiện nghĩa", "Chọn nghĩa"]
    selected_mode = st.radio("Chế độ flashcard", flashcard_modes, horizontal=True)
    conn = mysql.connector.connect(
        host=st.secrets["database_airflow"]["host"],
        user=st.secrets["database_airflow"]["username"],
        password=st.secrets["database_airflow"]["password"],
        database=st.secrets["database_airflow"]["database"]
    )
    # Lấy danh sách flashcard theo chủ đề (giả sử có cột deck/topic trong bảng flashcards)
    # Nếu chưa có cột deck/topic, bạn cần thêm vào hoặc ánh xạ chủ đề sang từ/cụm từ
    query = """
        SELECT * FROM flashcard.flashcards
        WHERE definition_lang = 'vi' AND term IS NOT NULL
    """
    df = pd.read_sql(query, conn)
    if df.empty:
        st.warning("Không có flashcard cho chủ đề này.")
        return
    # Khởi tạo session_state cho flashcard thứ tự và random hóa chỉ 1 lần
    if 'flashcard_order' not in st.session_state:
        st.session_state.flashcard_order = df.sample(frac=1).index.tolist()
        st.session_state.flashcard_idx = 0
    num_cards = len(st.session_state.flashcard_order)
    st.session_state.flashcard_idx = max(0, min(st.session_state.flashcard_idx, num_cards - 1))
    if 'show_definition' not in st.session_state:
        st.session_state.show_definition = False
    if 'mcq_selected' not in st.session_state:
        st.session_state.mcq_selected = None
    # Nút chuyển flashcard căn giữa
    col_left, col_prev, col_center, col_next, col_right = st.columns([2,2,2,2,1])
    with col_prev:
        if shortcut_button("⬅️ Trước", "arrowleft"):
            if st.session_state.flashcard_idx > 0:
                st.session_state.flashcard_idx -= 1
                st.session_state.show_definition = False
                st.session_state.mcq_selected = None
            else:
                st.warning("Đây là flashcard đầu tiên.")
            st.rerun()
    with col_center:
        if selected_mode == "Hiện nghĩa":
            if shortcut_button("Hiện nghĩa 💡", "arrowup") and not st.session_state.show_definition:
                st.session_state.show_definition = True
                st.rerun()
        else:
            if shortcut_button("Làm lại câu hỏi", "arrowup"):
                st.session_state.mcq_selected = None
                st.rerun()
    with col_next:
        if shortcut_button("Tiếp ➡️", "arrowright"):
            if st.session_state.flashcard_idx < num_cards - 1:
                st.session_state.flashcard_idx += 1
                st.session_state.show_definition = False
                st.session_state.mcq_selected = None
            else:
                st.warning("Đây là flashcard cuối cùng.")
            st.rerun()
    # Hiển thị flashcard hiện tại
    card_idx = st.session_state.flashcard_order[st.session_state.flashcard_idx]
    card = df.iloc[card_idx]
    ex_query = f"SELECT * FROM flashcard.flashcard_examples WHERE flashcard_id = {card['id']} ORDER BY example_order"
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
    audio_id = f"audio-{card['id']}"
    audio_btn = ""
    if card['audio_url']:
        audio_btn = f'''<button class="audio-btn" onclick="document.getElementById('{audio_id}').play()" aria-label="Play pronunciation">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor" aria-hidden="true">
            <path d="M3 10v4h4l5 5V5L7 10H3zm13.5 2c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.74 2.5-2.26 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z"></path>
          </svg>
        </button><audio id="{audio_id}" src="{card['audio_url']}"></audio>'''

    # Chế độ chọn nghĩa (MCQ)
    if selected_mode == "Chọn nghĩa":
        # Lấy 3 nghĩa sai ngẫu nhiên
        wrong_defs = df[df['id'] != card['id']]['definition'].dropna().sample(n=3, replace=False).tolist()
        options = wrong_defs + [card['definition']]
        import random
        random.shuffle(options)
        st.markdown(f"""
        <div class='flashcard-center'>
          <div class='flashcard'>
            <div class='flashcard-content'>
              <div>
                <span class='term'>{card['term']}</span>
                <span class='pos'>({card['part_of_speech'] or ''})</span>
                <span class='phonetic'>{card['phonetic'] or ''}</span>
                {audio_btn}
              </div>
              <div class='section-title'>Chọn nghĩa đúng:</div>
        """, unsafe_allow_html=True)
        for i, opt in enumerate(options):
            btn_label = f"{chr(65+i)}. {opt}"
            if st.session_state.mcq_selected is None:
                if st.button(btn_label, key=f"mcq_{i}"):
                    st.session_state.mcq_selected = opt
                    st.rerun()
            else:
                # Đã chọn đáp án
                if opt == card['definition']:
                    st.markdown(f"<div style='background:#d1fae5;color:#065f46;padding:8px;border-radius:6px;margin-bottom:4px;'>{btn_label} ✅</div>", unsafe_allow_html=True)
                elif opt == st.session_state.mcq_selected:
                    st.markdown(f"<div style='background:#fee2e2;color:#991b1b;padding:8px;border-radius:6px;margin-bottom:4px;'>{btn_label} ❌</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div style='background:#f3f4f6;color:#222;padding:8px;border-radius:6px;margin-bottom:4px;'>{btn_label}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='section-title'>Ví dụ:</div>{examples_html}", unsafe_allow_html=True)
        if card['image_url']:
            st.markdown(f"<img class='flashcard-image' src='{card['image_url']}' alt='Hình minh hoạ từ {card['term']}' />", unsafe_allow_html=True)
        st.markdown("</div></div></div>", unsafe_allow_html=True)
    else:
        # Card HTML với nghĩa ẩn/hiện
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
          max-width: 740px;
          align-items: flex-start;
          gap: 24px;
          border: 1px solid var(--fc-border, #e5e7eb);
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
              <div>{card['definition'] if st.session_state.show_definition else '<i style="color:gray">(Nhấn nút để hiện nghĩa)</i>'}</div>
              <div class='section-title'>Ví dụ:</div>
              {examples_html}
            </div>
            {f"<img class='flashcard-image' src='{card['image_url']}' alt='Hình minh hoạ từ {card['term']}' />" if card['image_url'] else ''}
          </div>
        </div>
        """
        st.markdown(card_html, unsafe_allow_html=True);



        