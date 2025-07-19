import streamlit as st
from page_setup import *
import pandas as pd
import plotly.graph_objects as go
from streamlit_echarts import st_echarts
import mysql.connector

def show_dashboard(authenticator):
    st.set_page_config(layout='wide')

    if not st.session_state.get('authentication_status'):
        st.warning("Bạn chưa đăng nhập.")
        return

    st.title("Dashboard Airflow - Gần nhất")

    # --- Date filter setup ---
    import datetime
    now = datetime.datetime.now()
    date_dic = get_date_info()
    date_range = st.sidebar.date_input(
        "Chọn phạm vi ngày",
        (date_dic['three_days_ago'], date_dic['tomorrow']),
        date_dic['jan_1'], date_dic['dec_31']
    )
    # Ensure date_range is a tuple of two dates
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        # If only one date is selected, set start_date to that date and end_date to today
        start_date = date_range
        end_date = date_dic['today']
    # Ensure both are datetime.date (not tuple)
    if isinstance(start_date, tuple):
        start_date = start_date[0]
    if isinstance(end_date, tuple):
        end_date = end_date[0]
    interval_date = (end_date - start_date).days
    # Hiển thị mô tả dữ liệu trong khoảng ngày đã chọn
    st.info(f"Dữ liệu trong {abs(interval_date)+1} ngày từ {start_date.strftime('%d/%m/%Y')} đến {end_date.strftime('%d/%m/%Y')}")

    # --- Database connection ---
    db_conf = st.secrets["database_airflow"]
    conn = mysql.connector.connect(
        host=db_conf["host"],
        user=db_conf["username"],
        password=db_conf["password"],
        database=db_conf["database"]
    )

    from_str = start_date.strftime('%Y-%m-%d %H:%M:%S')
    to_str = end_date.strftime('%Y-%m-%d %H:%M:%S')
    query = f'''
        SELECT dag_id, execution_date, state, TIMESTAMPDIFF(SECOND, start_date, end_date) AS duration
        FROM dag_run
        WHERE start_date IS NOT NULL AND end_date IS NOT NULL
            AND execution_date >= '{from_str}' AND execution_date <= '{to_str}'
    '''
    df = pd.read_sql(query, conn)
    conn.close()

    # --- Filter by dag_id ---
    dag_ids = sorted(df['dag_id'].unique()) if not df.empty else []
    selected_dag_ids = st.sidebar.multiselect('Lọc theo DAG', dag_ids, default=[])
    # Nếu không chọn gì thì coi như chọn hết (không filter)
    if selected_dag_ids and len(selected_dag_ids) < len(dag_ids):
        df = df[df['dag_id'].isin(selected_dag_ids)]


    # --- Overview metrics ---
    total_runs = len(df)
    num_success = (df['state'] == 'success').sum()
    num_failed = (df['state'] == 'failed').sum()
    avg_duration = round(df['duration'].mean()/60, 2) if not df.empty else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tổng DAG run", total_runs)
    c2.metric("Thành công", num_success)
    c3.metric("Thất bại", num_failed)
    c4.metric("Thời gian chạy TB (phút)", avg_duration)


    # --- Aggregated summary by dag_id ---
    st.markdown("### Tổng hợp DAG")
    if not df.empty:
        # Lấy trạng thái và thời gian chạy cuối cùng của mỗi dag_id
        df_sorted = df.sort_values(['dag_id', 'execution_date'])
        last_row = df_sorted.groupby('dag_id').tail(1).set_index('dag_id')
        last_state = last_row['state']
        last_duration_min = (last_row['duration'] / 60).round(2)
        last_start_time = last_row['execution_date']

        # Tính ngũ phân vị thời gian chạy cho mỗi dag_id
        def duration_percentiles(x):
            return pd.Series({
                'duration_p10_min': round(x.quantile(0.1)/60, 2),
                'duration_p25_min': round(x.quantile(0.25)/60, 2),
                'duration_p50_min': round(x.quantile(0.5)/60, 2),
                'duration_p75_min': round(x.quantile(0.75)/60, 2),
                'duration_p90_min': round(x.quantile(0.9)/60, 2),
                'duration_p99_min': round(x.quantile(0.99)/60, 2)
            })

        agg = df.groupby('dag_id').agg(
            runs=('dag_id', 'count'),
            avg_duration_min=('duration', lambda x: round(x.mean()/60, 2))
        )
        percentiles = df.groupby('dag_id')['duration'].apply(duration_percentiles).unstack()
        summary = agg.join(percentiles)
        summary['last_state'] = last_state
        # Chuyển trạng thái thành số: success=1, failed=0, các trạng thái khác=None
        def state_to_num(s):
            if s == 'success':
                return 1
            elif s == 'failed':
                return 0
            else:
                return None
        summary['last_state_num'] = last_state.apply(state_to_num)
        summary['last_duration_min'] = last_duration_min
        summary['last_start_time'] = last_start_time.dt.strftime('%Y-%m-%d %H:%M:%S')
        # Tạo cột 5 trạng thái chạy gần đây cho mỗi dag_id
        def recent_states(dag_id):
            rows = df[df['dag_id'] == dag_id].sort_values('execution_date').tail(5)
            return [state_to_num(s) for s in rows['state']]
        summary['recent_states_bar'] = summary.index.map(recent_states)
        summary = summary.reset_index()
        # Tạo cột bar chart cho ngũ phân vị
        summary['duration_percentiles'] = summary.apply(lambda row: [
            row['duration_p10_min'],
            row['duration_p25_min'],
            row['duration_p50_min'],
            row['duration_p75_min'],
            row['duration_p90_min'],
            row['duration_p99_min']
        ], axis=1)
        max_duration = max(summary['last_duration_min'].max(), summary['avg_duration_min'].max(), 1)
        st.data_editor(
            summary[['dag_id', 'runs', 'recent_states_bar', 'last_start_time', 'last_duration_min', 'avg_duration_min', 'duration_percentiles']],
            column_config={
                "dag_id": st.column_config.TextColumn(
                    "Tên DAG",
                    help="Tên DAG ID"
                ),
                "runs": st.column_config.NumberColumn(
                    "Số lần chạy",
                    help="Tổng số lần chạy của DAG"
                ),
                # Bỏ cột last_state_icon
                # Bỏ cột last_state_num
                "recent_states_bar": st.column_config.BarChartColumn(
                    "5 lần gần nhất",
                    help="5 trạng thái chạy gần nhất của DAG: 1=Thành công, 0=Thất bại",
                    y_min=0,
                    y_max=1,
                    ),
                "last_start_time": st.column_config.TextColumn(
                    "Thời gian bắt đầu lần cuối",
                    help="Thời gian bắt đầu chạy gần nhất của DAG"
                ),
                "last_duration_min": st.column_config.ProgressColumn(
                    "Thời gian chạy gần nhất (phút)",
                    help="Thời gian chạy gần nhất của mỗi DAG (phút)",
                    min_value=0,
                    max_value=max_duration,
                    format="%f phút"
                ),
                "avg_duration_min": st.column_config.ProgressColumn(
                    "Thời gian chạy trung bình (phút)",
                    help="Thời gian chạy trung bình của mỗi DAG (phút)",
                    min_value=0,
                    max_value=max_duration,
                    format="%f phút"
                ),
                "duration_percentiles": st.column_config.BarChartColumn(
                    "Ngũ phân vị thời gian chạy (phút)",
                    help="[P10, P25, P50, P75, P90, P99] thời gian chạy (phút)",
                    y_min=0,
                    y_max=max(summary['duration_p99_min'].max(), 1),
                    )
            },
            hide_index=True,
            height=30*len(summary)
        )
    else:
        st.info("Không có dữ liệu để tổng hợp.")

    # --- Detailed table ---
    if selected_dag_ids and len(selected_dag_ids) < len(dag_ids):
        st.markdown("### Bảng chi tiết DAG run theo filter DAG ID")
        st.dataframe(df[['dag_id', 'execution_date', 'state', 'duration']])