"""
ai_analyst.py
A rule-based AI analyst layer. Pulls REAL numbers from retail_db,
detects patterns automatically, writes plain-English business
insights, and saves them into a new MySQL table so they can be
displayed inside the Power BI dashboard.
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

orders = pd.read_sql("SELECT * FROM orders", engine)
orders["order_date"] = pd.to_datetime(orders["order_date"])
order_items = pd.read_sql("SELECT * FROM order_items", engine)
products = pd.read_sql("SELECT * FROM products", engine)

orders_revenue = orders.merge(
    order_items.groupby("order_id")["revenue"].sum().reset_index(),
    on="order_id"
)
orders_revenue["month"] = orders_revenue["order_date"].dt.to_period("M").astype(str)

product_revenue = order_items.merge(products, on="product_id")


def analyze_monthly_trend():
    monthly = orders_revenue.groupby("month")["revenue"].sum().sort_index()
    if len(monthly) < 2:
        return "Not enough months of data to detect a trend."

    last = monthly.iloc[-1]
    prev = monthly.iloc[-2]
    change_pct = ((last - prev) / prev) * 100
    best_month = monthly.idxmax()
    worst_month = monthly.idxmin()

    direction = "increased" if change_pct > 0 else "decreased"
    insight = (
        f"Revenue {direction} by {abs(change_pct):.1f}% in the most recent month "
        f"({monthly.index[-1]}: ₹{last:,.0f}) compared to the previous month "
        f"({monthly.index[-2]}: ₹{prev:,.0f}). "
        f"The strongest month overall was {best_month} (₹{monthly[best_month]:,.0f}), "
        f"and the weakest was {worst_month} (₹{monthly[worst_month]:,.0f}). "
    )

    if change_pct < -10:
        insight += "Recommendation: Investigate the recent decline — check if it aligns with fewer orders, higher returns, or seasonal dips."
    elif change_pct > 10:
        insight += "Recommendation: Recent growth is strong — consider increasing inventory for top products to avoid stockouts."

    return insight


def analyze_categories():
    cat_revenue = product_revenue.groupby("category")["revenue"].sum().sort_values(ascending=False)
    top_cat = cat_revenue.index[0]
    bottom_cat = cat_revenue.index[-1]
    top_share = (cat_revenue.iloc[0] / cat_revenue.sum()) * 100

    insight = (
        f"{top_cat} is the leading category, generating ₹{cat_revenue.iloc[0]:,.0f} "
        f"({top_share:.1f}% of total revenue). "
        f"{bottom_cat} is the weakest category at ₹{cat_revenue.iloc[-1]:,.0f}. "
    )

    if top_share > 30:
        insight += f"Recommendation: Revenue is heavily concentrated in {top_cat} — consider whether this is a risk if demand shifts, and whether {bottom_cat} needs a marketing push."

    return insight


def analyze_products():
    prod_stats = product_revenue.groupby("product_name").agg(
        revenue=("revenue", "sum"),
        units=("quantity", "sum")
    ).reset_index()

    top_product = prod_stats.sort_values("revenue", ascending=False).iloc[0]
    slow_products = prod_stats.sort_values("units", ascending=True).head(5)

    insight = (
        f"Your top-performing product is '{top_product['product_name']}', generating "
        f"₹{top_product['revenue']:,.0f} from {int(top_product['units'])} units sold. "
        f"The 5 slowest-moving products by units sold: "
    )
    insight += ", ".join(
        f"{row['product_name']} ({int(row['units'])} units)" for _, row in slow_products.iterrows()
    )
    insight += ". Recommendation: Consider discounting or discontinuing these slow movers to free up inventory budget for top performers."

    return insight


def analyze_regions():
    region_revenue = order_items.merge(orders, on="order_id").merge(
        pd.read_sql("SELECT * FROM stores", engine), on="store_id"
    ).groupby("region")["revenue"].sum().sort_values(ascending=False)

    top_region = region_revenue.index[0]
    bottom_region = region_revenue.index[-1]
    gap_pct = ((region_revenue.iloc[0] - region_revenue.iloc[-1]) / region_revenue.iloc[-1]) * 100

    insight = (
        f"{top_region} is the top-performing region (₹{region_revenue.iloc[0]:,.0f}), "
        f"outperforming {bottom_region} (₹{region_revenue.iloc[-1]:,.0f}) by {gap_pct:.0f}%. "
        f"Recommendation: Investigate what's working in {top_region} — store count, local demand, or marketing — "
        f"and consider applying those learnings to {bottom_region}."
    )
    return insight


def save_insights_to_db():
    insights_data = [
        ("Revenue Trend", analyze_monthly_trend()),
        ("Category Performance", analyze_categories()),
        ("Product Performance", analyze_products()),
        ("Regional Performance", analyze_regions()),
    ]

    insights_df = pd.DataFrame(insights_data, columns=["insight_type", "insight_text"])
    insights_df.to_sql("ai_insights", engine, if_exists="replace", index=False)
    print("✅ Saved AI insights to 'ai_insights' table in retail_db")
    print(insights_df)


if __name__ == "__main__":
    save_insights_to_db()
    