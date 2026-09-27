

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
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

sns.set_style("whitegrid")


orders = pd.read_sql("SELECT * FROM orders", engine)
orders["order_date"] = pd.to_datetime(orders["order_date"])
order_items = pd.read_sql("SELECT * FROM order_items", engine)
products = pd.read_sql("SELECT * FROM products", engine)
customers = pd.read_sql("SELECT * FROM customers", engine)
rfm = pd.read_csv("data/customer_rfm.csv")

product_revenue = order_items.merge(products, on="product_id")

orders_revenue = orders.merge(
    order_items.groupby("order_id")["revenue"].sum().reset_index(),
    on="order_id"
)
orders_revenue["month"] = orders_revenue["order_date"].dt.to_period("M").astype(str)

# ---------- Calculate KPIs ----------
total_revenue = order_items["revenue"].sum()
total_orders = orders["order_id"].nunique()
total_customers = customers["customer_id"].nunique()
avg_order_value = order_items.groupby("order_id")["revenue"].sum().mean()


fig = plt.figure(figsize=(18, 12))
fig.suptitle("FASHION RETAIL INTELLIGENCE DASHBOARD", fontsize=22, fontweight="bold", y=0.98)

gs = fig.add_gridspec(3, 2, height_ratios=[0.4, 1, 1], hspace=0.5, wspace=0.3)


kpi_ax = fig.add_subplot(gs[0, :])
kpi_ax.axis("off")

kpis = [
    ("Total Revenue", f"₹{total_revenue:,.0f}"),
    ("Total Orders", f"{total_orders:,}"),
    ("Total Customers", f"{total_customers:,}"),
    ("Avg Order Value", f"₹{avg_order_value:,.0f}"),
]

for i, (label, value) in enumerate(kpis):
    x = 0.02 + i * 0.25
    kpi_ax.text(x, 0.6, value, fontsize=24, fontweight="bold", color="#2E4057", transform=kpi_ax.transAxes)
    kpi_ax.text(x, 0.15, label, fontsize=12, color="#666666", transform=kpi_ax.transAxes)

# Chart 1
ax1 = fig.add_subplot(gs[1, 0])
monthly_revenue = orders_revenue.groupby("month")["revenue"].sum()
ax1.plot(monthly_revenue.index, monthly_revenue.values, marker="o", linewidth=2, color="#2E86AB")
ax1.set_title("Monthly Revenue Trend", fontsize=13, fontweight="bold")
ax1.tick_params(axis="x", rotation=45, labelsize=8)
ax1.set_ylabel("Revenue (₹)")

# Chart 2

ax2 = fig.add_subplot(gs[1, 1])
category_revenue = product_revenue.groupby("category")["revenue"].sum().sort_values(ascending=False)
sns.barplot(x=category_revenue.index, y=category_revenue.values, ax=ax2, palette="rocket")
ax2.set_title("Revenue by Category", fontsize=13, fontweight="bold")
ax2.tick_params(axis="x", rotation=30, labelsize=8)
ax2.set_ylabel("Revenue (₹)")
ax2.set_xlabel("")
#chart 3

ax3 = fig.add_subplot(gs[2, 0])
top_products = product_revenue.groupby("product_name")["revenue"].sum().sort_values(ascending=False).head(10)
sns.barplot(x=top_products.values, y=top_products.index, ax=ax3, palette="mako")
ax3.set_title("Top 10 Products by Revenue", fontsize=13, fontweight="bold")
ax3.set_xlabel("Revenue (₹)")

# chart 4
ax4 = fig.add_subplot(gs[2, 1])
segment_revenue = rfm.groupby("segment")["monetary"].sum().sort_values(ascending=False)
sns.barplot(x=segment_revenue.values, y=segment_revenue.index, ax=ax4, palette="viridis")
ax4.set_title("Revenue by Customer Segment", fontsize=13, fontweight="bold")
ax4.set_xlabel("Revenue (₹)")

plt.savefig("dashboard.png", dpi=150, bbox_inches="tight", facecolor="white")
plt.close()
print("✅ Saved dashboard.png — open it to see your full dashboard!")