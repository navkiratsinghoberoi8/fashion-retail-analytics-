
"""
analysis.py
Connects to retail_db (MySQL) and pulls data into pandas
for exploration and analysis.
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


customers = pd.read_sql("SELECT * FROM customers", engine)
products = pd.read_sql("SELECT * FROM products", engine)
orders = pd.read_sql("SELECT * FROM orders", engine)
orders["order_date"] = pd.to_datetime(orders["order_date"])
order_items = pd.read_sql("SELECT * FROM order_items", engine)

print("=" * 50)
print("BASIC DATA OVERVIEW")
print("=" * 50)

print(f"\nTotal customers: {len(customers)}")
print(f"Total products: {len(products)}")
print(f"Total orders: {len(orders)}")
print(f"Total order line items: {len(order_items)}")

print(f"\nTotal revenue: ₹{order_items['revenue'].sum():,.2f}")
print(f"Average order value: ₹{order_items.groupby('order_id')['revenue'].sum().mean():,.2f}")

print("\nFirst 5 rows of order_items:")
print(order_items.head())


print("\n" + "=" * 50)
print("RFM CUSTOMER SEGMENTATION")
print("=" * 50)


orders_with_revenue = orders.merge(
    order_items.groupby("order_id")["revenue"].sum().reset_index(),
    on="order_id"
)


snapshot_date = orders_with_revenue["order_date"].max()


rfm = orders_with_revenue.groupby("customer_id").agg(
    recency=("order_date", lambda x: (snapshot_date - x.max()).days),
    frequency=("order_id", "count"),
    monetary=("revenue", "sum")
).reset_index()

print(f"\nCalculated RFM for {len(rfm)} customers")
print("\nSample RFM data:")
print(rfm.head())


rfm["r_score"] = pd.qcut(rfm["recency"], 4, labels=[4, 3, 2, 1])
rfm["f_score"] = pd.qcut(rfm["frequency"].rank(method="first"), 4, labels=[1, 2, 3, 4])
rfm["m_score"] = pd.qcut(rfm["monetary"], 4, labels=[1, 2, 3, 4])


rfm["rfm_score"] = rfm["r_score"].astype(str) + rfm["f_score"].astype(str) + rfm["m_score"].astype(str)


def segment_customer(row):
    r, f, m = int(row["r_score"]), int(row["f_score"]), int(row["m_score"])
    if r >= 3 and f >= 3 and m >= 3:
        return "Champions"
    elif r >= 3 and f >= 2:
        return "Loyal Customers"
    elif r >= 3:
        return "New Customers"
    elif r == 2:
        return "At Risk"
    else:
        return "Lost Customers"

rfm["segment"] = rfm.apply(segment_customer, axis=1)

print("\nCustomer count per segment:")
print(rfm["segment"].value_counts())

print("\nRevenue contribution per segment:")
segment_revenue = rfm.groupby("segment")["monetary"].sum().sort_values(ascending=False)
print(segment_revenue.round(2))


rfm.to_csv("data/customer_rfm.csv", index=False)
print("\n✅ Saved customer_rfm.csv to the data folder")