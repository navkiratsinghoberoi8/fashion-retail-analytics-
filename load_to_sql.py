
"""
load_to_sql.py
Reads all 7 CSV files from the 'data' folder and loads them
into a MySQL database called retail_db
"""

import pandas as pd
from sqlalchemy import create_engine


from dotenv import load_dotenv
import os

load_dotenv()

DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_USER = "root"
DB_HOST = "127.0.0.1"
DB_PORT = "3306"
DB_NAME = "retail_db"

engine = create_engine(f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

files_and_tables = {
    "data/customers.csv": "customers",
    "data/products.csv": "products",
    "data/stores.csv": "stores",
    "data/orders.csv": "orders",
    "data/order_items.csv": "order_items",
    "data/inventory.csv": "inventory",
    "data/returns.csv": "returns",
}

for file_path, table_name in files_and_tables.items():
    df = pd.read_csv(file_path)
    df.to_sql(table_name, engine, if_exists="replace", index=False)
    print(f"✅ Loaded {file_path} into table '{table_name}' ({len(df)} rows)")

print("\n🎉 All done! Data loaded into MySQL database: retail_db")