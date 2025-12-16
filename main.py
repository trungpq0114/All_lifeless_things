from streamlit_option_menu import option_menu
import streamlit as st
import importlib
import streamlit_authenticator as stauth
from streamlit_authenticator.utilities import *
from streamlit_autorefresh import st_autorefresh

# Xóa cache nếu cần
# st.cache_resource.clear()
page_dict = {
    "Home": {"module": "menu_pages.home", "func": "show_home", "icon": "house", "roles": ["admin", "user", "manager"]},
    "Flashcard": {"module": "menu_pages.flashcard", "func": "show_flashcard", "icon": "bookmark", "roles": ["admin", "user", "manager"]},
    "Dashboard": {"module": "menu_pages.dashboard", "func": "show_dashboard", "icon": "bar-chart", "roles": ["admin", "manager"]},
    "Transaction": {"module": "menu_pages.transaction", "func": "show_transaction", "icon": "bar-chart", "roles": ["admin", "manager"]},
    "Settings": {"module": "menu_pages.settings", "func": "show_settings", "icon": "gear", "roles": ["admin"]},
    "Account": {"module": "menu_pages.account", "func": "show_account", "icon": "person", "roles": ["admin", "user", "manager"]},
    "Test": {"module": "menu_pages.test", "func": "show_test", "icon": "check-square", "roles": ["admin", "user", "manager"]},
}

# Khởi tạo session_state và URL
page_list = list(page_dict.keys())

if "selected_page" not in st.session_state:
    # Lần đầu: lấy từ URL hoặc dùng mặc định
    query_params = st.query_params
    page_from_url = query_params.get("page", "Home")
    st.session_state.selected_page = page_from_url if page_from_url in page_list else "Home"

try:
    default_index = page_list.index(st.session_state.selected_page)
except ValueError:
    default_index = 0

with st.sidebar:
    selected = option_menu(
        "OllEh",
        page_list,
        icons=[page_dict[k]["icon"] for k in page_list],
        menu_icon="cast",
        default_index=default_index
    )
    
    # Cập nhật state nếu user chọn trang khác
    if selected != st.session_state.selected_page:
        st.session_state.selected_page = selected
        st.query_params["page"] = selected
        st.rerun()

module_name = page_dict[selected]["module"]
func_name = page_dict[selected]["func"]
module = importlib.import_module(module_name)

if selected in ["Home", "Flashcard"]:
    # Trang Home và Flashcard không cần xác thực
    getattr(module, func_name)()
else:
    # Các trang khác cần xác thực
    from functions.def_setup import setup_page
    authenticator = setup_page()
    if st.session_state.get('authentication_status'):
        # Kiểm tra role của user
        user_role = st.session_state.get('roles', 'user')
        allowed_roles = page_dict[selected].get("roles", ["admin", "user", "manager"])
        if user_role in allowed_roles:
            getattr(module, func_name)(authenticator)
        else:
            st.error(f"Bạn không có quyền truy cập trang này (role: {user_role})")