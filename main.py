from page_setup import *
from streamlit_option_menu import option_menu
import streamlit as st
import importlib

# Xóa cache nếu cần
st.cache_resource.clear()

page_dict = {
    "Home": {"module": "menu_pages.home", "func": "show_home", "icon": "house"},
    "Dashboard": {"module": "menu_pages.dashboard", "func": "show_dashboard", "icon": "bar-chart"},
    "Settings": {"module": "menu_pages.settings", "func": "show_settings", "icon": "gear"},
    "Account": {"module": "menu_pages.account", "func": "show_account", "icon": "person"},
}

with st.sidebar:
    selected = option_menu(
        "Hello",
        list(page_dict.keys()),
        icons=[page_dict[k]["icon"] for k in page_dict],
        menu_icon="cast",
        default_index=0
    )

module_name = page_dict[selected]["module"]
func_name = page_dict[selected]["func"]
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