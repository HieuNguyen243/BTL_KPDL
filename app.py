import streamlit as st
import pandas as pd
from FP_growth import create_tree, mine_fp_tree, generate_association_rules

# ==========================================
# 1. CẤU HÌNH TRANG WEB & SESSION STATE
# ==========================================
st.set_page_config(
    page_title="Data Mining Retail (FP-Growth)",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

if 'df_layout' not in st.session_state:
    st.session_state['df_layout'] = None
if 'df_combo' not in st.session_state:
    st.session_state['df_combo'] = None

st.title("🛒 Ứng dụng Phân tích Giỏ hàng Bán lẻ (FP-Growth)")
st.markdown("Hệ thống khai phá dữ liệu thông minh, giúp tìm ra các quy luật mua sắm của khách hàng nhằm tối ưu không gian kệ hàng và tạo các Combo xúc tiến bán hàng (Giải cứu dọn kho).")

# ==========================================
# 2. GIAO DIỆN THANH BÊN (SIDEBAR)
# ==========================================
with st.sidebar:
    st.header("📁 Dữ liệu đầu vào")
    st.caption("Định dạng bắt buộc: .csv")
    sales_file = st.file_uploader("Tệp Sales (sales.csv)", type=['csv'])
    products_file = st.file_uploader("Tệp Products (products.csv)", type=['csv'])

    st.markdown("---")
    st.header("⚙️ Cấu hình Siêu tham số (Hyperparameters)")
    
    min_sup = st.slider(
        "Min Support (Số lần xuất hiện):", 
        min_value=2, max_value=20, value=5, step=1,
        help="Yêu cầu hệ thống chỉ lấy các tập hợp mặt hàng xuất hiện ít nhất X lần trong toàn bộ Giỏ hàng."
    )

    min_conf_layout = st.slider(
        "Min Conf - Luồng Xếp Kệ:", 
        min_value=0.05, max_value=0.50, value=0.10, step=0.01,
        help="Độ tin cậy tối thiểu cho việc tìm quy luật khách hàng tự nhiên mua kèm các món hàng."
    )

    min_conf_combo = st.slider(
        "Min Conf - Luồng Combo:", 
        min_value=0.001, max_value=0.100, value=0.001, step=0.001, format="%.3f",
        help="Ngưỡng cực thấp (nới lỏng cực hạn) để tìm bất kỳ mối liên hệ dù là nhỏ nhất với các mặt hàng Eế để tạo Combo giải cứu."
    )
    
    st.markdown("---")
    btn_run = st.button("🚀 KHỞI CHẠY THUẬT TOÁN", use_container_width=True, type="primary")


# ==========================================
# 3. HÀM TIỆN ÍCH (HELPER FUNCTIONS)
# ==========================================
def format_rules(rules_list, target_products_set=None):
    """
    Format mảng Dict các luật sinh ra thành DataFrame chuẩn hóa để render Web.
    """
    if not rules_list:
        return pd.DataFrame()
    
    formatted_data = []
    for rule in rules_list:
        ant = " + ".join(rule['antecedent'])
        con = " + ".join(rule['consequent'])
        
        row_data = {
            "Khách mua": ant,
            "Gợi ý mua kèm": con,
            "Confidence (%)": f"{rule['confidence'] * 100:.2f}%", 
            "Lift": round(rule['lift'], 2)
        }
        
        if target_products_set is not None:
            is_ant_target = any(item in target_products_set for item in rule['antecedent'])
            row_data["Chiến lược P/p"] = "Mồi bằng đồ Ế" if is_ant_target else "Khách mua Hot -> Mời thêm đồ Ế"
            
        formatted_data.append(row_data)
    
    return pd.DataFrame(formatted_data)


# ==========================================
# 4. DATA PIPELINE (CHỈ CẬP NHẬT DỮ LIỆU)
# ==========================================
if btn_run:
    if not sales_file or not products_file:
        st.error("⚠️ LỖI VẬN HÀNH: Bạn chưa tải lên đủ 2 file cấu trúc dữ liệu (`sales.csv` và `products.csv`). Vui lòng kiểm tra lại Sidebar bên trái.")
    else:
        with st.status("🛠️ Hệ thống đang thực thi Data Mining...", expanded=True) as status:
            try:
                # BƯỚC 1: Tiền xử lý
                st.write("1/4: Đọc file và hợp nhất Dữ liệu (ETL)...")
                df_sales = pd.read_csv(sales_file)
                df_products = pd.read_csv(products_file)
                
                df_sales['order_date'] = pd.to_datetime(df_sales['order_date'])
                df_sales_clean = df_sales[df_sales['quantity'] > 0][['order_number', 'order_date', 'product_key', 'quantity']]
                
                df_products_clean = df_products[['product_key', 'product_name', 'category', 'unit_cost_usd', 'unit_price_usd']].copy()
                df_products_clean['profit_margin'] = (df_products_clean['unit_price_usd'] - df_products_clean['unit_cost_usd']) / df_products_clean['unit_price_usd']
                
                df_merged = pd.merge(df_sales_clean, df_products_clean, on='product_key', how='inner')
                
                # BƯỚC 2: Hàng Ế
                st.write("2/4: Phân tích Tổng sản lượng bán thấp nhất & Tìm Hàng Tồn (Chậm luân chuyển)...")
                product_stats = df_merged.groupby('product_name').agg(
                    total_sold=('quantity', 'sum')
                ).reset_index()
                
                product_stats = pd.merge(product_stats, df_products_clean[['product_name', 'profit_margin']].drop_duplicates(), on='product_name', how='inner')
                
                volume_threshold = product_stats['total_sold'].quantile(0.15)
                margin_threshold = 0.40 
                
                target_mask = (product_stats['total_sold'] <= volume_threshold) & (product_stats['profit_margin'] >= margin_threshold)
                target_products_set = set(product_stats[target_mask]['product_name'].tolist())
                
                if not target_products_set:
                    st.success("🌟 Tín hiệu tốt: Không có 'Hàng Ế' (Lãi >= 40% mà Tổng sản lượng bán thấp nhất) nào trong kỳ này. Hệ thống sẽ tối ưu bộ nhớ bằng cách tự động bỏ qua Luồng Tìm Combo.")
                
                # BƯỚC 3: Dựng cây FP-Tree
                st.write(f"3/4: Khởi tạo Thuật toán FP-Growth (Min Support = {min_sup}, Max Length = 3)...")
                transactions_series = df_merged.groupby('order_number')['product_name'].apply(list)
                dataset = transactions_series.tolist()
                TOTAL_TRANSACTIONS = len(dataset)
                
                fp_tree, header_table = create_tree(dataset, min_support=min_sup)
                
                frequent_itemsets_dict = {}
                if fp_tree is not None:
                    mine_fp_tree(fp_tree, header_table, min_sup, set([]), frequent_itemsets_dict, max_len=3)
                
                # BƯỚC 4: Rẽ nhánh Bài toán và Lưu SESSION_STATE
                st.write("4/4: Trích xuất Luật Kết Hợp và Lọc nhiễu theo Ngưỡng Confidence...")
                
                layout_rules_raw = generate_association_rules(frequent_itemsets_dict, TOTAL_TRANSACTIONS, min_confidence=min_conf_layout)
                layout_rules = [r for r in layout_rules_raw if r['lift'] > 1.2]
                layout_rules.sort(key=lambda x: x['lift'], reverse=True)
                st.session_state['df_layout'] = format_rules(layout_rules)
                
                if target_products_set:
                    combo_itemsets_keys = [
                        itemset for itemset in frequent_itemsets_dict.keys()
                        if not set(itemset).isdisjoint(target_products_set)
                    ]
                    
                    combo_rules_raw = generate_association_rules(
                        frequent_itemsets_dict, 
                        TOTAL_TRANSACTIONS, 
                        min_confidence=min_conf_combo, 
                        target_itemsets=combo_itemsets_keys
                    )
                    combo_rules_raw.sort(key=lambda x: x['confidence'], reverse=True)
                    st.session_state['df_combo'] = format_rules(combo_rules_raw, target_products_set)
                else:
                    st.session_state['df_combo'] = pd.DataFrame() 

                status.update(label="Tuyệt vời! Kết quả phân tích đã sẵn sàng.", state="complete", expanded=False)
            
            except Exception as e:
                status.update(label="Oops! Quá trình phân tích thất bại.", state="error", expanded=True)
                st.error(f"Chi tiết kỹ thuật (Traceback): {str(e)}")
                st.session_state['df_layout'] = pd.DataFrame()
                st.session_state['df_combo'] = pd.DataFrame()


# ==========================================
# 5. KHỐI HIỂN THỊ KẾT QUẢ ĐỘC LẬP (LẤY TỪ STATE)
# ==========================================
if st.session_state['df_layout'] is not None:
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("📊 Báo cáo Khuyến nghị từ Trí tuệ Nhân tạo")
    
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.info("🏪 CHIẾN LƯỢC 1: TỐI ƯU KHÔNG GIAN KỆ HÀNG", icon="🏬")
        st.caption("Các cụm hàng hóa được thiết lập hoàn toàn dựa trên hành vi Tự nhiên chắc chắn của người mua (Lift > 1.2).")
        df_layout_cache = st.session_state['df_layout']
        if not df_layout_cache.empty:
            search_layout = st.text_input("🔍 Tìm kiếm tên sản phẩm (Xếp Kệ):", key="search_layout")
            if search_layout:
                mask = df_layout_cache['Khách mua'].str.contains(search_layout, case=False, na=False) | \
                       df_layout_cache['Gợi ý mua kèm'].str.contains(search_layout, case=False, na=False)
                df_layout_show = df_layout_cache[mask]
            else:
                df_layout_show = df_layout_cache
            st.dataframe(df_layout_show, use_container_width=True, hide_index=True)
        else:
            st.warning("Không tìm thấy tổ hợp nào thỏa mãn. Xin lưu ý hệ thống đã kích hoạt bộ lọc tự nhiên Lift > 1.2. Mời tinh chỉnh lại tham số Min Support hoặc Min Confidence tại Sidebar.")
            
    with col_right:
        st.success("🎁 CHIẾN LƯỢC 2: THIẾT KẾ COMBO CROSS-SELL", icon="💡")
        st.caption("Các mặt hàng Lãi Lớn (nhưng kẹt kho) được ưu tiên mượn 'Lực đẩy' nhờ mua kèm với các hàng hot đầu vào.")
        df_combo_cache = st.session_state['df_combo']
        if not df_combo_cache.empty:
            search_combo = st.text_input("🔍 Tìm kiếm tên sản phẩm (Combo):", key="search_combo")
            if search_combo:
                mask = df_combo_cache['Khách mua'].str.contains(search_combo, case=False, na=False) | \
                       df_combo_cache['Gợi ý mua kèm'].str.contains(search_combo, case=False, na=False)
                df_combo_show = df_combo_cache[mask]
            else:
                df_combo_show = df_combo_cache
            st.dataframe(df_combo_show, use_container_width=True, hide_index=True)
        else:
            st.warning("Phễu lọc chưa tìm ra được mặt hàng mục tiêu sinh thành nhóm Combo phổ biến nào. Hãy giảm tham số Min Confidence (Combo) sâu hơn nữa!")
    
    st.markdown("---")
    st.caption("💡 **Mẹo:** Bạn có thể tinh chỉnh các Siêu tham số ở bên trái và bấm Khởi chạy lặp lại để so sánh chất lượng luật sinh ra.")
