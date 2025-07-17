import streamlit as st
from page_setup import *
import pandas as pd
import plotly.graph_objects as go
from streamlit_echarts import st_echarts
from functions.dataset import get_commit_activity, get_airflow_stats, get_airflow_dagrun

def show_dashboard(authenticator):
    st.set_page_config(layout='wide')
    if st.session_state['authentication_status']:
        st.title("Dashboard")