import streamlit as st
import streamlit_authenticator as stauth
from page_setup import *
from PIL import Image
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go


def show_home():
    # Hai cột chính cho layout
    col_left, col_right = st.columns([3, 1])
    with col_left:
        # Ảnh đại diện và thông tin cá nhân
        with st.container():
            col1, col2 = st.columns([1, 3])
            with col1:
                st.image('https://avatars.githubusercontent.com/u/84620703?s=400&u=1e3fc050834b12d4cbf23908b107d9ed4232c5d5&v=4', width=250)
            with col2:
                st.markdown("""
                <h1 style='margin-bottom:0;'>Phạm Quang Trung</h1>
                <h4 style='margin-top:0;color:gray;'>Data Analyst</h4>
                <p>📍 Hà Nội, Việt Nam  <br>
                📧 trungpq.0114@gmail.com  <br>
                ☎️ 0123 456 789  <br>
                <a href='https://www.linkedin.com/in/trungpham0114/'>LinkedIn</a> | <a href='https://github.com/trungpq0114'>GitHub</a></p>
                """, unsafe_allow_html=True)
        st.markdown("---")

        # Học vấn
        st.markdown("## 🎓 Học vấn")
        st.markdown("""
        **Đại học Ngoại thương**  <br>
        Khoa Kinh tế quốc tế  <br>
        GPA: 3.2/4.0  <br>
        Xếp loại: Bằng giỏi
        """, unsafe_allow_html=True)
        st.markdown("---")

        # Kinh nghiệm làm việc
        with st.expander("💼 Kinh nghiệm làm việc", expanded=True):
            st.markdown("""
            <div style='margin-bottom:16px;'>
            <b>Team Lead</b> <br>
            GHTK <br>
            <span style='color:gray;'>Feb 2025 - Present · 6 tháng | Hà Nội</span>
            </div>
            <div style='margin-bottom:16px;'>
            <b>Data Analyst</b> <br>
            GHTK <br>
            <span style='color:gray;'>Dec 2022 - Present · 2 năm 8 tháng | Hà Nội</span>
            </div>
            <div style='margin-bottom:16px;'>
            <b>Business Analyst</b> <br>
            Viet Culture Media Corporation <br>
            <span style='color:gray;'>Nov 2021 - Aug 2022 · 10 tháng | Hà Nội (On-site)</span>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("---")

        # Dự án tiêu biểu (làm nổi bật)
        with st.container():
            st.markdown("## 🚀 Dự án tiêu biểu")
            st.markdown("""
            <div style='border:1px solid #eee; border-radius:8px; padding:16px; margin-bottom:16px;'>
            <h4>Hệ thống dự đoán rủi ro tín dụng</h4>
            <ul>
            <li><b>Mô tả:</b> Xây dựng hệ thống machine learning dự đoán khả năng vỡ nợ của khách hàng dựa trên dữ liệu lịch sử tín dụng.</li>
            <li><b>Công nghệ:</b> Python, scikit-learn, pandas, SQL, Streamlit</li>
            <li><b>Kết quả:</b> Giảm 20% tỷ lệ nợ xấu, hỗ trợ ra quyết định tín dụng nhanh hơn.</li>
            </ul>
            </div>
            <div style='border:1px solid #eee; border-radius:8px; padding:16px; margin-bottom:16px;'>
            <h4>Phân tích cảm xúc mạng xã hội</h4>
            <ul>
            <li><b>Mô tả:</b> Thu thập và phân tích dữ liệu Twitter để nhận diện xu hướng dư luận về sản phẩm mới.</li>
            <li><b>Công nghệ:</b> Python, tweepy, nltk, matplotlib</li>
            <li><b>Kết quả:</b> Cung cấp báo cáo realtime cho phòng marketing, giúp điều chỉnh chiến lược truyền thông.</li>
            </ul>
            </div>
            <div style='border:1px solid #eee; border-radius:8px; padding:16px; margin-bottom:16px;'>
            <h4>Dashboard phân tích kinh doanh</h4>
            <ul>
            <li><b>Mô tả:</b> Thiết kế dashboard trực quan hóa dữ liệu bán hàng, tồn kho, lợi nhuận cho ban lãnh đạo.</li>
            <li><b>Công nghệ:</b> Power BI, SQL, Excel</li>
            <li><b>Kết quả:</b> Giúp lãnh đạo nắm bắt nhanh hiệu quả kinh doanh, ra quyết định kịp thời.</li>
            </ul>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("---")

        # --- Thống kê hoạt động cá nhân ---
        st.markdown("## 📊 Thống kê hoạt động cá nhân")

        # Bignumber highlight
        total_hours = 120 + 80 + 60 + 30
        num_projects = 4
        total_lines = 35000
        num_techs = 8
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Tổng giờ code", f"{total_hours}h")
        col2.metric("Số dự án", f"{num_projects}")
        col3.metric("Số dòng code", f"{total_lines:,}")
        col4.metric("Công nghệ sử dụng", f"{num_techs}")

        # Bar chart nằm ngang: số giờ code theo dự án (Plotly)
        project_hours = pd.DataFrame({
            'Dự án': ['Dự đoán tín dụng', 'Phân tích cảm xúc', 'Dashboard kinh doanh', 'Khác'],
            'Giờ code': [120, 80, 60, 30]
        })
        fig = go.Figure(go.Bar(
            x=project_hours['Giờ code'],
            y=project_hours['Dự án'],
            orientation='h',
            marker_color=['#636EFA', '#EF553B', '#00CC96', '#AB63FA']
        ))
        fig.update_layout(
            xaxis_title='Giờ code',
            yaxis_title='Dự án',
            height=300,
            margin=dict(l=10, r=10, t=30, b=10)
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

        # Hiệu ứng nhẹ: animation emoji
        st.markdown("<div style='text-align:center;font-size:30px;margin-top:30px;'>✨ <span style='animation: blinker 1s linear infinite;'>Cảm ơn bạn đã ghé thăm CV!</span> ✨</div>", unsafe_allow_html=True)
        st.markdown("""
        <style>
        @keyframes blinker { 50% { opacity: 0.2; } }
        </style>
        """, unsafe_allow_html=True)

    with col_right:
        # Kỹ năng chính
        st.markdown("## 🛠️ Kỹ năng chính")
        st.markdown("""
        - Excel, SQL, Power BI
        - Python
        - Data Visualization
        - Business Analysis
        - Dashboard, Report Automation
        """)
        st.markdown("---")
        # Ngôn ngữ
        st.markdown("## 🌐 Ngôn ngữ")
        st.markdown("""
        **Tiếng Anh**  <br>
        TOEIC 690
        """, unsafe_allow_html=True)
        st.markdown("---")
        # Sở thích với icon và layout
        st.markdown("## 🎯 Sở thích")
        hobby_cols = st.columns(1)
        hobbies = [
            ("📚", "Đọc sách"),
            ("🏃", "Chạy bộ"),
            ("🌏", "Du lịch"),
            ("📷", "Chụp ảnh")
        ]
        for icon, hobby in hobbies:
            st.markdown(f"<div style='font-size:40px'>{icon}</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='text-align:left'>{hobby}</div>", unsafe_allow_html=True)
        st.markdown("---")
    