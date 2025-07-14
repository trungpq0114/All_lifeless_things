import streamlit as st
import streamlit_authenticator as stauth
from page_setup import *

def show_account(authenticator):
    st.set_page_config(page_title='Tài khoản', page_icon=':bar_chart:', layout='wide', initial_sidebar_state="expanded")
    import yaml
    from yaml.loader import SafeLoader
    with open(path + '/.secret/config.yaml', 'r', encoding='utf-8') as file:
        config = yaml.load(file, Loader=SafeLoader)

    if st.session_state['authentication_status']:
        try:
            if authenticator.reset_password(st.session_state['username']):
                st.success('Password modified successfully')
        except (CredentialsError, ResetError) as e:
            st.error(e)

    try:
        (email_of_registered_user,
            username_of_registered_user,
            name_of_registered_user) = authenticator.register_user()
        if email_of_registered_user:
            st.success('User registered successfully')
    except RegisterError as e:
        st.error(e)

    try:
        (username_of_forgotten_password,
            email_of_forgotten_password,
            new_random_password) = authenticator.forgot_password()
        if username_of_forgotten_password:
            st.success('New password sent securely')
        elif not username_of_forgotten_password:
            st.error('Username not found')
    except ForgotError as e:
        st.error(e)

    try:
        (username_of_forgotten_username,
            email_of_forgotten_username) = authenticator.forgot_username()
        if username_of_forgotten_username:
            st.success('Username sent securely')
        elif not username_of_forgotten_username:
            st.error('Email not found')
    except ForgotError as e:
        st.error(e)

    if st.session_state['authentication_status']:
        try:
            if authenticator.update_user_details(st.session_state['username']):
                st.success('Entry updated successfully')
        except UpdateError as e:
            st.error(e)

    with open(path + '/.secret/config.yaml', 'w', encoding='utf-8') as file:
        yaml.dump(config, file, default_flow_style=False, allow_unicode=True)