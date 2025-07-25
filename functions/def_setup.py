import streamlit as st
import streamlit_authenticator as stauth
from streamlit_authenticator.utilities import *

def setup_page():
    import yaml
    import pandas as pd
    from urllib.parse import quote 
    from sqlalchemy import create_engine
    import streamlit.components.v1 as components
    from yaml.loader import SafeLoader
    path = st.secrets.env.path
    
    with open(path + "/All_lifeless_things/html/google_analytics.html", "r") as f:
        google_analytics_html = f.read()
        components.html(google_analytics_html, height=0)
    with open(path + "/All_lifeless_things/html/style.html", "r") as f:
        style_html = f.read()
    st.markdown(style_html, unsafe_allow_html=True)

    pd.options.display.float_format = '${:,.2f}'.format

    with open(path + '/.secret/config.yaml', 'r', encoding='utf-8') as file:
        config = yaml.load(file, Loader=SafeLoader)

    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days']
    )
    auth_status = st.session_state.get('authentication_status', None)
    if auth_status:
        authenticator.logout("Đăng xuất", "sidebar")
    else:
        tabs = st.tabs(["Đăng nhập", "Đăng ký"])
        with tabs[0]:
            try:
                authenticator.login()
            except Exception as e:
                st.error(e)
            auth_status = st.session_state.get('authentication_status', None)
            if auth_status is False:
                st.error('Username/password is incorrect')
            elif auth_status is None:
                st.warning('Please enter your username and password')
        # Tab 2: Đăng ký tài khoản
        with tabs[1]:
            try:
                (email_of_registered_user,
                    username_of_registered_user,
                    name_of_registered_user) = authenticator.register_user()
                if email_of_registered_user:
                    st.success('User registered successfully')
                    with open(path + '/.secret/config.yaml', 'w', encoding='utf-8') as file:
                        yaml.dump(config, file, default_flow_style=False, allow_unicode=True)
            except stauth.RegisterError as e:
                st.error(e)
    return authenticator

def get_date_info():
    import datetime
    today = datetime.datetime.today().date()
    # --- PREPARE ---
    years = [datetime.datetime.today().year, datetime.datetime.today().year - 1]
    months = list(range(1,13))
    days = list(range(1,32))
    next_year = today.year + 1
    last_year = today.year - 2
    jan_1 = datetime.date(last_year, 1, 1)
    dec_31 = datetime.date(next_year, 12, 31)
    firstday_of_month = today + datetime.timedelta(days=-(today.day-1))
    lastday_of_lastmonth = today + datetime.timedelta(days=-(today.day))
    firstday_of_lastmonth = datetime.date(lastday_of_lastmonth.year, lastday_of_lastmonth.month, 1)
    last_month = datetime.date(lastday_of_lastmonth.year, lastday_of_lastmonth.month, today.day if lastday_of_lastmonth.day >= today.day else lastday_of_lastmonth.day)

    date_dic = {}
    date_dic['today'] = today
    date_dic['tomorrow'] = today + datetime.timedelta(days=1)
    date_dic['three_days_ago'] = today - datetime.timedelta(days=3)
    date_dic['years'] = years
    date_dic['months'] = months
    date_dic['days'] = days
    date_dic['next_year'] = next_year
    date_dic['last_year'] = last_year
    date_dic['jan_1'] = jan_1
    date_dic['dec_31'] = dec_31
    date_dic['firstday_of_month'] = firstday_of_month
    date_dic['lastday_of_lastmonth'] = lastday_of_lastmonth
    date_dic['firstday_of_lastmonth'] = firstday_of_lastmonth
    date_dic['last_month'] = last_month
    return date_dic