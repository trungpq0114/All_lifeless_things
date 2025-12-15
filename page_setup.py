import streamlit as st
def setup_page():
    import json
    path = st.secrets.env.path
    with open(path + "/All_lifeless_things/config_web/config_conn.json") as file:
        config_conn = json.load(file)
    return config_conn