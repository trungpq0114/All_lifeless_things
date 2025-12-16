import streamlit as st
from functions.def_setup import get_date_info
import pandas as pd
import plotly.graph_objects as go
from streamlit_echarts import st_echarts
import mysql.connector

def show_transaction(authenticator):
    st.set_page_config(layout='wide')

    if not st.session_state.get('authentication_status'):
        st.warning("Bạn chưa đăng nhập.")
        return

    # --- Date filter setup ---
    import datetime
    now = datetime.datetime.now()
    date_dic = get_date_info()
    date_range = st.sidebar.date_input(
        "Chọn phạm vi ngày",
        (date_dic['firstday_of_month'], date_dic['tomorrow']),
        date_dic['jan_1'], date_dic['dec_31']
    )
    # Ensure date_range is a tuple of two dates
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        # If only one date is selected, set start_date to that date and end_date to today
        start_date = date_range
        end_date = date_dic['today']
    # Ensure both are datetime.date (not tuple)
    if isinstance(start_date, tuple):
        start_date = start_date[0]
    if isinstance(end_date, tuple):
        end_date = end_date[0]
    interval_date = (end_date - start_date).days
    # Hiển thị mô tả dữ liệu trong khoảng ngày đã chọn
    # Title section
    st.markdown(
        f"""
        <div style="background: #f1f5f9; border-radius: 8px; padding: 10px 24px; border-left: 5px solid #3b82f6; margin-bottom: 10px;">
            <div style="display: flex; flex-direction: column; gap: 8px;">
                <h5 style="margin: 0; font-size: 2.2rem; font-weight: 700; color: #2563eb; letter-spacing: 1px;">
                    Dashboard Chi tiêu
                </h5>
                <div style="font-size: 1.1rem; color: #222; font-weight: 500;">
                    <b>{abs(interval_date)+1} ngày</b>
                    từ <span style="color:#2563eb">{start_date.strftime('%d/%m/%Y')}</span>
                    đến <span style="color:#2563eb">{end_date.strftime('%d/%m/%Y')}</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # --- Database connection ---
    db_conf = st.secrets["database_transaction"]
    conn = mysql.connector.connect(
        host=db_conf["host"],
        user=db_conf["username"],
        password=db_conf["password"],
        database=db_conf["database"]
    )

    from_str = start_date.strftime('%Y-%m-%d %H:%M:%S')
    to_str = end_date.strftime('%Y-%m-%d %H:%M:%S')
    query = f'''
        SELECT e.id,
            bank_name,
            bank_account,
            reference_number,
            amount,
            currency,
            balance_after,
            transaction_date,
            posted_date,
            coalesce(name, 'Chưa xác định') as category_name,
            transaction_type,
            description,
            note,
            created_at,
            updated_at
        FROM expenses e
        LEFT JOIN categories c ON c.id = e.category_id
        WHERE (e.category_id is null or e.category_id not in (16, 12, 11))
            AND transaction_date >= '{from_str}' AND transaction_date <= '{to_str}'
    '''
    df = pd.read_sql(query, conn)
    conn.close()

    # Define internal transfer categories
    internal_categories = ["Chồng gửi vợ"]  # Loại bỏ "Vợ gửi chồng" vì không cần
    df_external_full = df[~df['category_name'].isin(internal_categories)]
    df_internal = df[df['category_name'].isin(internal_categories)]

    category_names = sorted(df_external_full['category_name'].dropna().unique()) if not df_external_full.empty else []
    selected_category_names = st.sidebar.multiselect('Lọc theo Category', category_names, default=[])
    # Filter df_external if categories selected
    df_external = df_external_full.copy()
    if selected_category_names:
        df_external = df_external[df_external['category_name'].isin(selected_category_names)]

    # --- Overview metrics ---
    total_transactions = len(df)
    total_expense_external = df_external['amount'].sum() if not df_external.empty else 0
    total_internal_husband = df_internal['amount'].sum() if not df_internal.empty else 0
    avg_amount = df['amount'].mean() if not df.empty else 0
    num_income = (df['transaction_type'] == 'income').sum() if not df.empty else 0
    num_expense = (df['transaction_type'] == 'expense').sum() if not df.empty else 0

    # Target chi tiêu trong tháng: 2.000.000 (based on external expenses)
    target_expense = 10000000
    current_month = now.month
    current_year = now.year
    df_external_this_month = df_external_full[(df_external_full['transaction_date'].dt.month == current_month) & (df_external_full['transaction_date'].dt.year == current_year)]
    total_expense_this_month = df_external_this_month['amount'].sum() if not df_external_this_month.empty else 0
    expense_progress = min(total_expense_this_month / target_expense, 1) * 100

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Tổng giao dịch", total_transactions)
    c2.metric("Tổng chi tiêu thực tế", f"{total_expense_external:,.0f}")
    c3.metric("Tổng chồng gửi vợ", f"{total_internal_husband:,.0f}")
    c4.metric("Thu nhập", num_income)
    c5.metric("Chi tiêu", num_expense)

    # Target progress
    st.markdown("### Tiến độ chi tiêu tháng này")
    st.progress(expense_progress / 100)
    st.write(f"Tổng chi tiêu thực tế: {total_expense_this_month:,.0f} / {target_expense:,.0f} ({expense_progress:.1f}%)")

    # --- Charts by category ---
    st.markdown("### Biểu đồ chi tiêu thực tế")
    if not df_external.empty:
        agg = df_external.groupby('category_name').agg(
            transactions=('id', 'count'),
            total_amount=('amount', 'sum'),
            avg_amount=('amount', 'mean')
        ).reset_index()

        # Sort by total_amount ascending (thấp lên cao)
        agg = agg.sort_values('total_amount', ascending=True)

        # Calculate percentage
        total = agg['total_amount'].sum()
        agg['percentage'] = (agg['total_amount'] / total * 100).round(1)

        col1, col2 = st.columns(2)

        # Horizontal bar chart for total amount using Plotly (with optional budgets)
        with col1:
            # Define budgets for specific categories (VND)
            budgets = {
                "Tiền dịch vụ": 1300000,
                "Biếu bố mẹ": 3000000,
                "Đi lại": 2000000,
                "Mua thức ăn": 2000000,
                "Đồ gia dụng": 1000000,
                "Ăn sáng": 1000000,
            }

            # Align budget values with aggregated categories
            budget_values = agg['category_name'].apply(lambda x: budgets.get(x, 0)).tolist()

            fig = go.Figure()

            # Add budget trace (shows only for categories present in the mapping)
            fig.add_trace(go.Bar(
                y=agg['category_name'],
                x=budget_values,
                orientation='h',
                name='Ngân sách',
                marker_color='#EF553B',
                opacity=0.6,
                hovertemplate='%{y}: %{x} VND<extra>Ngân sách</extra>'
            ))

            # Add actual expense trace
            fig.add_trace(go.Bar(
                y=agg['category_name'],
                x=agg['total_amount'],
                orientation='h',
                name='Thực tế',
                marker_color='#636EFA',
                text=agg.apply(lambda row: f"{int(row['total_amount']):,} ({row['percentage']}%)", axis=1),
                textposition='outside',
                hovertemplate='%{y}: %{x} VND (%{customdata}%)<extra>Thực tế</extra>',
                customdata=agg['percentage']
            ))

            fig.update_layout(
                barmode='group',
                yaxis_title='Category',
                xaxis_title='',
                xaxis=dict(showticklabels=False, visible=False),
                height=350,
                margin=dict(l=10, r=10, t=10, b=10),
                bargap=0.2,
                dragmode=False
            )
            fig.update_traces(textfont_size=12, textangle=0, cliponaxis=False)
            fig.update_yaxes(tickfont_size=12, title_font_size=14)
            fig.update_xaxes(tickfont_size=12, title_font_size=14)
            # Format x-axis with big number format
            fig.update_xaxes(
                tickformat=',.0f',
                tickfont_size=11
            )
            st.plotly_chart(fig, config={'displayModeBar': False})

        # Stacked bar chart for daily expenses by category
        with col2:
            df_grouped = df_external.groupby([df_external['transaction_date'].dt.date, 'category_name'])['amount'].sum().reset_index()
            df_grouped.columns = ['date', 'category', 'amount']
            fig_daily = go.Figure()
            for cat in df_grouped['category'].unique():
                cat_data = df_grouped[df_grouped['category'] == cat]
                fig_daily.add_trace(go.Bar(
                    x=cat_data['date'],
                    y=cat_data['amount'],
                    name=cat,
                    hovertemplate='%{x}: %{y} VND<extra>%{fullData.name}</extra>'
                ))
            fig_daily.update_layout(
                barmode='stack',
                xaxis_title="Ngày",
                yaxis_title="Số tiền",
                height=400,
                dragmode=False
            )
            # Format y-axis with big number format and remove gridlines
            fig_daily.update_yaxes(
                tickformat=',.0f',
                showgrid=False,
                tickfont_size=11
            )
            fig_daily.update_xaxes(
                showgrid=False,
                tickfont_size=11
            )
            st.plotly_chart(fig_daily, config={'displayModeBar': False})
    else:
        st.info("Không có dữ liệu chi tiêu thực tế để biểu diễn.")

    # --- Detailed table ---
    st.markdown("### Bảng chi tiết giao dịch")
    df_display = df_external[['id', 'transaction_date', 'category_name', 'amount', 'description', 'note', 'transaction_type']].copy()
    st.dataframe(df_display)

    st.markdown("### Chỉnh sửa giao dịch")

    # Fetch categories for selection
    db_conf = st.secrets["database_transaction"]
    conn2 = mysql.connector.connect(
        host=db_conf["host"],
        user=db_conf["username"],
        password=db_conf["password"],
        database=db_conf["database"]
    )
    cur = conn2.cursor()
    cur.execute("SELECT id, name FROM categories ORDER BY name")
    categories = cur.fetchall()
    cur.close()
    conn2.close()

    category_names_all = [c[1] for c in categories]
    category_name_to_id = {c[1]: c[0] for c in categories}

    # Prepare transaction selection
    if not df_external.empty:
        tx_options = df_external.sort_values('transaction_date', ascending=False).apply(
            lambda r: (int(r['id']), f"{r['id']} | {r['transaction_date'].strftime('%Y-%m-%d')} | {r.get('category_name') or 'None'} | {int(r['amount']):,}"), axis=1
        ).tolist()

        tx_map = {opt[1]: opt[0] for opt in tx_options}
        tx_labels = [opt[1] for opt in tx_options]

        selected_label = st.selectbox('Chọn giao dịch để chỉnh sửa', tx_labels)
        selected_id = tx_map[selected_label]

        selected_row = df_external[df_external['id'] == selected_id].iloc[0]
        current_category = selected_row.get('category_name')
        current_note = selected_row.get('note') if 'note' in selected_row else ''

        # Category select (only existing categories)
        try:
            default_idx = category_names_all.index(current_category) if current_category in category_names_all else 0
        except ValueError:
            default_idx = 0

        new_category = st.selectbox('Category', category_names_all, index=default_idx)
        new_note = st.text_area('Note', value=current_note if pd.notna(current_note) else '')

        if st.button('Cập nhật'):
            # Update expenses table: only category_id and note
            cat_id = category_name_to_id.get(new_category)
            conn3 = mysql.connector.connect(
                host=db_conf["host"],
                user=db_conf["username"],
                password=db_conf["password"],
                database=db_conf["database"]
            )
            cur3 = conn3.cursor()
            if cat_id is not None:
                cur3.execute("UPDATE expenses SET category_id = %s, note = %s, updated_at = NOW() WHERE id = %s", (cat_id, new_note, selected_id))
            else:
                cur3.execute("UPDATE expenses SET note = %s, updated_at = NOW() WHERE id = %s", (new_note, selected_id))
            conn3.commit()
            cur3.close()
            conn3.close()
            st.success('Cập nhật thành công')
            try:
                st.experimental_rerun()
            except AttributeError:
                # Fallback for Streamlit versions without experimental_rerun
                try:
                    from streamlit.runtime.scriptrunner import RerunException
                    raise RerunException()
                except Exception:
                    st.info('Vui lòng làm mới trang để thấy thay đổi.')
    else:
        st.info('Không có giao dịch để chỉnh sửa.')