from page_setup import *
from streamlit_option_menu import option_menu
import streamlit as st
import importlib

# Xóa cache nếu cần
st.cache_resource.clear()

page_dict = {
    "Home": ("menu_pages.home", "show_home"),
    "Settings": ("menu_pages.settings", "show_settings"),
    "Account": ("menu_pages.account", "show_account"),
}

with st.sidebar:
    selected = option_menu(
        "Hello", 
        list(page_dict.keys()), 
        icons=['house', 'gear', 'person'], 
        menu_icon="cast", 
        default_index=0
    )

module_name, func_name = page_dict[selected]
module = importlib.import_module(module_name)

if selected == "Home":
    # Trang Home không cần xác thực
    getattr(module, func_name)()
else:
    # Các trang khác cần xác thực
    from page_setup import setup_page
    authenticator = setup_page()
    if st.session_state.get('authentication_status'):
        getattr(module, func_name)(authenticator)
    else:
        st.error("Vui lòng đăng nhập để truy cập trang này")