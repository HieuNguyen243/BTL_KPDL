import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import sys

def setup_matplotlib_style():
    """Thiết lập style và font tiếng Việt cho biểu đồ."""
    try:
        plt.style.use('seaborn-v0_8-whitegrid')
    except OSError:
        plt.style.use('seaborn-whitegrid')
    
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = ['Segoe UI', 'Arial', 'Tahoma', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False 

def load_data_for_basket_analysis(sales_file, products_file):
    """Đọc dữ liệu và lấy thông số Hàng Ế (Mục tiêu)"""
    df_sales = pd.read_csv(sales_file)
    df_products = pd.read_csv(products_file)
    
    df_sales['order_date'] = pd.to_datetime(df_sales['order_date'])
    df_sales_clean = df_sales[df_sales['quantity'] > 0].copy()
    
    df_products_clean = df_products.copy()
    df_products_clean['profit_margin'] = (df_products_clean['unit_price_usd'] - df_products_clean['unit_cost_usd']) / df_products_clean['unit_price_usd']
    
    df_merged = pd.merge(df_sales_clean, df_products_clean, on='product_key', how='inner')
    
    product_stats = df_merged.groupby('product_name').agg(
        total_sold=('quantity', 'sum'),
        first_sold_date=('order_date', 'min'),
        last_sold_date=('order_date', 'max'),
        profit_margin=('profit_margin', 'first')
    ).reset_index()
    
    product_stats['days_active'] = (product_stats['last_sold_date'] - product_stats['first_sold_date']).dt.days + 1
    product_stats['sales_per_day'] = product_stats['total_sold'] / product_stats['days_active']
    
    velocity_threshold = product_stats['sales_per_day'].quantile(0.15)
    margin_threshold = 0.40
    
    product_stats['is_target'] = (product_stats['sales_per_day'] <= velocity_threshold) & (product_stats['profit_margin'] >= margin_threshold)
    
    return df_merged, product_stats

def plot_profit_vs_velocity_painpoint(product_stats):
    """Ý Nghĩa Bài Toán: Lợi Nhận Gắn Bó Mật Thiết Với Hàng Khó Bán"""
    plt.figure(figsize=(12, 7))
    
    sns.regplot(
        x='sales_per_day', y='profit_margin', data=product_stats,
        scatter=False, color='gray', line_kws={'linestyle':'--', 'linewidth':2, 'label': 'Đường xu hướng (Nghịch biến)'}
    )
    
    normal = product_stats[~product_stats['is_target']]
    target = product_stats[product_stats['is_target']]
    
    plt.scatter(normal['sales_per_day'], normal['profit_margin'], color='cadetblue', alpha=0.3, s=40, label='Sản phẩm thường')
    plt.scatter(target['sales_per_day'], target['profit_margin'], color='crimson', edgecolors='darkred', s=90, zorder=5, label='Điểm Mù: Hàng Ế & Lãi Cao')
    
    plt.title('Ý NGHĨA DỮ LIỆU: Nghịch Lý Thanh Khoản và Lợi Nhuận', fontsize=14, fontweight='bold', pad=20)
    plt.xlabel('Tốc độ Bán (Sản phẩm / Ngày)', fontsize=12)
    plt.ylabel('Biên Lợi Nhuận (Profit Margin)', fontsize=12)
    
    margin_thresh = 0.40
    velocity_thresh = product_stats['sales_per_day'].quantile(0.15)
    
    plt.axhline(margin_thresh, color='black', linestyle=':', label='Ngưỡng Lãi 40%')
    plt.axvline(velocity_thresh, color='red', linestyle=':', label='Ngưỡng Bán Chậm')
    
    plt.text(
        product_stats['sales_per_day'].max() * 0.45, margin_thresh + 0.1,
        'Insight Thực Chiến:\nSản phẩm đem lại lãi lớn nhất lại khó tiêu thụ nhất.\nTa bắt buộc dùng Data Mining (FP-Growth)\ntìm "Mặt Hàng Hot" để ghép Combo kéo hàng ế.',
        fontsize=11, color='blue', fontweight='bold',
        bbox=dict(facecolor='ivory', alpha=0.9, edgecolor='gray', boxstyle='round,pad=0.5')
    )
    
    plt.legend()
    plt.tight_layout()

def plot_transaction_length_distribution(df_merged):
    """Khó khăn 1: Độ Thưa Giỏ Hàng"""
    basket_sizes = df_merged.drop_duplicates(subset=['order_number', 'product_name']).groupby('order_number').size()
    
    plt.figure(figsize=(12, 6))
    
    plot_data = basket_sizes.copy()
    plot_data = plot_data.apply(lambda x: str(x) if x < 10 else '10+')
    order = [str(i) for i in range(1, 10)] + ['10+']
    current_vals = plot_data.unique()
    order = [o for o in order if o in current_vals]
    
    ax = sns.countplot(x=plot_data.values, order=order, color='steelblue')
    
    single_item_orders = (basket_sizes == 1).sum()
    total_orders = len(basket_sizes)
    single_item_ratio = single_item_orders / total_orders * 100
    
    plt.title('KHÓ KHĂN 1: Giỏ Hàng Quá Nhỏ (Transaction Sparsity)', fontsize=14, fontweight='bold', pad=20)
    plt.xlabel('Số Sản Phẩm Khác Nhau Trong Mỗi Đơn (Items)', fontsize=12)
    plt.ylabel('Số Lượng Đơn Hàng', fontsize=12)
    
    plt.annotate(
        f'RÀO CẢN BÀI TOÁN:\n{single_item_ratio:.1f}% khách chỉ mua 1 sản phẩm!\nThuật toán Association Rules mặc định\nvô tác dụng trên đống dữ liệu này.',
        xy=(0, single_item_orders*0.95),
        xytext=(max(1, len(order)*0.3), single_item_orders * 0.7),
        arrowprops=dict(facecolor='red', shrink=0.05, width=2, headwidth=8),
        fontsize=11, color='maroon', fontweight='bold',
        bbox=dict(boxstyle="round,pad=0.3", edgecolor="red", facecolor="mistyrose")
    )
    plt.tight_layout()

def plot_long_tail_items(df_merged, product_stats):
    """Khó khăn 2: Đuôi Dài Khốc Liệt"""
    item_freq = df_merged.groupby('product_name')['order_number'].nunique().sort_values(ascending=False).reset_index()
    item_freq.columns = ['product_name', 'transaction_count']
    item_freq = pd.merge(item_freq, product_stats[['product_name', 'is_target']], on='product_name', how='left')
    
    plt.figure(figsize=(14, 6))
    x = np.arange(len(item_freq))
    y = item_freq['transaction_count']
    colors = ['maroon' if is_t else 'lightsteelblue' for is_t in item_freq['is_target']]
    
    plt.bar(x, y, color=colors, width=1.0)
    
    plt.title('KHÓ KHĂN 2: Hiện Tượng "Đuôi Dài" (Long Tail) & Tần Suất Xóa Sổ', fontsize=14, fontweight='bold', pad=20)
    plt.xlabel('Thứ Hạng Sản Phẩm (Bán Chạy Nhất -> Bán Chậm Nhất)', fontsize=12)
    plt.ylabel('Support Base (Số Giỏ Hàng Xuất Hiện)', fontsize=12)
    
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='lightsteelblue', label='Hàng Thường (Đầu Bảng)'),
        Patch(facecolor='maroon', label='Hàng Ế Mục Tiêu (Đuôi Bảng)')
    ]
    plt.legend(handles=legend_elements, loc='upper right')
    
    plt.annotate(
        'Vùng Đầu: Hàng Hot (Dễ Tìm Luật)',
        xy=(max(x)*0.02, max(y)*0.6),
        fontsize=11, color='teal', fontweight='bold'
    )
    
    plt.annotate(
        'Vùng Rủi Ro: Hàng Ế Nằm Sâu Dưới Đáy (Đỏ).\nVì Support rất thấp, nếu không hạ tiêu chuẩn Model\n(Min Confidence) xuống đáy (0.1%),\nFP-Growth sẽ bỏ lỡ hoàn toàn!',
        xy=(max(x)*0.8, max(y)*0.05),
        xytext=(max(x)*0.5, max(y)*0.4),
        arrowprops=dict(facecolor='maroon', shrink=0.05, width=2, headwidth=8),
        fontsize=11, color='maroon', fontweight='bold',
        bbox=dict(boxstyle="round,pad=0.3", edgecolor="maroon", facecolor="mistyrose")
    )
    
    plt.xticks([])
    plt.tight_layout()

