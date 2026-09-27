
"""
generate_data.py
Creates a synthetic fashion retail dataset:
customers, products, stores, orders, order_items, inventory, returns
Saves everything as CSV files in a /data folder.
"""

import pandas as pd
import numpy as np
from faker import Faker
import random
from datetime import datetime, timedelta
import os

fake = Faker()
Faker.seed(42)
random.seed(42)
np.random.seed(42)


os.makedirs("data", exist_ok=True)


N_CUSTOMERS = 5000
N_PRODUCTS = 500
N_STORES = 15
N_ORDERS = 20000
START_DATE = datetime(2024, 1, 1)
END_DATE = datetime(2026, 9, 1)


customers = pd.DataFrame({
    "customer_id": range(1, N_CUSTOMERS + 1),
    "name": [fake.name() for _ in range(N_CUSTOMERS)],
    "email": [fake.email() for _ in range(N_CUSTOMERS)],
    "gender": np.random.choice(["Male", "Female", "Other"], N_CUSTOMERS, p=[0.47, 0.48, 0.05]),
    "signup_date": [fake.date_between(start_date=START_DATE, end_date=END_DATE) for _ in range(N_CUSTOMERS)],
    "region": np.random.choice(["North", "South", "East", "West"], N_CUSTOMERS),
})
customers.to_csv("data/customers.csv", index=False)


categories = ["Tops", "Bottoms", "Dresses", "Footwear", "Accessories", "Outerwear"]
sizes = ["XS", "S", "M", "L", "XL"]
colors = ["Black", "White", "Blue", "Red", "Green", "Beige", "Grey"]
brands = ["Urban Threads", "Nova Wear", "StrideFit", "LuxeLine", "CasualCo"]

products = pd.DataFrame({
    "product_id": range(1, N_PRODUCTS + 1),
    "product_name": [f"{random.choice(brands)} {random.choice(categories)[:-1]} {i}" for i in range(N_PRODUCTS)],
    "category": np.random.choice(categories, N_PRODUCTS),
    "brand": np.random.choice(brands, N_PRODUCTS),
    "size": np.random.choice(sizes, N_PRODUCTS),
    "color": np.random.choice(colors, N_PRODUCTS),
    "cost_price": np.round(np.random.uniform(5, 60, N_PRODUCTS), 2),
})

products["selling_price"] = np.round(
    products["cost_price"] * np.random.uniform(1.4, 2.2, N_PRODUCTS), 2
)
products.to_csv("data/products.csv", index=False)


stores = pd.DataFrame({
    "store_id": range(1, N_STORES + 1),
    "store_name": [f"Store {i}" for i in range(1, N_STORES + 1)],
    "region": np.random.choice(["North", "South", "East", "West"], N_STORES),
    "channel": np.random.choice(["Online", "In-Store"], N_STORES, p=[0.4, 0.6]),
})
stores.to_csv("data/stores.csv", index=False)


orders_list = []
order_items_list = []
order_item_id = 1

for order_id in range(1, N_ORDERS + 1):
    customer_id = random.randint(1, N_CUSTOMERS)
    store_id = random.randint(1, N_STORES)
    order_date = fake.date_between(start_date=START_DATE, end_date=END_DATE)

    orders_list.append({
        "order_id": order_id,
        "customer_id": customer_id,
        "store_id": store_id,
        "order_date": order_date,
    })

    
    n_items = random.randint(1, 4)
    chosen_products = random.sample(range(1, N_PRODUCTS + 1), n_items)

    for pid in chosen_products:
        product_row = products.loc[products["product_id"] == pid].iloc[0]
        quantity = random.randint(1, 3)
        discount_pct = random.choice([0, 0, 0, 10, 20, 30])  # mostly no discount
        unit_price = product_row["selling_price"]
        final_price = round(unit_price * (1 - discount_pct / 100), 2)

        order_items_list.append({
            "order_item_id": order_item_id,
            "order_id": order_id,
            "product_id": pid,
            "quantity": quantity,
            "unit_price": unit_price,
            "discount_pct": discount_pct,
            "final_price": final_price,
            "revenue": round(final_price * quantity, 2),
        })
        order_item_id += 1

orders = pd.DataFrame(orders_list)
order_items = pd.DataFrame(order_items_list)
orders.to_csv("data/orders.csv", index=False)
order_items.to_csv("data/order_items.csv", index=False)


inventory = pd.DataFrame({
    "product_id": products["product_id"],
    "store_id": np.random.randint(1, N_STORES + 1, N_PRODUCTS),
    "stock_on_hand": np.random.randint(0, 300, N_PRODUCTS),
    "reorder_level": np.random.randint(10, 50, N_PRODUCTS),
})
inventory.to_csv("data/inventory.csv", index=False)


returned_items = order_items.sample(frac=0.08, random_state=42)
returns = pd.DataFrame({
    "return_id": range(1, len(returned_items) + 1),
    "order_item_id": returned_items["order_item_id"].values,
    "reason": np.random.choice(
        ["Size Issue", "Damaged", "Not as Described", "Changed Mind", "Wrong Item"],
        len(returned_items)
    ),
    "return_date": [fake.date_between(start_date=START_DATE, end_date=END_DATE) for _ in range(len(returned_items))],
})
returns.to_csv("data/returns.csv", index=False)

print("✅ Done! Files created in the 'data' folder:")
print(" - customers.csv")
print(" - products.csv")
print(" - stores.csv")
print(" - orders.csv")
print(" - order_items.csv")
print(" - inventory.csv")
print(" - returns.csv")