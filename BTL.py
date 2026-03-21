import sys
import pandas as pd
from FP_growth import create_tree, mine_fp_tree, generate_association_rules

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

    print("2. Đang phân tích Tổng sản lượng bán thấp nhất để tìm 'Sản phẩm ế'...")
    product_stats = df_merged.groupby('product_name').agg(
        total_sold=('quantity', 'sum')
    ).reset_index()

    product_stats = pd.merge(product_stats, df_products_clean[['product_name', 'profit_margin']].drop_duplicates(), on='product_name', how='inner')

    # Thiết lập ngưỡng và gắn nhãn mục tiêu
    volume_threshold = product_stats['total_sold'].quantile(0.15)
    margin_threshold = 0.40 
    
    product_stats['is_target_combo'] = (product_stats['total_sold'] <= volume_threshold) & (product_stats['profit_margin'] >= margin_threshold)
    
    target_products_set = set(product_stats[product_stats['is_target_combo']]['product_name'].tolist())
    print(f"-> Tìm thấy {len(target_products_set)} sản phẩm có tổng lượng bán thấp nhất và lợi nhuận cao (>= 40%).")

    print("3. Đang chuyển đổi dữ liệu sang dạng Giỏ hàng (Transactions)...")
    transactions_series = df_merged.groupby('order_number')['product_name'].apply(list)
    dataset = transactions_series.tolist()
    print(f"-> Đã tạo xong {len(dataset)} giỏ hàng.")

    # ... (Phần 1, 2, 3: Đọc file và chuẩn bị 'dataset' giữ nguyên như cũ) ...
    
    print("4. Khởi chạy thuật toán FP-Growth...")
    MIN_SUP = 2
    MAX_LEN = 3
    TOTAL_TRANSACTIONS = len(dataset)
    
    print(f"-> Dựng cây FP-Tree với min_support = {MIN_SUP}...")
    fp_tree, header_table = create_tree(dataset, min_support=MIN_SUP)

    # VẼ CÂY: Hiển thị một phần cây ra màn hình để quan sát (Giới hạn độ sâu 3 tầng)
    if fp_tree is not None:
        print("\n--- CẤU TRÚC CÂY FP-TREE (RÚT GỌN 3 TẦNG) ---")
        fp_tree.display_tree(max_depth=10)
        print("-------------------------------------------\n")

    # SỬA ĐỔI: frequent_itemsets giờ là DICTIONARY
    frequent_itemsets_dict = {}
    
    if fp_tree is not None:
        print(f"-> Khai phá tập phổ biến (giới hạn độ dài max_len = {MAX_LEN})...")
        mine_fp_tree(fp_tree, header_table, MIN_SUP, set([]), frequent_itemsets_dict, max_len=MAX_LEN)
    
    print(f"-> Hoàn tất! Tìm thấy {len(frequent_itemsets_dict)} tập phổ biến.")

    # =========================================================
    # BƯỚC 5: RẼ NHÁNH TOÁN HỌC - SINH 2 BỘ LUẬT ĐỘC LẬP
    # =========================================================
    
    print("\n" + "="*50)
    print(" LUỒNG 1: SẮP XẾP TỐI ƯU GIAN HÀNG (LIÊN KẾT TỰ NHIÊN) ")
    print("="*50)
    # Dùng ngưỡng Confidence cao (VD: 10%) để lọc các tương tác tự nhiên, chắc chắn
    layout_rules = generate_association_rules(frequent_itemsets_dict, TOTAL_TRANSACTIONS, min_confidence=0.1)
    
    # Chỉ lấy các cặp có độ đẩy (Lift) > 1.2
    strong_layout = [r for r in layout_rules if r['lift'] > 1.2]
    strong_layout.sort(key=lambda x: x['lift'], reverse=True)
    
    if strong_layout:
        for i, rule in enumerate(strong_layout[:5], 1):
            ant = " + ".join(rule['antecedent'])
            con = " + ".join(rule['consequent'])
            print(f"[{i}] Cạnh kệ [{ant}] NÊN ĐẶT [{con}]")
            print(f"    ↳ Lift: {rule['lift']:.2f} | Confidence: {rule['confidence']*100:.1f}%")
    else:
        print("Không có quy luật đủ mạnh để tối ưu gian hàng.")

    print("\n" + "="*50)
    print(" LUỒNG 2: THIẾT KẾ COMBO (LIÊN KẾT NHÂN TẠO) ")
    print("="*50)
    # Bước tinh tế: Tạo ra danh sách KEY chứa các tập phổ biến có dính tới hàng ế (để duyệt)
    combo_itemsets_keys = [
        itemset for itemset in frequent_itemsets_dict.keys()
        if not set(itemset).isdisjoint(target_products_set)
    ]
    
    # Sinh luật với ngưỡng Confidence cực thấp (VD: 0.1% = 0.001) để vớt mọi mỏ neo (chim mồi)
    # Lưu ý truyển tử điển gốc frequent_itemsets_dict và keys cần duyệt combo_itemsets_keys
    combo_rules = generate_association_rules(
        frequent_itemsets_dict, 
        TOTAL_TRANSACTIONS, 
        min_confidence=0.001, 
        target_itemsets=combo_itemsets_keys
    )
    
    # Sắp xếp theo Confidence từ cao xuống thấp
    combo_rules.sort(key=lambda x: x['confidence'], reverse=True)

    if combo_rules:
        # Giới hạn in ra 10 combo khả thi nhất
        for i, rule in enumerate(combo_rules[:10], 1):
            ant = " + ".join(rule['antecedent'])
            con = " + ".join(rule['consequent'])
            
            is_ant_target = any(item in target_products_set for item in rule['antecedent'])
            note = "(Mồi bằng đồ ế)" if is_ant_target else "(Khách mua đồ Hot -> Mời mua đồ Ế)"
            
            print(f"[{i}] COMBO {note}: Khách mua [{ant}] => Mời mua [{con}]")
            print(f"    ↳ Tỷ lệ tự nhiên (Conf): {rule['confidence']*100:.2f}% | Lực đẩy gốc (Lift): {rule['lift']:.2f}")
    else:
        print("Không tìm thấy tổ hợp nào có thể dùng làm combo.")
        
if __name__ == "__main__":
   main()