def plot_cooccurrence_sparsity(df_merged, product_stats):
    """Khó khăn 3: Hố đen Đồng Xuất Hiện"""
    top_n_hot = 12
    top_n_target = 12
    
    # Lấy mẫu Top Hàng Hot & Top Hàng Ế
    top_hot = df_merged.groupby('product_name')['quantity'].sum().nlargest(top_n_hot).index.tolist()
    top_target = product_stats[product_stats['is_target']].nlargest(top_n_target, 'profit_margin')['product_name'].tolist()
    
    # Gom 2 tập lại
    subset_items = top_hot + top_target
    df_sub = df_merged[df_merged['product_name'].isin(subset_items)]
    
    # Ma trận xuất hiện
    basket = pd.crosstab(df_sub['order_number'], df_sub['product_name']).astype(bool).astype(int)
    co_matrix = basket.T.dot(basket)
    np.fill_diagonal(co_matrix.values, 0)
    
    for item in subset_items:
        if item not in co_matrix.index:
            co_matrix.loc[item] = 0
            co_matrix[item] = 0
            
    co_matrix = co_matrix.loc[subset_items, subset_items]
    
    plt.figure(figsize=(12, 11))
    sns.heatmap(co_matrix, cmap="YlOrRd", annot=True, fmt="d", linewidths=.5, cbar=False)
    
    plt.title('KHÓ KHĂN 3: "Hố Đen" Mua Kèm Giữa Hot & Ế (Product Co-occurrence)', fontsize=14, fontweight='bold', pad=20)
    plt.xlabel('Sản Phẩm', fontsize=12)
    plt.ylabel('Sản Phẩm', fontsize=12)
    
    # Kẻ khung
    plt.axhline(top_n_hot, color='blue', linewidth=3)
    plt.axvline(top_n_hot, color='blue', linewidth=3)
    
    plt.text((top_n_hot/2), (top_n_hot/2), 'Hot + Hot\n(Tương tác Tự Nhiên)', color='maroon', ha='center', va='center', fontweight='bold', alpha=0.3, fontsize=16)
    plt.text(top_n_hot + (top_n_target/2), top_n_hot + (top_n_target/2), 'Ế + Ế\n(Trắng Lưỡng)', color='gray', ha='center', va='center', fontweight='bold', alpha=0.3, fontsize=16)
    
    box_props = dict(facecolor='lightgreen', alpha=0.8, boxstyle='round,pad=0.3')
    plt.text(top_n_hot + (top_n_target/2), (top_n_hot/2), 'VÙNG ĐÍCH NGẮM:\nTương tác Hot rẽ sang Ế\n(Gần như số 0, \nđòi hỏi mồi Lift thấp!)', color='darkgreen', bbox=box_props, ha='center', va='center', fontweight='bold', fontsize=11)

    plt.tight_layout()

if __name__ == "__main__":
    sales_file = "dataset/sales_202603191558.csv"
    products_file = "dataset/products_202603191559.csv"
    
    sys.stdout.reconfigure(encoding='utf-8')
    setup_matplotlib_style()
    
    print("1/ Đang tải và phân tích dữ liệu cho FP-Growth...")
    try:
        df_merged, product_stats = load_data_for_basket_analysis(sales_file, products_file)
        
        print("2/ Hiển thị 4 Phân tích Trực quan Chuyên sâu (Data Insight):")
        # Gọi 4 biểu đồ Professional Data Insight
        plot_profit_vs_velocity_painpoint(product_stats)
        plot_transaction_length_distribution(df_merged)
        plot_long_tail_items(df_merged, product_stats)
        plot_cooccurrence_sparsity(df_merged, product_stats)
        
        print("=> Render Xong! Tắt từng cửa sổ (Hình) để tiếp tục xem hình sau.")
        plt.show()
        
    except FileNotFoundError:
        print(f"\n❌ LỖI: Không tìm thấy file gốc ({sales_file} hoặc {products_file}).")
        print("Chạy script này ngay tại thư mục chứa file csv.")
