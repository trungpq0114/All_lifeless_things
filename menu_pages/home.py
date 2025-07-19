import streamlit as st
from page_setup import *
import pandas as pd
import plotly.graph_objects as go
from streamlit_echarts import st_echarts
from functions.dataset import get_commit_activity, get_airflow_stats, get_airflow_dagrun

def show_home():
    st.set_page_config(layout='wide')
    # Layout hai cột chính cho toàn bộ nội dung bên dưới heatmap
    col_left, col_right = st.columns([3, 1])
    with col_left:
        # Thông tin cá nhân
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
    with col_right:
        st.markdown("## 🛠️ Kỹ năng chính")
        st.markdown("""
        - Excel, GG sheet, SQL
        - Python, Mysql, ETL
        - Data Visualization
        - Business Analysis
        - AI Agent
        - Datamart
        """)
        st.markdown("---")
        st.markdown("## 🎓 Học vấn")
        st.markdown("""
        **Đại học Ngoại thương**  <br>
        Khoa Kinh tế Quốc tế  <br>
        Xếp loại: Bằng giỏi
        """, unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("## 🌐 Ngôn ngữ")
        st.markdown("""
        **Tiếng Anh**  <br>
        TOEIC 690
        """, unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("## 🎯 Sở thích")
        hobbies = [
            ("📚", "Đọc sách"),
            ("🏃", "Chạy bộ"),
            ("🌏", "Du lịch"),
            ("📷", "Chụp ảnh")
        ]
        cols = st.columns(2)
        for idx, (icon, hobby) in enumerate(hobbies):
            with cols[idx % 2]:
                st.markdown(
                    f"""
                    <div style='display:flex; align-items:center; margin-bottom:12px;'>
                        <span style='font-size:32px; margin-right:10px;'>{icon}</span>
                        <span style='font-size:18px;'>{hobby}</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
    with col_left:
        st.markdown("---")
        df = get_commit_activity()
        # Chỉ lấy các repo có ít nhất 1 commit
        repo_commit = df.groupby('repo_name')['total'].sum()
        valid_repos = repo_commit[repo_commit > 0].index.tolist()
        repo_options = ['Tất cả'] + valid_repos
        repo_descriptions = {
            "Tất cả": "Ít quá :D mà mình chưa hiểu được sao API Github trả về ít vậy. Nhưng trên hết, mời bạn đến với Portfolio của mình!",
            "All_lifeless_things": "Chính là dự án tạo ra trang web này, nơi mình lưu trữ các dự án và thông tin cá nhân."
            "bạn có thể xem mã nguồn tại <a href='https://github.com/trungpq0114/All_lifeless_things'>đây</a>.",
            "repo2": "Mô tả repo 2",
            # Thêm các repo khác ở đây
        }

        col_repo, col_main = st.columns([2, 10])
        with col_repo:
            repo = st.selectbox("Repositories", repo_options)
            st.markdown(repo_descriptions.get(repo, "Không có mô tả cho repo này."), unsafe_allow_html=True)
        if repo == 'Tất cả':
            df_repo = df[df['repo_name'].isin(valid_repos)].copy()
        else:
            df_repo = df[df['repo_name'] == repo].copy()
        df_repo['week_dt'] = pd.to_datetime(df_repo['week'], unit='s')
        df_repo['week_label'] = df_repo['week_dt'].dt.strftime('%Y-%U')
        days = ['day_0', 'day_1', 'day_2', 'day_3', 'day_4', 'day_5', 'day_6']
        week_day = df_repo.groupby('week_label')[days].sum().T
        week_day.index = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
        # Tạo text cho tooltip
        text = []
        for i, day in enumerate(week_day.index):
            row = []
            for j, week in enumerate(week_day.columns):
                row.append(f"Tuần: {week}<br>Ngày: {day}<br>Commits: {week_day.iloc[i, j]}")
            text.append(row)
        # Chuẩn bị dữ liệu cho ECharts heatmap
        x_labels = list(week_day.columns)
        y_labels = list(week_day.index)
        data = []
        for y_idx, y in enumerate(y_labels):
            for x_idx, x in enumerate(x_labels):
                value = int(week_day.loc[y, x])  # Đảm bảo là int
                data.append([x_idx, y_idx, value])
        # Tính toán chiều cao phù hợp để ô gần vuông
        cell_size = 20  # px, bạn có thể điều chỉnh
        chart_height = max(160, cell_size * len(y_labels))
        option = {
            "tooltip": {
                "position": 'top'
            },
            "grid": {"show": True, "bottom": '12%',"top": '10%', "left": '10%', "right": '1%', "containLabel": False, "borderWidth": 5},
            "xAxis": {
                "type": 'category',
                "data": x_labels,
                "splitArea": {"show": True}
            },
            "yAxis": {
                "type": 'category',
                "data": y_labels,
                "splitArea": {"show": True}
            },
            "visualMap": {
                "show": False,
                "min": int(week_day.values.min()),
                "max": int(week_day.values.max()),
                "calculable": True,
                "color": ["#232877", "#2A3C96", "#364DAA", "#6786E9", '#F1F5FF']
            },
            "series": [{
                "name": 'Commits',
                "type": 'heatmap',
                "data": data,
                "label": {"show": False},
                "emphasis": {"itemStyle": {"shadowBlur": 10, "shadowColor": 'rgba(0, 0, 0, 0.5)'}},
                "itemStyle": {
                    "borderColor": "#333",
                    "borderWidth": 2
                }
            }]
        }
        with col_main:
            st_echarts(option, height=f"{chart_height}px")

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
        # Dự án tiêu biểu
        with st.container():
            st.markdown("## 🚀 Dự án tiêu biểu")
            st.markdown("""
            <div style='border:1px solid #eee; border-radius:8px; padding:16px; margin-bottom:16px;'>
            <h4>Hệ thống dashboard cho công ty Ecom</h4>
            <ul>
            <li><b>Mô tả:</b> Xây dựng hệ thống Dashboard doanh thu, chi phí, tồn kho cho công ty với các tính năng cơ bản gồm phân quyền theo tài khoản, chi nhánh, team.</li>
            <li><b>Công nghệ:</b> Python, Pandas, SQL, Streamlit</li>
            <li><b>Kết quả:</b> Hỗ trợ team MKT ra quyết định nhanh hơn, số liệu chính xác hơn, giảm bớt được 80% nhân viên kế toán tổng hợp với chi phí vận hành thấp.</li>
            </ul>
            </div>
            """, unsafe_allow_html=True)
            # Hệ thống ETL + thống kê Airflow 7 ngày gần nhất
            st.markdown("""
            <div style='border:1px solid #eee; border-radius:8px; padding:16px; margin-bottom:16px;'>
            <h4>Hệ thống ETL</h4>
            <ul>
            <li><b>Mô tả:</b> Hệ thống ETL đồng bộ đơn hàng tự các nền tảng POS Pancake, Facebook Ads, Tiktok Ads.</li>
            <li><b>Công nghệ:</b> Python, Airflow, DBT, Mysql</li>
            <li><b>Kết quả:</b> Tự động hóa 100% các công việc đồng bộ đơn hàng. Cập nhật dữ liệu mới nhất mỗi 5 phút.</li>
            </ul>
            <div style='margin-top:16px;'><b>Thống kê Airflow 7 ngày gần nhất:</b></div>
            """, unsafe_allow_html=True)
            stats = get_airflow_stats()
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Số DAG đã chạy", f"{stats['num_dags']}")
            c2.metric("Số DAG run", f"{stats['num_runs']}")
            c3.metric("Số lượng DAG lỗi", f"{stats['num_failed']}")
            avg_min = round(stats['avg_duration']/60, 2) if stats['avg_duration'] else 0
            c4.metric("Thời gian chạy 1 DAG TB", f"{avg_min} phút")
            df_dag = get_airflow_dagrun()
            dag_median = df_dag.groupby('dag_id')['duration'].median().sort_values(ascending=True)
            fig = go.Figure(go.Bar(
                y=dag_median.index,
                x=dag_median.values / 60,  # chuyển sang phút
                orientation='h',
                marker_color='#636EFA',
                text=[f"{v/60:.2f}" for v in dag_median.values],
                textposition='outside',
            ))
            fig.update_layout(
                yaxis_title='DAG',
                xaxis_title='',
                xaxis=dict(showticklabels=False, visible=False),
                height=350,
                margin=dict(l=10, r=10, t=10, b=10),  # giảm margin-top
            )
            fig.update_traces(textfont_size=12, textangle=0, cliponaxis=False)
            fig.update_yaxes(tickfont_size=12, title_font_size=14)
            fig.update_xaxes(tickfont_size=12, title_font_size=14)
            max_len = dag_median.index.str.len().max()
            st.markdown(f"""
                <div style='margin-bottom:5px; margin-left: {max_len*8}px; margin-top:0;'>
                    <span style='font-size:26px; font-weight:700; color:#636EFA;'>Trung vị <b>thời gian chạy của DAG</b></span>
                </div>
                <div style='margin-bottom:0px; margin-left: {max_len*8}px; margin-top:-8px;'>
                    <span style='font-size:16px; color:#ffffff;'>trên Airflow trong 7 ngày qua. (phút)</span>
                </div>
            """, unsafe_allow_html=True)
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            st.markdown("""
            </div>
            """, unsafe_allow_html=True)
            st.markdown("""
            <div style='border:1px solid #eee; border-radius:8px; padding:16px; margin-bottom:16px;'>
            <h4>Webapp cá nhân hóa</h4>
            <ul>
            <li><b>Mô tả:</b> Blog cá nhân deploy trên Server cá nhân, theo dõi kết quả công việc.</li>
            <li><b>Công nghệ:</b> Python, Service, Ngrok</li>
            <li><b>Kết quả:</b> Lưu profile cá nhân và theo dõi các dashboard cá nhân (Github, số lượng DAG, ...).</li>
            </ul>
            </div>
            """, unsafe_allow_html=True)