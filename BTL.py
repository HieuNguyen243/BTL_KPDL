import pandas as pd
from sqlalchemy import create_engine
import urllib
from FP_growth import mine_fp_tree, find_prefix_path, create_tree

server = '45.124.94.158,1433'
database = 'xomdata_dataset'
username = 'nguyenngocanh2695'
password = 'do%evA4U1x'
driver = '{ODBC Driver 17 for SQL Server}'

try:
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       
    params = urllib.parse.quote_plus(f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}')
    engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")
    
    print("Dang ket noi toi server qua SQLAlchemy...")
    sale_query = "SELECT * FROM retails.sales" 
    product_query = "SELECT * FROM retails.products"
    
    df_sales = pd.read_sql(sale_query, engine)
    df_products = pd.read_sql(product_query, engine)
    # df_sales = pd.read_csv("sales_202603191558.csv")
    # df_products = pd.read_csv("products_202603191559.csv")
    if not df_sales.empty:
        print("Ket noi va lay du lieu THANH CONG!")
        df_sales['order_date'] = pd.to_datetime(df_sales['order_date'])

        # 1. & 2. LÀM SẠCH VÀ TÍNH BIÊN LỢI NHUẬN (Như cũ)
        sales_cols = ['order_number', 'order_date', 'product_key', 'quantity'] # Lấy thêm order_date
        df_sales_clean = df_sales[df_sales['quantity'] > 0][sales_cols].copy()
        df_products_clean = df_products[['product_key', 'product_name', 'category', 'unit_cost_usd', 'unit_price_usd']].copy()
        df_products_clean['profit_margin'] = (df_products_clean['unit_price_usd'] - df_products_clean['unit_cost_usd']) / df_products_clean['unit_price_usd']

        # 3. TÍCH HỢP & TÍNH TỐC ĐỘ BÁN HÀNG (MỚI)
        df_merged = pd.merge(df_sales_clean, df_products_clean, on='product_key', how='inner')

        # Tính tổng số lượng và số ngày đã bán cho từng sản phẩm
        product_stats = df_merged.groupby('product_name').agg(
            total_sold=('quantity', 'sum'),
            first_sold_date=('order_date', 'min'),
            last_sold_date=('order_date', 'max')
        ).reset_index()

        # Tính số ngày vòng đời của sản phẩm (cộng thêm 1 để tránh chia cho 0 nếu chỉ bán trong 1 ngày)
        product_stats['days_active'] = (product_stats['last_sold_date'] - product_stats['first_sold_date']).dt.days + 1

        # Tính Tốc độ bán (Sales Velocity) = Tổng lượng bán / Số ngày
        product_stats['sales_per_day'] = product_stats['total_sold'] / product_stats['days_active']

        # Ghép thêm thông tin lợi nhuận
        product_stats = pd.merge(product_stats, df_products_clean[['product_name', 'profit_margin']].drop_duplicates(), on='product_name', how='inner')

        # 4. GẮN NHÃN SẢN PHẨM Ế DỰA TRÊN TỐC ĐỘ BÁN (THAY VÌ TỔNG SỐ LƯỢNG)
        # Lấy 25% sản phẩm có TỐC ĐỘ BÁN CHẬM NHẤT và có Biên lợi nhuận >= 40%
        velocity_threshold = product_stats['sales_per_day'].quantile(0.15)
        margin_threshold = 0.40 

        product_stats['is_target_combo'] = (product_stats['sales_per_day'] <= velocity_threshold) & (product_stats['profit_margin'] >= margin_threshold)

        target_products = product_stats[product_stats['is_target_combo']]
        print(f"San pham e: {len(target_products)}") 
    else:
        print("Ket noi thanh cong nhung bang khong co du lieu.")

except Exception as e:
    print("Connection FAILED!")
    print("Error details:", str(e))