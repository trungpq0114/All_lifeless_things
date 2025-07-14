import streamlit as st
import sqlalchemy as sa
from urllib.parse import quote 
from streamlit_autorefresh import st_autorefresh
from streamlit_echarts import st_echarts
from def_function.def_setup import *
import json
path = st.secrets.env.path
with open(path + "/All_lifeless_things/config_web/config_conn.json") as file:
    config_conn = json.load(file)