import pandas as pd
from sqlalchemy import create_engine
import urllib

server = '45.124.94.158,1433'
database = 'xomdata_dataset'
username = 'nguyenngocanh2695'
password = 'do%evA4U1x'
driver = '{ODBC Driver 17 for SQL Server}'

try:
    while                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       
    params = urllib.parse.quote_plus(f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}')
    engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")
    
    print("Dang ket noi toi server qua SQLAlchemy...")
    sale_query = "SELECT TOP 5 * FROM retails.sales" 
    product_query = "SELECT TOP 5 * FROM retails.products"
    
    df_sales = pd.read_sql(sale_query, engine)
    df_products = pd.read_sql(product_query, engine)

    if not df_sales.empty:
        print("Ket noi va lay du lieu THANH CONG!")
        print(df_sales.head())
        print(df_products.head()) 
    else:
        print("Ket noi thanh cong nhung bang khong co du lieu.")

except Exception as e:
    print("Connection FAILED!")
    print("Error details:", str(e))