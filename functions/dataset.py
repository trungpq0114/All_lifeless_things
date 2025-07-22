import streamlit as st
import pandas as pd
import mysql.connector
import datetime
import json
@st.cache_data
def get_commit_activity():
    conn = mysql.connector.connect(
        host=st.secrets["database_web_account"]["host"],
        user=st.secrets["database_web_account"]["username"],
        password=st.secrets["database_web_account"]["password"],
        database=st.secrets["database_web_account"]["database"]
    )
    one_year_ago = int((datetime.datetime.now() - datetime.timedelta(days=365)).timestamp())
    query = f"""
        SELECT repo_name, week, total, day_0, day_1, day_2, day_3, day_4, day_5, day_6
        FROM commit_activity
        WHERE week >= {one_year_ago}
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df
@st.cache_data
def get_airflow_stats():
    conn = mysql.connector.connect(
        host=st.secrets["database_airflow"]["host"],
        user=st.secrets["database_airflow"]["username"],
        password=st.secrets["database_airflow"]["password"],
        database=st.secrets["database_airflow"]["database"]
    )
    seven_days_ago = (datetime.datetime.now() - datetime.timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')
    query = f"""
        SELECT
            COUNT(DISTINCT dag_id) AS num_dags,
            COUNT(*) AS num_runs,
            SUM(state='failed') AS num_failed,
            AVG(TIMESTAMPDIFF(SECOND, start_date, end_date)) AS avg_duration,
            COUNT(CASE WHEN state='running' THEN 1 END) AS num_running
        FROM dag_run
        WHERE execution_date >= '{seven_days_ago}'
    """
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query)
    stats = cursor.fetchone()
    cursor.close()
    conn.close()
    return stats
@st.cache_data
def get_airflow_dagrun():
    # Biểu đồ phân vị trung vị thời gian chạy một DAG
    conn = mysql.connector.connect(
        host=st.secrets["database_airflow"]["host"],
        user=st.secrets["database_airflow"]["username"],
        password=st.secrets["database_airflow"]["password"],
        database=st.secrets["database_airflow"]["database"]
    )
    query = """
        SELECT concat('D',left(MD5(dag_id), 3), SUBSTRING(dag_id, 4)) dag_id, TIMESTAMPDIFF(SECOND, start_date, end_date) AS duration
        FROM dag_run
        WHERE start_date IS NOT NULL AND end_date IS NOT NULL
            AND execution_date >= DATE_SUB(NOW(), INTERVAL 7 DAY)
    """
    df_dag = pd.read_sql(query, conn)
    conn.close()
    return df_dag
@st.cache_data
def prepare_heatmap_data(df, repo=None):
    if repo:
        df = df[df['repo_name'] == repo]
    # Chuyển week sang dạng datetime nếu muốn
    df['week_dt'] = pd.to_datetime(df['week'], unit='s')
    # Tạo dataframe cho heatmap
    heatmap_data = df[['week_dt', 'day_0', 'day_1', 'day_2', 'day_3', 'day_4', 'day_5', 'day_6']]
    heatmap_data = heatmap_data.set_index('week_dt')
    heatmap_data.columns = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    return heatmap_data