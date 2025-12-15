import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from streamlit_echarts import st_echarts
import mysql.connector

def show_settings(authenticator):
    st.set_page_config(layout='wide')

    if not st.session_state.get('authentication_status'):
        st.warning("Bạn chưa đăng nhập.")
        return

    st.title("Settings")
