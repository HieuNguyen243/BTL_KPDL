import sys
import pandas as pd
from FP_growth import create_tree, mine_fp_tree

# Ép terminal hiển thị tiếng Việt để tránh lỗi charmap
sys.stdout.reconfigure(encoding='utf-8')

def main():
    print("1. Đang nạp và làm sạch dữ liệu...")
    try:
        df_sales = pd.read_csv("sales_202603191558.csv")
        df_products = pd.read_csv("products_202603191559.csv")
    except FileNotFoundError:
        print("LỖI: Không tìm thấy file CSV. Hãy đảm bảo 2 file CSV nằm cùng thư mục với BTL.py")
        return

    # Tiền xử lý Sales
    df_sales['order_date'] = pd.to_datetime(df_sales['order_date'])
    sales_cols = ['order_number', 'order_date', 'product_key', 'quantity']
    df_sales_clean = df_sales[df_sales['quantity'] > 0][sales_cols].copy()

    # Tiền xử lý Products & Tính Biên Lợi Nhuận
    df_products_clean = df_products[['product_key', 'product_name', 'category', 'unit_cost_usd', 'unit_price_usd']].copy()
    df_products_clean['profit_margin'] = (df_products_clean['unit_price_usd'] - df_products_clean['unit_cost_usd']) / df_products_clean['unit_price_usd']

    # Tích hợp dữ liệu
    df_merged = pd.merge(df_sales_clean, df_products_clean, on='product_key', how='inner')

    print("2. Đang phân tích Tốc độ bán hàng để tìm 'Sản phẩm ế'...")
    product_stats = df_merged.groupby('product_name').agg(
        total_sold=('quantity', 'sum'),
        first_sold_date=('order_date', 'min'),
        last_sold_date=('order_date', 'max')
    ).reset_index()

    product_stats['days_active'] = (product_stats['last_sold_date'] - product_stats['first_sold_date']).dt.days + 1
    product_stats['sales_per_day'] = product_stats['total_sold'] / product_stats['days_active']
    product_stats = pd.merge(product_stats, df_products_clean[['product_name', 'profit_margin']].drop_duplicates(), on='product_name', how='inner')

    # Thiết lập ngưỡng và gắn nhãn mục tiêu
    velocity_threshold = product_stats['sales_per_day'].quantile(0.15)
    margin_threshold = 0.40 
    
    product_stats['is_target_combo'] = (product_stats['sales_per_day'] <= velocity_threshold) & (product_stats['profit_margin'] >= margin_threshold)
    
    target_products_set = set(product_stats[product_stats['is_target_combo']]['product_name'].tolist())
    print(f"-> Tìm thấy {len(target_products_set)} sản phẩm bán chậm có lợi nhuận cao (>= 40%).")

    print("3. Đang chuyển đổi dữ liệu sang dạng Giỏ hàng (Transactions)...")
    transactions_series = df_merged.groupby('order_number')['product_name'].apply(list)
    dataset = transactions_series.tolist()
    print(f"-> Đã tạo xong {len(dataset)} giỏ hàng.")

    print("4. Khởi chạy thuật toán FP-Growth...")
    # Thiết lập min_support thấp (ví dụ: cần xuất hiện ít nhất 2 lần)
    MIN_SUP = 2
    MAX_LEN = 3
    
    print(f"-> Dựng cây FP-Tree với min_support = {MIN_SUP}...")
    fp_tree, header_table = create_tree(dataset, min_support=MIN_SUP)

    frequent_itemsets = []
    if fp_tree is not None:
        print(f"-> Khai phá tập phổ biến (giới hạn độ dài max_len = {MAX_LEN})...")
        mine_fp_tree(fp_tree, header_table, MIN_SUP, set([]), frequent_itemsets, max_len=MAX_LEN)
    
    print(f"-> Thuật toán hoàn tất! Tổng cộng tạo ra {len(frequent_itemsets)} tập phổ biến.")

    print("\n5. LỌC KẾT QUẢ: Các tập phổ biến CHỨA SẢN PHẨM Ế để làm Combo:")
    # Lọc ra các tập phổ biến có ít nhất 2 sản phẩm VÀ chứa ít nhất 1 sản phẩm ế
    combo_candidates = [
        itemset for itemset in frequent_itemsets 
        if len(itemset) >= 2 and not set(itemset).isdisjoint(target_products_set)
    ]

    if len(combo_candidates) > 0:
        print(f"-> TÌM THẤY {len(combo_candidates)} COMBO TIỀM NĂNG!")
        # In ra 10 combo đầu tiên để kiểm tra
        for i, combo in enumerate(combo_candidates[:10], 1):
            print(f"   Combo {i}: {list(combo)}")
        if len(combo_candidates) > 10:
            print("   ... (còn tiếp)")
    else:
        print("-> Không tìm thấy tổ hợp nào chứa sản phẩm ế đạt đủ mức min_support.")
        print("-> Gợi ý: Thử giảm MIN_SUP xuống thấp hơn (ví dụ: 3 hoặc 2).")

if __name__ == "__main__":
    main()