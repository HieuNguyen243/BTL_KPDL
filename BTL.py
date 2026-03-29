import sys
import pandas as pd
from FP_growth import create_tree, mine_fp_tree, generate_association_rules

sys.stdout.reconfigure(encoding='utf-8')

def main():
    print("1. Đang nạp và làm sạch dữ liệu...")
    try:
        df_sales = pd.read_csv("dataset/sales_202603191558.csv")
        df_products = pd.read_csv("dataset/products_202603191559.csv")
    except FileNotFoundError:
        print("LỖI: Không tìm thấy file CSV. Hãy đảm bảo 2 file CSV nằm trong thư mục 'dataset'")
        return
        
    sales_cols = ['order_number', 'product_key', 'quantity']
    df_sales_clean = df_sales[df_sales['quantity'] > 0][sales_cols].copy()

    df_products_clean = df_products[['product_key', 'product_name', 'subcategory', 'unit_cost_usd', 'unit_price_usd']].copy()
    df_products_clean['profit_margin'] = (df_products_clean['unit_price_usd'] - df_products_clean['unit_cost_usd']) / df_products_clean['unit_price_usd']

    df_merged = pd.merge(df_sales_clean, df_products_clean, on='product_key', how='inner')

    print("2. Đang phân tích Tổng sản lượng bán thấp nhất để tìm 'Sản phẩm ế'...")
    product_stats = df_merged.groupby('product_name').agg(
        total_sold=('quantity', 'sum')
    ).reset_index()

    product_stats = pd.merge(product_stats, df_products_clean[['product_name', 'profit_margin']].drop_duplicates(), on='product_name', how='inner')
    volume_threshold = product_stats['total_sold'].quantile(0.15)
    margin_threshold = 0.40 
    
    product_stats['is_target_combo'] = (product_stats['total_sold'] <= volume_threshold) & (product_stats['profit_margin'] >= margin_threshold)
    
    target_products_set = set(product_stats[product_stats['is_target_combo']]['product_name'].tolist())
    print(f"-> [Debug] Tìm thấy {len(target_products_set)} sản phẩm có tổng lượng bán <= 15% quantile và lợi nhuận >= 40%.")

    # =========================================================
    # LUỒNG 1: SẮP XẾP TỐI ƯU GIAN HÀNG (LIÊN KẾT THEO SUBCATEGORY)
    # =========================================================
    print("\n" + "="*50)
    print(" LUỒNG 1: SẮP XẾP TỐI ƯU GIAN HÀNG (Phân tích theo Subcategory) ")
    print("="*50)
    
    print("-> 1.1 Chuẩn bị dữ liệu 1 (Gom nhóm theo Subcategory)...")
    transactions_subcats = df_merged.groupby('order_number')['subcategory'].apply(lambda x: list(set(x)))
    dataset_flow1 = transactions_subcats.tolist()
    TOTAL_TRANS_1 = len(dataset_flow1)
    
    # Chỉ xét những giỏ có từ 2 danh mục trở lên để debug
    valid_baskets_1 = [t for t in dataset_flow1 if len(t) > 1]
    print(f"-> [Debug] Số giỏ hàng danh mục hợp lệ (>= 2 subcategory): {len(valid_baskets_1)} / {TOTAL_TRANS_1}")

    MIN_SUP_1 = 40
    print(f"-> 1.2 Khởi chạy FP-Growth trên {TOTAL_TRANS_1} giỏ (min_support = {MIN_SUP_1})...")
    fp_tree_1, header_table_1 = create_tree(dataset_flow1, min_support=MIN_SUP_1)
    
    frequent_itemsets_dict_1 = {}
    if fp_tree_1 is not None:
        mine_fp_tree(fp_tree_1, header_table_1, MIN_SUP_1, set([]), frequent_itemsets_dict_1, max_len=2)
        
    pairs_count_1 = sum(1 for k in frequent_itemsets_dict_1.keys() if len(k) > 1)
    print(f"-> [Debug] Số lượng tập phổ biến danh mục có >= 2 thành phần: {pairs_count_1}")

    print("-> 1.3 Sinh luật và lọc theo Lift > 1.2...")
    flow1_rules_raw = generate_association_rules(frequent_itemsets_dict_1, TOTAL_TRANS_1, min_confidence=0.01)
    print(f"-> [Debug] Số luật sinh ra (chưa lọc Lift): {len(flow1_rules_raw)}")
    
    valid_layout_rules = []
    seen_layouts = set()
    print("-> [Debug] Đã áp dụng bộ lọc Khử trùng lặp đối xứng.")
    
    for rule in flow1_rules_raw:
        if rule['lift'] > 1.2:
            combined_items = frozenset(rule['antecedent'] + rule['consequent'])
            
            if combined_items not in seen_layouts:
                seen_layouts.add(combined_items)
                rule['score'] = rule['support'] * rule['lift']
                valid_layout_rules.append(rule)
            
    valid_layout_rules.sort(key=lambda x: x['score'], reverse=True)
    
    if valid_layout_rules:
        print("\n--- TOP 5 GỢI Ý XẾP GIAN HÀNG ---")
        for i, rule in enumerate(valid_layout_rules[:], 1):
            ant = " + ".join(rule['antecedent'])
            con = " + ".join(rule['consequent'])
            print(f"[{i}] Khu vực [{ant}] NÊN ĐẶT CẠNH [{con}]")
            print(f"    ↳ Score: {rule['score']:.4f} | Lift: {rule['lift']:.2f} | Support: {rule['support']*100:.2f}% | Conf: {rule['confidence']*100:.1f}%")
    else:
        print("Không có luật nào thỏa mãn điều kiện tối ưu gian hàng.")

    # =========================================================
    # LUỒNG 2: THIẾT KẾ COMBO BÁN CHÉO (LIÊN KẾT THEO PRODUCT NAME)
    # =========================================================
    print("\n" + "="*50)
    print(" LUỒNG 2: THIẾT KẾ COMBO BÁN CHÉO (Phân tích theo Product Name) ")
    print("="*50)
    
    print("-> 2.1 Chuẩn bị dữ liệu 2 (Gom nhóm theo Product Name)...")
    transactions_products = df_merged.groupby('order_number')['product_name'].apply(lambda x: list(set(x)))
    dataset_flow2 = transactions_products.tolist()
    TOTAL_TRANS_2 = len(dataset_flow2)
    
    valid_baskets_2 = [t for t in dataset_flow2 if len(t) > 1]
    print(f"-> [Debug] Số giỏ hàng sản phẩm hợp lệ (>= 2 sản phẩm): {len(valid_baskets_2)} / {TOTAL_TRANS_2}")

    MIN_SUP_2 = 2
    print(f"-> 2.2 Khởi chạy FP-Growth trên {TOTAL_TRANS_2} giỏ (min_support = {MIN_SUP_2} - Vét cạn)...")
    fp_tree_2, header_table_2 = create_tree(dataset_flow2, min_support=MIN_SUP_2)
    
    frequent_itemsets_dict_2 = {}
    if fp_tree_2 is not None:
        mine_fp_tree(fp_tree_2, header_table_2, MIN_SUP_2, set([]), frequent_itemsets_dict_2, max_len=3)
        
    pairs_count_2 = sum(1 for k in frequent_itemsets_dict_2.keys() if len(k) > 1)
    print(f"-> [Debug] Số lượng tập phổ biến sản phẩm có >= 2 thành phần: {pairs_count_2}")

    print("-> 2.3 Sinh luật (min_confidence = 0.01) và lọc Combo...")
    flow2_rules_raw = generate_association_rules(frequent_itemsets_dict_2, TOTAL_TRANS_2, min_confidence=0.01)
    print(f"-> [Debug] Số luật sinh ra (chưa lọc combo): {len(flow2_rules_raw)}")
    
    valid_combo_rules = []
    for rule in flow2_rules_raw:
        ant_set = set(rule['antecedent'])
        con_set = set(rule['consequent'])
        
       
        cond_ant = ant_set.isdisjoint(target_products_set)
        cond_con = not con_set.isdisjoint(target_products_set)
        cond_lift = rule['lift'] > 1.2
        
        if cond_ant and cond_con and cond_lift:
            rule['combo_score'] = rule['confidence'] * rule['lift']
            valid_combo_rules.append(rule)
            
    valid_combo_rules.sort(key=lambda x: x['combo_score'], reverse=True)
    
    if valid_combo_rules:
        print("\n--- TOP 10 COMBO TIỀM NĂNG NHẤT ---")
        for i, rule in enumerate(valid_combo_rules[:], 1):
            ant = " + ".join(rule['antecedent'])
            con = " + ".join(rule['consequent'])
            print(f"[{i}] COMBO HOT: Khách mua [{ant}] => Khuyến mãi thêm [{con}]")
            print(f"    ↳ Score: {rule['combo_score']:.4f} | Conf: {rule['confidence']*100:.1f}% | Lift: {rule['lift']:.2f}")
    else:
        print("Không tìm ra combo nào đủ mạnh thỏa mãn tiêu chí.")
        
if __name__ == "__main__":
   main()